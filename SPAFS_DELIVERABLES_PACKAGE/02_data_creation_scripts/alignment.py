"""Gate 1.3 — Point-in-Time (PIT) Temporal Alignment & Canonical Panel Engine.

This module implements Step 1.3 of the SPAFS V5.2 data architecture. It performs
rigorous Temporal As-Of Integration between the validated Platts FOB Singapore Mogas
panel (MOC 16:30 SGT) and the continuous ICE Brent crude futures series (London settlement,
available ~03:30 SGT next morning).

Key Architecture and Quantitative Principles:

1. Temporal As-Of Integration:
   Adheres to Section 4.6 of the Blueprint ("Tuyệt đối không dùng pd.merge(..., on='Date')
   đơn thuần"). Automatically synchronizes cross-timezone market panels under the invariant:
       Record Date <= D_t  AND  availability_datetime <= 08:30 SGT on D_{t+1}
   When London is closed for UK bank holidays while Singapore is actively trading,
   it joins the latest known Brent settlement prior to the 08:30 SGT cutoff,
   preventing artificial data loss while maintaining zero lookahead bias.

2. Target Formulation Universe Boundary:
   Defines `target_market_date` as the next active trading day in the synchronized
   universe (D_{t+1}) and locks `forecast_origin_datetime` strictly at 08:30 SGT
   on D_{t+1} (t_origin).

3. Composite PIT Availability Timestamp:
   Synthesizes the composite availability horizon across all asset streams:
       availability_datetime = max(platts_availability, brent_availability)
   Resolving timezone-aware Asia/Singapore representations and tracking explicit
   proxy flags (`availability_datetime_is_proxy`).

4. PIT Hard Gate Verification:
   Strictly enforces:
       availability_datetime <= forecast_origin_datetime (100% Pass/Fail Gate)
   Any lookahead leakage triggers an immediate DataContractViolationError.

Artifacts Generated:
- data/interim/canonical_market_panel.parquet : Fully synchronized canonical market panel.
- reports/data_quality/canonical_panel_audit.csv : Machine-readable tabular audit record.
- reports/data_quality/canonical_panel_audit.json : Comprehensive JSON audit trail.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from ..aliases import ALIASES
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import make_sgt_timestamp, resolve_column, save_json
from ..io import write_csv, write_parquet

logger = logging.getLogger("SPAFS_V5.2")


def build_canonical_panel(
    platts: pd.DataFrame,
    brent: pd.DataFrame,
    cfg: Config,
    *,
    alignment_mode: str = "asof",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the Point-in-Time canonical market panel from validated Platts and Brent series.

    Integrates Platts Singapore assessments with ICE Brent futures according to
    the 5-timestamp temporal governance model. Bridges timezone differences
    between Singapore (UTC+8) and London/New York (UTC+0/-5) by locking the
    information cutoff at 08:30 SGT on the morning of target trading day D_{t+1}.
    Computes composite availability timestamps and verifies zero lookahead leakage.

    Args:
        platts (pd.DataFrame): Validated Platts trading-day DataFrame
            from Gate 1.1 (containing 'market_date', 'MG95', 'MG92', 'DO_005', etc.).
        brent (pd.DataFrame): Validated continuous Brent DataFrame
            from Gate 1.2 (containing 'market_date', 'brent_close', returns, etc.).
        cfg (Config): Pipeline configuration supplying forecast cutoff times,
            interim storage directories, and report destinations.
        alignment_mode (str, optional): Synchronization method. Defaults to 'asof'
            (Temporal As-Of Join). Can be set to 'exact' for strict calendar inner join.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: A two-element tuple containing:
            - **synchronized**: Canonical market panel DataFrame ready for analytical
              feature engineering, sorted chronologically with valid target dates.
            - **audit**: Machine-readable audit report containing alignment counts,
              calendar overlap metrics, and PIT verification results.

    Raises:
        DataContractViolationError: If required columns are missing, if the resulting
            canonical panel is empty, or if any record breaches the Point-in-Time
            hard gate (availability_datetime > forecast_origin_datetime).
    """
    logger.info("Building Point-in-Time Canonical Market Panel (mode=%s)...", alignment_mode)

    # ── Step 1: Resolve Brent column identifiers ──────────────────
    try:
        brent_price_col = resolve_column(brent, ALIASES, "brent_close")
    except KeyError:
        # Fallback check for alternative column naming
        if "brent_price" in brent.columns:
            brent_price_col = "brent_price"
        else:
            raise DataContractViolationError(
                f"Cannot locate Brent price series in brent DataFrame. "
                f"Available: {list(brent.columns)}"
            )

    candidate_brent_cols = [
        "market_date",
        brent_price_col,
        "brent_return_pct",
        "brent_return_pos",
        "brent_return_neg",
        "brent_outlier_flag",
        "brent_availability_datetime",
        "brent_availability_datetime_is_proxy",
        "brent_high",
        "brent_low",
        "brent_open",
        "brent_volume",
    ]
    brent_cols = [c for c in candidate_brent_cols if c in brent.columns]

    # Ensure clean sorting by market_date
    platts_sorted = platts.sort_values("market_date").reset_index(drop=True)
    brent_sorted = brent.sort_values("market_date").reset_index(drop=True)

    # ── Step 2: Temporal Integration (As-Of vs Exact) ────────────
    brent_sub = brent_sorted[brent_cols].copy()
    brent_sub["brent_observed_date"] = brent_sub["market_date"]

    if alignment_mode == "asof":
        panel = pd.merge_asof(
            platts_sorted,
            brent_sub,
            on="market_date",
            direction="backward",
        )
    elif alignment_mode == "exact":
        panel = platts_sorted.merge(
            brent_sub,
            on="market_date",
            how="inner",
        )
    else:
        raise ValueError(
            f"Unsupported alignment_mode '{alignment_mode}'. Choose 'asof' or 'exact'."
        )

    # Standardize Brent price column to canonical 'brent_close'
    if brent_price_col != "brent_close" and brent_price_col in panel.columns:
        panel = panel.rename(columns={brent_price_col: "brent_close"})

    # Track exact calendar overlap vs carry-forward on foreign market holidays
    panel["brent_calendar_exact_match"] = (
        panel["market_date"] == panel["brent_observed_date"]
    )

    # ── Step 3: Core price completeness check ────────────────────
    # Core series required for Mogas 95 refining spreads: MG95, MG92, DO_005, brent_close
    core_price_cols = ["MG95", "MG92", "DO_005", "brent_close"]
    missing_core_cols = [c for c in core_price_cols if c not in panel.columns]
    if missing_core_cols:
        raise DataContractViolationError(
            f"Missing essential pricing series for canonical panel: {missing_core_cols}"
        )

    eligible = panel[core_price_cols].notna().all(axis=1)
    synchronized = (
        panel.loc[eligible]
        .sort_values("market_date")
        .reset_index(drop=True)
        .copy()
    )

    if synchronized.empty:
        raise DataContractViolationError(
            "Canonical panel is empty after Platts-Brent temporal synchronization."
        )

    # ── Step 4: Target market date & Forecast cutoff definition ──
    # CRITICAL: Target is created only AFTER the final eligible trading universe is known.
    synchronized["target_market_date"] = synchronized["market_date"].shift(-1)

    synchronized["forecast_origin_datetime"] = make_sgt_timestamp(
        synchronized["target_market_date"],
        cfg.forecast_cutoff_time_sgt,
    )

    # ── Step 5: Composite Point-in-Time Availability Timestamp ────
    platts_availability = synchronized["availability_datetime"].copy()

    # Handle missing/proxy Platts availability gracefully with tz-aware observation time
    if platts_availability.isna().all():
        platts_availability = synchronized["observation_datetime"].copy()
    else:
        platts_availability = platts_availability.fillna(
            synchronized["observation_datetime"]
        )

    # Composite availability = latest availability among all ingested asset streams
    synchronized["availability_datetime"] = pd.concat(
        [
            platts_availability.rename("platts"),
            synchronized["brent_availability_datetime"].rename("brent"),
        ],
        axis=1,
    ).max(axis=1)

    synchronized["availability_datetime_is_proxy"] = (
        synchronized["availability_datetime_is_proxy"].fillna(True)
        | synchronized["brent_availability_datetime_is_proxy"]
        | platts["availability_datetime_is_proxy"].fillna(True)
    )

    # Drop the trailing row that has no forward target date in the sample
    synchronized = synchronized.dropna(
        subset=["target_market_date", "forecast_origin_datetime"]
    ).reset_index(drop=True)

    # ── Step 6: Point-in-Time Hard Gate Verification ──────────────
    pit_violation = (
        synchronized["availability_datetime"]
        > synchronized["forecast_origin_datetime"]
    )

    if pit_violation.any():
        num_violations = int(pit_violation.sum())
        raise DataContractViolationError(
            f"PIT HARD GATE BREACH: Detected {num_violations} observations where "
            f"availability_datetime > forecast_origin_datetime. Lookahead leakage prevented."
        )

    # ── Step 7: Build Audit Metrics & Persist Artifacts ──────────
    audit: dict[str, Any] = {
        "alignment_mode": alignment_mode,
        "platts_trading_rows": len(platts),
        "brent_trading_rows": len(brent),
        "canonical_panel_rows": len(synchronized),
        "exact_calendar_overlap_rows": int(
            synchronized["brent_calendar_exact_match"].sum()
        ),
        "holiday_carry_forward_rows": int(
            (~synchronized["brent_calendar_exact_match"]).sum()
        ),
        "date_range": (
            f"{synchronized['market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{synchronized['market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "target_date_range": (
            f"{synchronized['target_market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{synchronized['target_market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "pit_records_audited": len(synchronized),
        "pit_violations": int(pit_violation.sum()),
        "proxy_availability_rows": int(
            synchronized["availability_datetime_is_proxy"].sum()
        ),
        "status": "PASSED",
    }

    # Persist validated interim panel and quality audit files
    write_parquet(
        synchronized,
        cfg.interim_dir / "canonical_market_panel.parquet",
    )
    write_csv(
        pd.DataFrame([audit]),
        cfg.report_dir / "canonical_panel_audit.csv",
    )
    save_json(
        audit,
        cfg.report_dir / "canonical_panel_audit.json",
    )

    logger.info(
        "GATE 1.3 PASSED | Canonical Rows: %d | Exact Calendar Overlap: %d | PIT Violations: 0",
        len(synchronized),
        audit["exact_calendar_overlap_rows"],
    )

    return synchronized, audit
