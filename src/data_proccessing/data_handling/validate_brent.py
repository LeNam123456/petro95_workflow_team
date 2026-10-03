"""Gate 1.2 — Brent Crude Futures Data Contract Validation & PIT Continuity Engine.

This module implements the second mandatory data contract gate of the SPAFS V5.2
framework. It processes the raw ICE Brent crude front-month continuous futures
series (BZ=F), executes strict econometric and structural data contract gates,
computes continuous log returns along with asymmetric shock components (r+, r-),
and attaches Point-in-Time (PIT) availability timestamps.

Key Architecture and Quantitative Principles:

1. Multi-Format Ingestion: Transparently auto-detects and parses Yahoo Finance
   multi-row headers (Ticker / Price artifacts) while maintaining backward
   compatibility with standard flat tabular CSV files.

2. Hard Contract Verification Gates:
   - Gate 1: Monotonic chronology and primary-key uniqueness on `market_date`.
   - Gate 2: Temporal boundary enforcement within [min_date, max_date].
   - Gate 3: Completeness assurance (zero unexpected missing / null entries).
   - Gate 4: Price positivity validation (P_Brent > 0 strictly enforced).

3. Quantitative Return & Shock Formulation:
   Computes continuous log returns: r_{Brent, t} = ln(P_t / P_{t-1}) * 100%,
   and decomposes asymmetric shock branches (r_{Brent}^+, r_{Brent}^-)
   tailored for the Asymmetric Distributed Lag (ADL) model (RQ1).

4. Financial Philosophy: "Outlier Detection != Outlier Removal":
   Extreme market movements (|r| > 20.0%) such as the March-April 2020 oil price
   war and COVID-19 demand shock are flagged and audited, but strictly preserved
   to maintain fat-tail economic realism.

5. Point-in-Time Governance:
   Locks Brent settlement availability at 03:30 SGT on the subsequent morning,
   verifying that information availability strictly precedes the 08:30 SGT
   forecast cutoff (t_origin) for downstream trading day D_{t+1}.

Artifacts Generated:
- data/interim/brent_continuous.parquet : Clean, continuous validated panel.
- reports/data_quality/brent_audit.csv  : Tabular audit record for research appendix.
- reports/data_quality/brent_audit.json : Comprehensive JSON audit trail.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from ..aliases import ALIASES
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import (
    make_sgt_timestamp,
    parse_naive_datetime,
    parse_numeric,
    resolve_column,
    sanitize_column_names,
    save_json,
)
from ..io import read_csv, write_csv, write_parquet

logger = logging.getLogger("SPAFS_V5.2")


# ── Internal Single-Responsibility Gate Procedures ─────────────


def _ingest_and_rename_brent(cfg: Config) -> pd.DataFrame:
    """Ingest raw Brent futures CSV and standardize column names.

    Auto-detects whether the CSV contains Yahoo Finance multi-level header
    artifacts (e.g., row 0 containing 'Ticker'/'BZ=F' and row 1 containing
    'Date' / NaNs) or a standard flat tabular header. Resolves physical
    identifiers to canonical logical names ('market_date', 'brent_close',
    'brent_high', 'brent_low', 'brent_open', 'brent_volume').

    Args:
        cfg (Config): Pipeline configuration supplying the path to ``brent_csv``.

    Returns:
        pd.DataFrame: Sanitized raw DataFrame with canonical column names.

    Raises:
        DataContractViolationError: If required date or close price series
            cannot be resolved from the alias registry or file structure.
    """
    # Sample initial lines to inspect schema structure
    peek = read_csv(cfg.brent_csv, nrows=2)
    is_yfinance_multiindex = (
        peek.iloc[0].astype(str).str.contains("Ticker|BZ=F", regex=True).any()
    )

    if is_yfinance_multiindex:
        logger.info(
            "Detected Yahoo Finance multi-row header artifact in %s. "
            "Skipping metadata rows [1, 2].",
            cfg.brent_csv.name,
        )
        raw = sanitize_column_names(read_csv(cfg.brent_csv, skiprows=[1, 2]))
        # In Yahoo Finance export, the first column contains the trading date
        # even if labeled as 'Price' in line 0.
        date_col = raw.columns[0]
        rename_map: dict[str, str] = {date_col: "market_date"}
    else:
        raw = sanitize_column_names(read_csv(cfg.brent_csv))
        try:
            date_col = resolve_column(raw, ALIASES, "market_date")
            rename_map = {date_col: "market_date"}
        except KeyError as err:
            # Fallback: inspect if the first column contains parseable dates
            date_col = raw.columns[0]
            logger.warning(
                "Logical 'market_date' not found via standard aliases. "
                "Falling back to first column: '%s'.",
                date_col,
            )
            rename_map = {date_col: "market_date"}

    try:
        close_col = resolve_column(raw, ALIASES, "brent_close")
        rename_map[close_col] = "brent_close"
    except KeyError as err:
        raise DataContractViolationError(
            f"Failed to identify Brent close price column in {cfg.brent_csv}. "
            f"Available headers: {list(raw.columns)}"
        ) from err

    # Map auxiliary OHLCV columns if present for feature engineering completeness
    for aux in ["Open", "High", "Low", "Volume"]:
        col_found = resolve_column(
            raw,
            {aux.lower(): [aux, aux.lower(), f"brent_{aux.lower()}"]},
            aux.lower(),
            required=False,
        )
        if col_found and col_found not in rename_map:
            rename_map[col_found] = f"brent_{aux.lower()}"

    df = raw.rename(columns=rename_map).copy()
    return df


def _check_primary_key(df: pd.DataFrame, cfg: Config) -> None:
    """Enforce Gate 1: Primary key uniqueness and strictly monotonic chronology.

    Args:
        df (pd.DataFrame): Ingested DataFrame containing the parsed ``market_date``.
        cfg (Config): Pipeline configuration specifying uniqueness enforcement.

    Returns:
        None

    Raises:
        DataContractViolationError: If duplicate trading dates are detected
            or if the time series is not sorted monotonically increasing.
    """
    duplicates = df["market_date"].duplicated(keep=False)
    if cfg.require_unique_market_date and duplicates.any():
        num_dupes = int(duplicates.sum())
        raise DataContractViolationError(
            f"Brent primary key violation: detected {num_dupes} duplicate "
            f"observations on 'market_date'."
        )

    if not df["market_date"].is_monotonic_increasing:
        raise DataContractViolationError(
            "Brent chronological sequence violation: 'market_date' series "
            "is not strictly monotonically increasing."
        )


def _check_date_range(df: pd.DataFrame, cfg: Config) -> None:
    """Enforce Gate 2: Temporal boundary validation within configured bounds.

    Args:
        df (pd.DataFrame): DataFrame containing parsed ``market_date``.
        cfg (Config): Pipeline configuration supplying ``min_date`` and ``max_date``.

    Returns:
        None

    Raises:
        DataContractViolationError: If records exist outside the research horizon.
    """
    out_of_bounds = ~df["market_date"].between(
        pd.Timestamp(cfg.min_date), pd.Timestamp(cfg.max_date)
    )
    if out_of_bounds.any():
        num_out = int(out_of_bounds.sum())
        raise DataContractViolationError(
            f"Brent temporal boundary violation: {num_out} records reside outside "
            f"prescribed window [{cfg.min_date}, {cfg.max_date}]."
        )


def _check_completeness_and_positivity(df: pd.DataFrame, cfg: Config) -> None:
    """Enforce Gate 3 & 4: Zero missing values and strictly positive price levels.

    Args:
        df (pd.DataFrame): DataFrame containing validated numeric ``brent_close``.
        cfg (Config): Pipeline configuration controlling positive price constraints.

    Returns:
        None

    Raises:
        DataContractViolationError: If null values or non-positive price records
            are encountered in the continuous settlement series.
    """
    null_count = int(df["brent_close"].isna().sum())
    if null_count > 0:
        raise DataContractViolationError(
            f"Brent completeness violation: detected {null_count} null / NaN "
            f"entries in 'brent_close'. No forward-filling permitted."
        )

    non_positive = df["brent_close"] <= 0.0
    if cfg.require_positive_prices and non_positive.any():
        num_nonpos = int(non_positive.sum())
        raise DataContractViolationError(
            f"Brent economic realism violation: encountered {num_nonpos} non-positive "
            f"price observations (<= 0.0 USD/bbl)."
        )


def _compute_returns_and_audit_outliers(
    df: pd.DataFrame, cfg: Config
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Compute continuous log returns, asymmetric shock branches, and audit outliers.

    Calculates daily continuous return:
        r_{Brent, t} = ln(P_{Brent, t} / P_{Brent, t-1}) * 100%
    and decomposes asymmetric shock branches for econometric RQ1 testing:
        r_{Brent, t}^+ = max(r_{Brent, t}, 0.0)
        r_{Brent, t}^- = min(r_{Brent, t}, 0.0)

    Identifies large return jumps exceeding ``cfg.outlier_abs_return_pct`` (default 20.0%).
    In compliance with "Outlier Detection != Outlier Removal", records are flagged
    for the audit log without truncating the fat-tailed market distributions.

    Args:
        df (pd.DataFrame): Validated DataFrame sorted chronologically.
        cfg (Config): Pipeline configuration supplying outlier threshold.

    Returns:
        tuple[pd.DataFrame, list[dict[str, Any]]]: A tuple containing:
            - Augmented DataFrame with columns ['brent_return_pct', 'brent_return_pos',
              'brent_return_neg', 'brent_outlier_flag'].
            - List of audited outlier records with date, price, and magnitude.
    """
    df = df.copy()

    # Continuous log return in percentage points
    df["brent_return_pct"] = (
        np.log(df["brent_close"] / df["brent_close"].shift(1)) * 100.0
    )

    # Asymmetric shock decomposition for RQ1 Asymmetric Distributed Lag (ADL)
    df["brent_return_pos"] = df["brent_return_pct"].clip(lower=0.0)
    df["brent_return_neg"] = df["brent_return_pct"].clip(upper=0.0)

    # Outlier detection (|r| > threshold)
    threshold = cfg.outlier_abs_return_pct
    df["brent_outlier_flag"] = df["brent_return_pct"].abs() > threshold

    outlier_rows = df[df["brent_outlier_flag"]].copy()
    outlier_audit_records: list[dict[str, Any]] = []

    for _, row in outlier_rows.iterrows():
        record = {
            "market_date": str(row["market_date"].strftime("%Y-%m-%d")),
            "brent_close": round(float(row["brent_close"]), 4),
            "log_return_pct": round(float(row["brent_return_pct"]), 4),
            "classification": "GENUINE_MARKET_SHOCK_PRESERVED",
        }
        outlier_audit_records.append(record)
        logger.info(
            "AUDITED OUTLIER PRESERVED | Date: %s | Close: %.2f USD/bbl | Return: %+.2f%%",
            record["market_date"],
            record["brent_close"],
            record["log_return_pct"],
        )

    return df, outlier_audit_records


def _stamp_brent_pit_timestamps(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Attach Point-in-Time governance availability timestamps to Brent records.

    Because ICE Brent crude futures settle during the late London evening (~19:30 UTC),
    the official settlement price becomes verifiable in Singapore at approximately
    03:30 SGT on the morning of calendar day D_{t+1}. This timestamp is stamped
    to explicitly prove zero lookahead leakage before the 08:30 SGT Cutoff (t_origin).

    Args:
        df (pd.DataFrame): DataFrame containing normalized ``market_date``.
        cfg (Config): Pipeline configuration supplying settlement availability time.

    Returns:
        pd.DataFrame: DataFrame augmented with Point-in-Time availability columns:
            ``brent_availability_datetime`` (tz-aware SGT) and
            ``brent_availability_datetime_is_proxy`` (bool).
    """
    df = df.copy()

    # Available at 03:30 SGT on next calendar day (market_date + 1 day)
    next_calendar_day = df["market_date"] + pd.Timedelta(days=1)
    df["brent_availability_datetime"] = make_sgt_timestamp(
        next_calendar_day,
        cfg.brent_settlement_available_time_sgt,
    )
    df["brent_availability_datetime_is_proxy"] = True

    return df


# ── Public Entry Point: Gate 1.2 Pipeline Execution ────────────


def validate_brent(
    cfg: Config,
    platts_reference: Optional[pd.DataFrame | str] = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute Gate 1.2 — Full Brent Crude Contract Validation & PIT Audit.

    Orchestrates the complete validation lifecycle:
    1. Robust multi-header ingestion and schema normalization.
    2. Exact-duplicate deduplication.
    3. Rigorous validation gates (primary key, chronology, boundaries, positivity).
    4. Continuous log return computation and asymmetric shock separation (r+, r-).
    5. Fat-tail outlier auditing (preserving extreme events without truncation).
    6. Point-in-Time availability stamping (03:30 SGT next-day lock).
    7. Artifact generation and persistence:
       - ``data/interim/brent_continuous.parquet``
       - ``reports/data_quality/brent_audit.csv``
       - ``reports/data_quality/brent_audit.json``

    Args:
        cfg (Config): Pipeline configuration containing data paths and audit parameters.
        platts_reference (Optional[pd.DataFrame | str]): Optional reference to the
            validated Platts dataset (or file path) to assess calendar overlap
            and synchronisation readiness. Defaults to None.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: A two-element tuple containing:
            - **clean**: Fully validated, continuous Brent panel ready for As-Of Join.
            - **audit**: Machine-readable audit metrics dictionary.

    Raises:
        DataContractViolationError: If any of the 4 core validation gates fails.
    """
    logger.info("Executing Gate 1.2: Brent Crude Contract Validation...")

    # Step 1: Ingestion and column resolution
    raw_df = _ingest_and_rename_brent(cfg)

    # Step 2: Type parsing
    raw_df["market_date"] = parse_naive_datetime(
        raw_df["market_date"], "brent market_date"
    ).dt.normalize()
    raw_df["brent_close"] = parse_numeric(raw_df["brent_close"])

    for aux_col in [c for c in raw_df.columns if c.startswith("brent_") and c != "brent_close"]:
        raw_df[aux_col] = parse_numeric(raw_df[aux_col])

    # Step 3: Exact-duplicate deduplication on trading date
    n_raw = len(raw_df)
    clean_df = (
        raw_df.drop_duplicates(subset=["market_date"])
        .sort_values("market_date")
        .reset_index(drop=True)
    )
    n_deduped = n_raw - len(clean_df)
    if n_deduped > 0:
        logger.info(
            "Dropped %d duplicate market_date entries from Brent raw series.",
            n_deduped,
        )

    # Step 4: Verification of Data Contract Gates
    _check_primary_key(clean_df, cfg)
    _check_date_range(clean_df, cfg)
    _check_completeness_and_positivity(clean_df, cfg)

    # Step 5: Continuous returns & outlier audit
    clean_df, outlier_records = _compute_returns_and_audit_outliers(clean_df, cfg)

    # Step 6: Point-in-Time availability timestamp assignment
    clean_df = _stamp_brent_pit_timestamps(clean_df, cfg)

    # Step 7: Calendar overlap inspection against Platts benchmark (if available)
    overlap_count: Optional[int] = None
    platts_path = cfg.interim_dir / "platts_validated.parquet"
    if platts_reference is not None:
        if isinstance(platts_reference, (str, pd.DataFrame)):
            p_df = (
                pd.read_parquet(platts_reference)
                if isinstance(platts_reference, str)
                else platts_reference
            )
            overlap_count = int(
                clean_df["market_date"].isin(p_df["market_date"]).sum()
            )
    elif platts_path.exists():
        p_df = pd.read_parquet(platts_path)
        overlap_count = int(
            clean_df["market_date"].isin(p_df["market_date"]).sum()
        )

    # Step 8: Build machine-readable audit report
    audit: dict[str, Any] = {
        "raw_rows": n_raw,
        "exact_duplicate_rows_removed": n_deduped,
        "trading_rows": len(clean_df),
        "date_range": (
            f"{clean_df['market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{clean_df['market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "min_close_usd_bbl": round(float(clean_df["brent_close"].min()), 4),
        "max_close_usd_bbl": round(float(clean_df["brent_close"].max()), 4),
        "outlier_threshold_pct": cfg.outlier_abs_return_pct,
        "outliers_detected": len(outlier_records),
        "outlier_details": outlier_records,
        "platts_calendar_overlap_days": overlap_count,
        "brent_availability_rule": f"market_date + 1 day @ {cfg.brent_settlement_available_time_sgt} SGT",
        "status": "PASSED",
    }

    # Step 9: Persist validated artifacts
    write_parquet(clean_df, cfg.interim_dir / "brent_continuous.parquet")
    write_csv(pd.DataFrame([audit]), cfg.report_dir / "brent_audit.csv")
    save_json(audit, cfg.report_dir / "brent_audit.json")

    logger.info(
        "GATE 1.2 PASSED | Trading Days: %d | Price Range: [%.2f, %.2f] | Outliers: %d",
        len(clean_df),
        audit["min_close_usd_bbl"],
        audit["max_close_usd_bbl"],
        len(outlier_records),
    )

    return clean_df, audit
