"""Low-level helper utilities for the SPAFS V5.2 data pipeline.

Provides reusable, stateless functions that are shared across
multiple pipeline stages:

* **sanitize_column_names** — strip BOM and normalise whitespace in
  DataFrame column headers without altering case.
* **resolve_column** — two-pass alias lookup (case-insensitive exact,
  then fuzzy alphanumeric) to map logical column names to their
  physical counterparts in heterogeneous CSV files.
* **parse_numeric / parse_naive_datetime / parse_timestamp_sgt** —
  type-coercion helpers with explicit error handling.
* **make_sgt_timestamp** — combine a date Series with an HH:MM string
  into timezone-aware Asia/Singapore timestamps.
* **save_json** — atomic JSON serialisation with ``ensure_ascii=False``.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger("SPAFS_V5.2")


# ── Column name sanitisation ────────────────────────────────────


def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip Unicode BOM and collapse whitespace in column headers.

    Does NOT lowercase column names because Platts canonical identifiers
    (MG95, DO_005, etc.) are case-sensitive by project convention.

    Args:
        df: Input DataFrame whose column headers may contain BOM
            characters (``\\ufeff``) or irregular whitespace.

    Returns:
        pd.DataFrame: A shallow copy of *df* with cleaned column names.
    """
    out = df.copy()
    out.columns = [
        re.sub(r"\s+", "_", str(c).strip().replace("\ufeff", ""))
        for c in out.columns
    ]
    return out


# ── Alias resolution ────────────────────────────────────────────


def resolve_column(
    df: pd.DataFrame,
    aliases: dict[str, list[str]],
    logical_name: str,
    *,
    required: bool = True,
) -> Optional[str]:
    """Map a logical column name to its physical counterpart via alias lookup.

    Performs a two-pass search over the DataFrame's columns:

    1. **Case-insensitive exact match** — strip + lower both sides.
    2. **Fuzzy match** — strip all non-alphanumeric characters, then lower.

    Args:
        df: DataFrame whose columns are searched.
        aliases: Registry mapping logical names to lists of known
            raw-file variants (e.g. ``ALIASES`` from ``aliases.py``).
        logical_name: The canonical name to resolve (must be a key
            in *aliases*).
        required: If ``True`` (default) and no column matches, raise
            ``KeyError``. If ``False``, return ``None`` silently.

    Returns:
        Optional[str]: The physical column name if found, otherwise
            ``None`` (only when ``required=False``).

    Raises:
        KeyError: If *logical_name* is not registered in *aliases*
            (always a caller bug), or if ``required=True`` and no
            physical column matches.
    """
    if logical_name not in aliases:
        raise KeyError(
            f"Unknown logical column '{logical_name}'. "
            f"Registered aliases: {list(aliases.keys())}"
        )

    candidates = aliases[logical_name]

    # Pass 1 — case-insensitive exact match
    col_index = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in col_index:
            return col_index[key]

    # Pass 2 — fuzzy (alphanumeric only)
    col_index_fuzzy = {
        re.sub(r"[^a-z0-9]+", "", str(c).lower()): c
        for c in df.columns
    }
    for candidate in candidates:
        key = re.sub(r"[^a-z0-9]+", "", candidate.lower())
        if key in col_index_fuzzy:
            return col_index_fuzzy[key]

    if required:
        raise KeyError(
            f"Required logical column '{logical_name}' not found. "
            f"Tried aliases={candidates}, available={list(df.columns)}"
        )
    return None


# ── Type-coercion helpers ───────────────────────────────────────


def parse_numeric(series: pd.Series) -> pd.Series:
    """Coerce a Series to float64, stripping commas and whitespace.

    Non-numeric values are silently coerced to ``NaN``. Downstream
    audit gates (structural-holiday vs. unexpected-missing) are
    responsible for catching unexpected NaN patterns.

    Args:
        series: Raw string or mixed-type Series from CSV ingestion.

    Returns:
        pd.Series: Float64 Series with invalid entries set to ``NaN``.
    """
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def parse_naive_datetime(series: pd.Series, name: str) -> pd.Series:
    """Parse a Series to timezone-naive datetime, raising on bad values.

    If the input carries timezone information, it is first converted to
    Asia/Singapore and then the timezone is stripped so that downstream
    code operates in a uniform naive-SGT space.

    Args:
        series: Raw date/datetime strings or mixed-type values.
        name: Human-readable column name for error messages.

    Returns:
        pd.Series: Timezone-naive datetime64[ns] Series.

    Raises:
        ValueError: If any non-null entry cannot be parsed to a valid
            datetime.
    """
    out = pd.to_datetime(series, errors="coerce")

    bad = out.isna() & series.notna()
    if bad.any():
        raise ValueError(
            f"Column '{name}' has {int(bad.sum())} unparseable datetime "
            f"values: {series[bad].unique().tolist()}"
        )

    if out.dt.tz is not None:
        out = out.dt.tz_convert("Asia/Singapore").dt.tz_localize(None)

    return out


def parse_timestamp_sgt(series: pd.Series, name: str) -> pd.Series:
    """Parse a Series to timezone-aware datetime in Asia/Singapore.

    Handles both tz-naive and tz-aware inputs:

    * **tz-naive** → localised directly as Asia/Singapore.
    * **tz-aware** → converted to Asia/Singapore.

    Args:
        series: Raw timestamp strings or mixed-type values.
        name: Human-readable column name for error messages.

    Returns:
        pd.Series: Timezone-aware datetime64[ns, Asia/Singapore] Series.

    Raises:
        ValueError: If any non-null entry cannot be parsed.
    """
    out = pd.to_datetime(series, errors="coerce")

    bad = out.isna() & series.notna()
    if bad.any():
        raise ValueError(
            f"Column '{name}' has {int(bad.sum())} unparseable timestamp "
            f"values: {series[bad].unique().tolist()}"
        )

    if out.dt.tz is None:
        return out.dt.tz_localize("Asia/Singapore")

    return out.dt.tz_convert("Asia/Singapore")


# ── Timestamp construction ──────────────────────────────────────


def make_sgt_timestamp(
    date_values: pd.Series,
    hhmm: str,
) -> pd.Series:
    """Combine a date Series with an HH:MM string into SGT timestamps.

    Args:
        date_values: Series of date-like values (strings, Timestamps,
            or datetime64).
        hhmm: Time-of-day in ``"HH:MM"`` format (e.g. ``"16:30"``).

    Returns:
        pd.Series: Timezone-aware datetime64[ns, Asia/Singapore] Series
            where each entry is ``date + hhmm`` localised to SGT.

    Raises:
        ValueError: If *hhmm* is not in valid ``HH:MM`` format.
    """
    parts = hhmm.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise ValueError(f"Expected HH:MM format, got '{hhmm}'")

    hour, minute = int(parts[0]), int(parts[1])
    base = pd.to_datetime(date_values).dt.normalize()

    return (
        base + pd.Timedelta(hours=hour, minutes=minute)
    ).dt.tz_localize("Asia/Singapore")


# ── JSON persistence ────────────────────────────────────────────


def save_json(payload: dict, path: Path | str) -> None:
    """Write a dictionary to a pretty-printed JSON file.

    Parent directories are created automatically if they do not exist.

    Args:
        payload: The data to serialise. Non-serialisable values are
            converted via ``str()``.
        path: Destination file path (str or Path).

    Returns:
        None
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )