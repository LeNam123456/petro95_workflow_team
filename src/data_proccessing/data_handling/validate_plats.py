"""Gate 1.1 — Platts FOB Singapore Data Contract Validation.

Implements the first mandatory quality gate of the SPAFS V5.2 pipeline.
The validation enforces four sequential hard-gate rules on the raw
Platts CSV before any downstream processing is allowed:

    Gate 1  Primary-key uniqueness and chronological ordering.
    Gate 2  Date range within [min_date, max_date].
    Gate 3  Structural-holiday vs. partial-missing classification
            (no forward-fill is ever permitted).
    Gate 4  Strictly positive prices on all trading days.

After passing all gates the function attaches Point-in-Time (PIT)
timestamps (observation, publication, availability), removes structural
holidays, and persists:

* ``platts_validated.parquet``  — clean trading-day panel.
* ``platts_audit.csv / .json`` — machine-readable audit report.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from ..aliases import ALIASES, PLATTS_PRICE_COLUMNS
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import (
    make_sgt_timestamp,
    parse_naive_datetime,
    parse_numeric,
    parse_timestamp_sgt,
    resolve_column,
    sanitize_column_names,
    save_json,
)
from ..io import read_csv, write_csv, write_parquet

logger = logging.getLogger("SPAFS_V5.2")


# ── Internal helpers (single-responsibility gate functions) ─────


def _ingest_and_rename(cfg: Config) -> pd.DataFrame:
    """Read the raw Platts CSV, sanitise headers, and rename columns
    to their canonical logical names via alias resolution.

    Args:
        cfg: Pipeline configuration with ``platts_csv`` path.

    Returns:
        pd.DataFrame: Raw data with canonical column names. Column
            types are still strings at this stage.

    Raises:
        KeyError: If any required column (market_date, MG95, MG92,
            DO_001, DO_005) cannot be resolved from the alias registry.
    """
    # Row 1 in the raw CSV is a unit-description row ("Đơn vị tính, USD/bbl, …")
    # that must be skipped to avoid polluting the data with non-numeric strings.
    raw = sanitize_column_names(read_csv(cfg.platts_csv, skiprows=[1]))

    rename_map: dict[str, str] = {
        resolve_column(raw, ALIASES, "market_date"): "market_date",
    }
    for logical in PLATTS_PRICE_COLUMNS:
        rename_map[resolve_column(raw, ALIASES, logical)] = logical

    # Optional timestamp columns
    pub_col = resolve_column(
        raw, ALIASES, "publication_datetime", required=False
    )
    if pub_col:
        rename_map[pub_col] = "publication_datetime"

    avail_col = resolve_column(
        raw, ALIASES, "availability_datetime", required=False
    )
    if avail_col:
        rename_map[avail_col] = "availability_datetime"

    return raw.rename(columns=rename_map)


def _check_primary_key(df: pd.DataFrame, cfg: Config) -> None:
    """Gate 1 — Verify primary-key uniqueness and chronological order.

    Args:
        df: DataFrame with a parsed ``market_date`` column.
        cfg: Pipeline configuration (controls whether uniqueness
            is enforced via ``require_unique_market_date``).

    Returns:
        None

    Raises:
        DataContractViolationError: If duplicate dates are found
            (when enforced) or if dates are not monotonically
            increasing.
    """
    dupes = df["market_date"].duplicated(keep=False)
    if cfg.require_unique_market_date and dupes.any():
        raise DataContractViolationError(
            f"Duplicate market_date: {int(dupes.sum())} rows"
        )
    if not df["market_date"].is_monotonic_increasing:
        raise DataContractViolationError(
            "market_date is not monotonically increasing."
        )


def _check_date_range(df: pd.DataFrame, cfg: Config) -> None:
    """Gate 2 — Verify all dates fall within the research window.

    Args:
        df: DataFrame with a parsed ``market_date`` column.
        cfg: Pipeline configuration supplying ``min_date``
            and ``max_date``.

    Returns:
        None

    Raises:
        DataContractViolationError: If any row has a date outside
            ``[min_date, max_date]``.
    """
    out_of_range = ~df["market_date"].between(
        pd.Timestamp(cfg.min_date), pd.Timestamp(cfg.max_date)
    )
    if out_of_range.any():
        raise DataContractViolationError(
            f"{int(out_of_range.sum())} rows outside "
            f"[{cfg.min_date}, {cfg.max_date}]"
        )


def _check_missing_pattern(
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    """Gate 3 — Classify rows as structural holidays or partial missing.

    Three missing-data patterns are recognised:

    1. **Structural holiday** — ALL price columns are NaN (entire
       market closed). Retained in audit, removed from trading panel.
    2. **Leading product-launch absence** — a single series (e.g.
       ``DO_001``) is NaN in a contiguous block from the first row
       because the product was not yet traded. Tolerated silently.
    3. **Genuine partial missing** — some but not all columns are NaN
       in a non-leading pattern. This is a hard contract violation.

    Args:
        df: DataFrame with parsed numeric price columns.

    Returns:
        tuple[pd.Series, pd.Series]: A pair of boolean masks
            ``(structural_holiday, unexpected_missing)``.

    Raises:
        DataContractViolationError: If any genuine partial-missing
            rows are detected (pattern 3).
    """
    all_na = df[PLATTS_PRICE_COLUMNS].isna().all(axis=1)
    any_na = df[PLATTS_PRICE_COLUMNS].isna().any(axis=1)
    partial = any_na & ~all_na

    if partial.any():
        # Identify leading NaN blocks (product not yet launched).
        # A column's leading-NaN block is the contiguous run of NaN
        # from index 0 before the first non-NaN value.
        tolerated = pd.Series(False, index=df.index)
        for col in PLATTS_PRICE_COLUMNS:
            first_valid = df[col].first_valid_index()
            if first_valid is not None and first_valid > 0:
                leading_mask = pd.Series(False, index=df.index)
                leading_mask.iloc[:first_valid] = True
                tolerated = tolerated | (df[col].isna() & leading_mask)

        # A row is tolerated if every NaN in that row is explained
        # by a leading product-launch block.
        unexplained = partial.copy()
        for idx in df.index[partial]:
            na_cols = [
                c for c in PLATTS_PRICE_COLUMNS if pd.isna(df.at[idx, c])
            ]
            all_explained = all(
                idx < (df[c].first_valid_index() or 0) for c in na_cols
            )
            if all_explained:
                unexplained.at[idx] = False

        if unexplained.any():
            raise DataContractViolationError(
                f"Partial missing in {int(unexplained.sum())} rows. "
                "No forward-fill allowed."
            )

    return all_na, partial


def _check_positive_prices(df: pd.DataFrame, cfg: Config) -> pd.Series:
    """Gate 4 — Verify all non-null prices are strictly positive.

    Args:
        df: DataFrame with parsed numeric price columns.
        cfg: Pipeline configuration (controls enforcement via
            ``require_positive_prices``).

    Returns:
        pd.Series: Boolean mask where ``True`` indicates a row with
            at least one non-positive price.

    Raises:
        DataContractViolationError: If non-positive prices are found
            (when enforced).
    """
    nonpos = (
        df[PLATTS_PRICE_COLUMNS].notna()
        & (df[PLATTS_PRICE_COLUMNS] <= 0)
    ).any(axis=1)
    if cfg.require_positive_prices and nonpos.any():
        raise DataContractViolationError(
            f"Non-positive prices in {int(nonpos.sum())} rows."
        )
    return nonpos


def _stamp_pit_timestamps(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Attach Point-in-Time governance timestamps to the DataFrame.

    Creates or parses three timestamp columns:

    * ``observation_datetime`` — Platts MOC close (always synthesised).
    * ``publication_datetime`` — parsed if present, else ``NaT`` + proxy flag.
    * ``availability_datetime`` — parsed if present, else ``NaT`` + proxy flag.

    Args:
        df: DataFrame with a parsed ``market_date`` column and
            optionally raw ``publication_datetime`` /
            ``availability_datetime`` columns.
        cfg: Pipeline configuration supplying ``platts_moc_time_sgt``.

    Returns:
        pd.DataFrame: A copy of *df* with the three timestamp columns
            and their ``_is_proxy`` boolean companions attached.
    """
    df = df.copy()

    # Observation = Platts MOC close
    df["observation_datetime"] = make_sgt_timestamp(
        df["market_date"], cfg.platts_moc_time_sgt
    )

    # Publication
    if "publication_datetime" in df.columns:
        df["publication_datetime"] = parse_timestamp_sgt(
            df["publication_datetime"], "Platts publication_datetime"
        )
        df["publication_datetime_is_proxy"] = False
    else:
        df["publication_datetime"] = pd.NaT
        df["publication_datetime_is_proxy"] = True

    # Availability
    if "availability_datetime" in df.columns:
        df["availability_datetime"] = parse_timestamp_sgt(
            df["availability_datetime"], "Platts availability_datetime"
        )
        df["availability_datetime_is_proxy"] = False
    else:
        df["availability_datetime"] = pd.NaT
        df["availability_datetime_is_proxy"] = True

    return df


# ── Public entry point ──────────────────────────────────────────


def validate_platts(cfg: Config) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute Gate 1.1 — full Platts Data Contract validation.

    Orchestrates ingestion, type parsing, four sequential hard gates,
    PIT timestamp attachment, and artifact persistence. This is the
    single entry point that downstream pipeline stages call.

    Args:
        cfg: Pipeline configuration containing file paths, research
            windows, and audit enforcement flags.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: A two-element tuple:

            * **clean** — Trading-day-only DataFrame (structural
              holidays removed), sorted by ``market_date``, with
              PIT timestamps attached.
            * **audit** — Summary dict written to
              ``platts_audit.json`` / ``.csv``.

    Raises:
        DataContractViolationError: If any gate (PK, range, missing
            pattern, positive prices) fails.
        KeyError: If required columns cannot be resolved from the
            alias registry.
    """
    df = _ingest_and_rename(cfg)

    # ── Type parsing ────────────────────────────────────────────
    df["market_date"] = parse_naive_datetime(
        df["market_date"], "market_date"
    ).dt.normalize()
    for col in PLATTS_PRICE_COLUMNS:
        df[col] = parse_numeric(df[col])

    # ── Exact-duplicate removal ───────────────────────────────────
    # Exact-duplicate rows (same date AND same prices) are a known
    # raw-data artefact; drop them before the PK uniqueness gate.
    # Rows with the same date but *different* prices are NOT dropped
    # and will correctly trigger Gate 1.
    n_before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    n_deduped = n_before - len(df)
    if n_deduped > 0:
        logger.info(
            "Dropped %d exact-duplicate rows from raw Platts data.",
            n_deduped,
        )

    # ── Contract gates ──────────────────────────────────────────
    _check_primary_key(df, cfg)
    _check_date_range(df, cfg)
    holidays, unexpected = _check_missing_pattern(df)
    nonpos = _check_positive_prices(df, cfg)

    # ── Optional row-count sanity check ─────────────────────────
    if cfg.expected_raw_platts_rows is not None:
        if len(df) != cfg.expected_raw_platts_rows:
            logger.warning(
                "Expected %d raw rows, got %d",
                cfg.expected_raw_platts_rows, len(df),
            )

    # ── PIT timestamps ──────────────────────────────────────────
    df = _stamp_pit_timestamps(df, cfg)

    # ── Remove structural holidays ──────────────────────────────
    clean = (
        df.loc[~holidays]
        .sort_values("market_date")
        .reset_index(drop=True)
    )

    if cfg.expected_trading_rows is not None:
        if len(clean) != cfg.expected_trading_rows:
            logger.warning(
                "Expected %d trading rows, got %d",
                cfg.expected_trading_rows, len(clean),
            )

    # ── Audit report ────────────────────────────────────────────
    audit: dict[str, Any] = {
        "raw_rows": n_before,
        "exact_duplicate_rows_removed": n_deduped,
        "structural_holiday_rows": int(holidays.sum()),
        "unexpected_missing_rows": int(unexpected.sum()),
        "nonpositive_price_rows": int(nonpos.sum()),
        "trading_rows": len(clean),
        "date_range": (
            f"{clean['market_date'].min()} -> "
            f"{clean['market_date'].max()}"
        ),
        "required_series": PLATTS_PRICE_COLUMNS,
        "publication_timestamp_is_proxy": bool(
            clean["publication_datetime_is_proxy"].all()
        ),
        "availability_timestamp_is_proxy": bool(
            clean["availability_datetime_is_proxy"].all()
        ),
        "status": "PASSED",
    }

    # ── Persist artifacts ───────────────────────────────────────
    write_parquet(clean, cfg.interim_dir / "platts_validated.parquet")
    write_csv(pd.DataFrame([audit]), cfg.report_dir / "platts_audit.csv")
    save_json(audit, cfg.report_dir / "platts_audit.json")

    logger.info(
        "GATE 1.1 PASSED | raw=%d | holidays=%d | trading=%d",
        len(df), audit["structural_holiday_rows"], len(clean),
    )
    return clean, audit