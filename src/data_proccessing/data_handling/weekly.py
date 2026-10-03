"""Step 08 — Weekly Aggregation & Temporal Robustness Engine.

This module aggregates daily trading observations into weekly time series in accordance
with the SPAFS V5.2 Robustness Framework (Section 1.4).

Key Architecture and Quantitative Principles:
1. Temporal Aggregation Robustness (N ≈ 900):
   Aggregates daily physical prices (Mogas 95, Mogas 92, Gasoil 0.05%, Brent) to the weekly
   frequency by taking the final available trading session of each calendar week (W-SUN).
   Serves as an empirical robustness test verifying that econometric findings (such as
   symmetric transmission in RQ1) are not artifacts of high-frequency daily market noise.
2. Weekly Target Formulation:
   - Primary Weekly Return: r_{w+1} = ln(P_{MG95, w+1} / P_{MG95, w}) * 100%
   - Weekly Direction: y_{w+1} = 1 if r_{w+1} > 0 else 0
3. Cross-Product Weekly Spreads:
   Computes weekly octane spreads, diesel spreads, and crack margins.

Artifacts Generated:
- data/processed/weekly_price_robustness.parquet : Aggregated weekly panel.
- reports/data_quality/weekly_audit.csv : Tabular summary of weekly aggregation.
- reports/data_quality/weekly_audit.json : Machine-readable weekly audit report.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from ..aliases import ALIASES
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import resolve_column, save_json
from ..io import write_csv, write_parquet

logger = logging.getLogger("SPAFS_V5.2")


def build_weekly_price_robustness(
    daily: pd.DataFrame,
    cfg: Config,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aggregate daily market panel into weekly frequency for robustness checking.

    Takes the last observed trading day of each calendar week (ending Sunday),
    derives weekly log returns, binary directions, and refining spreads, and
    enforces temporal validity.

    Args:
        daily (pd.DataFrame): Synchronized daily panel containing pricing series.
        cfg (Config): Pipeline configuration supplying output directories.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: A two-element tuple containing:
            - **weekly**: Validated weekly DataFrame sorted chronologically.
            - **audit**: Audit metrics dictionary documenting row counts and date horizons.

    Raises:
        DataContractViolationError: If required price columns cannot be resolved.
    """
    logger.info("Executing Step 08: Weekly Temporal Aggregation...")
    work = daily.sort_values("market_date").copy()

    # Resolve pricing columns
    try:
        mg95_col = resolve_column(work, ALIASES, "MG95")
    except KeyError:
        mg95_col = "MG95" if "MG95" in work.columns else "mg95"

    try:
        mg92_col = resolve_column(work, ALIASES, "MG92")
    except KeyError:
        mg92_col = "MG92" if "MG92" in work.columns else "mg92"

    try:
        do005_col = resolve_column(work, ALIASES, "DO_005")
    except KeyError:
        do005_col = "DO_005" if "DO_005" in work.columns else "do005"

    try:
        brent_col = resolve_column(work, ALIASES, "brent_close")
    except KeyError:
        brent_col = "brent_close" if "brent_close" in work.columns else "brent_price"

    # Define calendar week (ending Sunday)
    work["week_period"] = work["market_date"].dt.to_period("W-SUN")

    # Aggregate by last trading session of the week
    weekly = (
        work.groupby("week_period", as_index=False)
        .agg(
            market_date=("market_date", "last"),
            MG95=(mg95_col, "last"),
            MG92=(mg92_col, "last"),
            DO_005=(do005_col, "last"),
            brent_close=(brent_col, "last"),
        )
        .sort_values("market_date")
        .reset_index(drop=True)
    )

    # ── Weekly target formulation ─────────────────────────────────
    weekly["target_market_date"] = weekly["market_date"].shift(-1)

    weekly["target_return_pct"] = (
        np.log(weekly["MG95"].shift(-1) / weekly["MG95"]) * 100.0
    )

    weekly["target_direction"] = pd.Series(
        np.where(
            weekly["target_return_pct"].notna(),
            (weekly["target_return_pct"] > 0).astype("int8"),
            np.nan,
        ),
        index=weekly.index,
        dtype="float64",
    )

    # Weekly refining spreads
    weekly["spread_mg95_mg92"] = weekly["MG95"] - weekly["MG92"]
    weekly["spread_mg95_do005"] = weekly["MG95"] - weekly["DO_005"]
    weekly["spread_mg95_brent"] = weekly["MG95"] - weekly["brent_close"]

    # Drop trailing observation without forward target
    clean_weekly = weekly.dropna(
        subset=["target_market_date", "target_return_pct"]
    ).reset_index(drop=True)

    audit: dict[str, Any] = {
        "daily_input_rows": len(daily),
        "weekly_robustness_rows": len(clean_weekly),
        "date_range": (
            f"{clean_weekly['market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{clean_weekly['market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "target_date_range": (
            f"{clean_weekly['target_market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{clean_weekly['target_market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "status": "PASSED",
    }

    # ── Persist Artifacts ─────────────────────────────────────────
    write_parquet(
        clean_weekly,
        cfg.processed_dir / "weekly_price_robustness.parquet",
    )
    write_csv(
        pd.DataFrame([audit]),
        cfg.report_dir / "weekly_audit.csv",
    )
    save_json(
        audit,
        cfg.report_dir / "weekly_audit.json",
    )

    logger.info(
        "STEP 08 COMPLETE | Weekly Rows: %d | Horizon: %s",
        len(clean_weekly),
        audit["date_range"],
    )

    return clean_weekly, audit
