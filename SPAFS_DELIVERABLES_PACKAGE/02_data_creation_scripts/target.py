"""Step 04 — Target Formulation & Return Computation Engine.

This module computes historical continuous log returns and formalizes the primary
and secondary target variables for the SPAFS V5.2 quantitative forecasting framework.

Key Architecture and Quantitative Principles:
1. Continuous Log Returns (t):
   Computes daily continuous returns from the information set available at day t:
       r_{MG95, t} = ln(P_{MG95, t} / P_{MG95, t-1}) * 100%
       r_{Brent, t} = ln(P_{Brent, t} / P_{Brent, t-1}) * 100%
2. Primary Target (t+1):
   Forecasts the next actual synchronized market day's return:
       r_{target, t+1} = ln(P_{MG95, t+1} / P_{MG95, t}) * 100%
   Transforms the non-stationary price series I(1) into a strictly stationary I(0)
   continuous return series, eliminating naive random-walk autocorrelation bias.
3. Secondary Target (Direction):
   Extracts binary direction indicators:
       y_{t+1} = 1 if r_{target, t+1} > 0 else 0
   with explicit NaN handling for out-of-horizon records.

Artifacts Generated:
- Appends target variables directly into the analytical DataFrame.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..aliases import ALIASES
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import resolve_column

logger = logging.getLogger("SPAFS_V5.2")


def add_returns_and_targets(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Compute daily historical log returns and formulate forward target variables.

    Calculates current-day log returns for Platts Mogas 95 and aligned Brent crude,
    and establishes the forward-looking target variables (r_{t+1} and y_{t+1})
    for the next synchronized trading session.

    Args:
        df (pd.DataFrame): Synchronized canonical market panel from Gate 1.3
            containing 'market_date', 'MG95', 'brent_close', and 'target_market_date'.
        cfg (Config): Pipeline configuration supplying audit thresholds and parameters.

    Returns:
        pd.DataFrame: DataFrame augmented with:
            - ``mg95_return_pct``: Today's continuous log return (t).
            - ``brent_return_pct_aligned``: Today's aligned Brent log return (t).
            - ``target_return_pct``: Primary target return for next trading session (t+1).
            - ``target_direction``: Secondary target binary direction in {0, 1}.

    Raises:
        DataContractViolationError: If required price series ('MG95' or 'brent_close')
            cannot be resolved from the input DataFrame.
    """
    out = df.sort_values("market_date").reset_index(drop=True).copy()

    # Resolve pricing columns flexibly across naming conventions
    try:
        mg95_col = resolve_column(out, ALIASES, "MG95")
    except KeyError:
        if "mg95" in out.columns:
            mg95_col = "mg95"
        else:
            raise DataContractViolationError(
                f"Cannot locate Mogas 95 price column in DataFrame. Available: {list(out.columns)}"
            )

    try:
        brent_col = resolve_column(out, ALIASES, "brent_close")
    except KeyError:
        if "brent_price" in out.columns:
            brent_col = "brent_price"
        else:
            raise DataContractViolationError(
                f"Cannot locate Brent price column in DataFrame. Available: {list(out.columns)}"
            )

    # ── Information available at cutoff t ─────────────────────────
    out["mg95_return_pct"] = (
        np.log(out[mg95_col] / out[mg95_col].shift(1)) * 100.0
    )

    out["brent_return_pct_aligned"] = (
        np.log(out[brent_col] / out[brent_col].shift(1)) * 100.0
    )

    # ── Primary Target: next synchronized trading session (t+1) ───
    out["target_return_pct"] = (
        np.log(out[mg95_col].shift(-1) / out[mg95_col]) * 100.0
    )

    # ── Secondary Target: Binary direction {0, 1} ─────────────────
    out["target_direction"] = pd.Series(
        np.where(
            out["target_return_pct"].notna(),
            (out["target_return_pct"] > 0).astype("int8"),
            np.nan,
        ),
        index=out.index,
        dtype="float64",
    )

    logger.info(
        "STEP 04 COMPLETE | rows=%d | valid target rows=%d",
        len(out),
        int(out["target_return_pct"].notna().sum()),
    )

    return out
