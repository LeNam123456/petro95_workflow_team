"""Step 05 — Analytical Feature Engineering & Refining Economics Engine.

This module constructs the domain-specific feature space for the SPAFS V5.2
framework, translating refining economic theory and market dynamics into quantitative
predictors.

Key Architecture and Quantitative Principles:
1. Cross-Product Refining Spreads (Section 5.1 - 5.3):
   - Octane Spread: Spread_{95-92, t} = P_{MG95, t} - P_{MG92, t}
     Measures octane enhancement premiums and blending cost differentials.
   - Diesel Spread: Spread_{MG95-DO, t} = P_{MG95, t} - P_{DO_005, t}
     Captures refinery yield competition between light and middle distillates.
   - Gasoline-Brent Spread: Spread_{MG95-Brent, t} = P_{MG95, t} - P_{Brent, t}
     Proxy for regional refining crack margins at the Singapore hub.
2. Long-Run Equilibrium Anchor (Section 5.4):
   - Lagged Spread: Spread_{MG95-Brent, t-1}
     Acts as a mean-reverting equilibrium correction term, capturing economic forces
     restoring refining margins to sustainable bands.
3. Asymmetric Shock Decomposition (Section 5.5):
   - r_{Brent, t}^+ = max(r_{Brent, t}, 0.0)  (Positive shock branch)
   - r_{Brent, t}^- = min(r_{Brent, t}, 0.0)  (Negative shock branch)
     Directly serves the Asymmetric Distributed Lag (ADL) model for RQ1 Wald tests.
4. Trailing Volatility & Dynamic Three-Regime Target (Section 5.6):
   - Trailing Volatility: 30-day strictly backward-looking standard deviation.
   - Dynamic Threshold: theta_t = tri_regime_multiplier * VOL_30D_t
   - Three-Regime Direction:
       y_{t+1}^{tri} = +1 if r_{t+1} > theta_t
                       -1 if r_{t+1} < -theta_t
                        0 if |r_{t+1}| <= theta_t
5. Outlier and Shock Flags ("Outlier Detection != Outlier Removal"):
   Flags extreme price swings (|r| > outlier_abs_return_pct) across both assets
   to preserve fat-tail real-world shocks for robust modeling.

Artifacts Generated:
- Appends comprehensive feature matrix to the daily panel.
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


def _resolve_price_series(df: pd.DataFrame) -> dict[str, str]:
    """Helper to resolve physical pricing column names from DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame containing market prices.

    Returns:
        dict[str, str]: Mapping from logical names ('mg95', 'mg92', 'do005', 'brent')
            to actual column names in *df*.

    Raises:
        DataContractViolationError: If required price series cannot be resolved.
    """
    mapping: dict[str, str] = {}

    # MG95
    try:
        mapping["mg95"] = resolve_column(df, ALIASES, "MG95")
    except KeyError:
        if "mg95" in df.columns:
            mapping["mg95"] = "mg95"
        else:
            raise DataContractViolationError("Cannot resolve MG95 price column.")

    # MG92
    try:
        mapping["mg92"] = resolve_column(df, ALIASES, "MG92")
    except KeyError:
        if "mg92" in df.columns:
            mapping["mg92"] = "mg92"
        else:
            raise DataContractViolationError("Cannot resolve MG92 price column.")

    # DO_005 (0.05% Sulfur Gasoil)
    try:
        mapping["do005"] = resolve_column(df, ALIASES, "DO_005")
    except KeyError:
        if "do005" in df.columns:
            mapping["do005"] = "do005"
        elif "DO_005" in df.columns:
            mapping["do005"] = "DO_005"
        else:
            raise DataContractViolationError("Cannot resolve DO_005 price column.")

    # Brent Close
    try:
        mapping["brent"] = resolve_column(df, ALIASES, "brent_close")
    except KeyError:
        if "brent_price" in df.columns:
            mapping["brent"] = "brent_price"
        elif "brent_close" in df.columns:
            mapping["brent"] = "brent_close"
        else:
            raise DataContractViolationError("Cannot resolve Brent price column.")

    return mapping


def add_refining_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute refining spreads and equilibrium terms from physical prices.

    Calculates Octane spread (MG95 - MG92), Diesel spread (MG95 - DO_005),
    Gasoline-Brent crack spread (MG95 - Brent), and the lagged equilibrium
    anchor term (Spread_{MG95-Brent, t-1}).

    Args:
        df (pd.DataFrame): DataFrame containing validated physical prices.

    Returns:
        pd.DataFrame: DataFrame augmented with:
            - ``spread_mg95_mg92``: Octane premium (USD/bbl).
            - ``spread_mg95_do005``: Gasoline-to-diesel spread (USD/bbl).
            - ``spread_mg95_brent``: Singapore crack margin proxy (USD/bbl).
            - ``spread_mg95_brent_lag1``: Equilibrium mean-reverting anchor (t-1).
            - ``octane_spread_nonpositive_flag``: Audit flag for anomalous spread <= 0.
    """
    out = df.copy()
    col = _resolve_price_series(out)

    out["spread_mg95_mg92"] = out[col["mg95"]] - out[col["mg92"]]
    out["spread_mg95_do005"] = out[col["mg95"]] - out[col["do005"]]
    out["spread_mg95_brent"] = out[col["mg95"]] - out[col["brent"]]

    # Long-run equilibrium correction term (Lagged Crack Margin)
    out["spread_mg95_brent_lag1"] = out["spread_mg95_brent"].shift(1)

    # Economic validation: Octane spread should normally be positive
    out["octane_spread_nonpositive_flag"] = (
        out["spread_mg95_mg92"] < 0
    ).fillna(False)

    return out


def add_lag_features(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Construct autoregressive and cross-market lagged return features.

    Generates strictly past-lagged return predictors for Mogas 95 and Brent crude
    up to ``cfg.max_return_lag`` to ensure zero forward lookahead.

    Args:
        df (pd.DataFrame): DataFrame containing 'mg95_return_pct' and
            'brent_return_pct_aligned'.
        cfg (Config): Pipeline configuration supplying ``max_return_lag``.

    Returns:
        pd.DataFrame: DataFrame augmented with ``mg95_return_lag{1..k}``
            and ``brent_return_lag{1..k}``.
    """
    out = df.copy()

    for lag in range(1, cfg.max_return_lag + 1):
        out[f"mg95_return_lag{lag}"] = out["mg95_return_pct"].shift(lag)
        out[f"brent_return_lag{lag}"] = out["brent_return_pct_aligned"].shift(lag)

    return out


def add_volatility_and_regime(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Compute rolling volatility, asymmetric shocks, and dynamic three-regime target.

    Implements trailing volatility estimation over ``cfg.volatility_window`` days,
    decomposes asymmetric Brent shocks (r+, r-), derives the dynamic threshold
    theta_t, and classifies the three-regime target direction {+1, 0, -1}.

    Args:
        df (pd.DataFrame): DataFrame containing daily returns and target returns.
        cfg (Config): Pipeline configuration supplying volatility parameters
            and outlier detection thresholds.

    Returns:
        pd.DataFrame: DataFrame augmented with:
            - ``vol_mg95_30d``: Trailing 30-day return volatility.
            - ``theta_t``: Dynamic threshold (0.5 * vol_mg95_30d).
            - ``brent_return_pos``: Positive Brent return component (r+).
            - ``brent_return_neg``: Negative Brent return component (r-).
            - ``target_direction_tri``: Three-regime target in {+1, 0, -1}.
            - Outlier and economic shock indicator flags.
    """
    out = df.copy()

    # Trailing 30-day volatility (strictly backward-looking, min_periods enforced)
    out["vol_mg95_30d"] = (
        out["mg95_return_pct"]
        .rolling(
            window=cfg.volatility_window,
            min_periods=cfg.volatility_window,
        )
        .std(ddof=1)
    )

    # Dynamic regime threshold
    out["theta_t"] = cfg.tri_regime_multiplier * out["vol_mg95_30d"]

    # Asymmetric shock branches for RQ1 Asymmetric Distributed Lag (ADL)
    out["brent_return_pos"] = out["brent_return_pct_aligned"].clip(lower=0.0)
    out["brent_return_neg"] = out["brent_return_pct_aligned"].clip(upper=0.0)

    # Dynamic three-regime target formulation
    tri = pd.Series(pd.NA, index=out.index, dtype="Int64")
    valid = out["target_return_pct"].notna() & out["theta_t"].notna()

    tri.loc[
        valid & (out.loc[valid, "target_return_pct"] > out.loc[valid, "theta_t"])
    ] = 1

    tri.loc[
        valid & (out.loc[valid, "target_return_pct"] < -out.loc[valid, "theta_t"])
    ] = -1

    tri.loc[
        valid & (out.loc[valid, "target_return_pct"].abs() <= out.loc[valid, "theta_t"])
    ] = 0

    out["target_direction_tri"] = tri

    # Outlier detection and shock preservation audit flags
    out["mg95_outlier_flag"] = (
        out["mg95_return_pct"].abs() > cfg.outlier_abs_return_pct
    ).fillna(False)

    out["brent_outlier_flag_aligned"] = (
        out["brent_return_pct_aligned"].abs() > cfg.outlier_abs_return_pct
    ).fillna(False)

    out["target_outlier_flag"] = (
        out["target_return_pct"].abs() > cfg.outlier_abs_return_pct
    ).fillna(False)

    out["economic_shock_flag"] = (
        out["mg95_outlier_flag"] | out["brent_outlier_flag_aligned"]
    )

    return out


def build_market_features(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Execute complete Step 05 feature engineering workflow.

    Sequentially generates refining spreads, autoregressive lags, rolling volatility,
    asymmetric shocks, and dynamic regime targets.

    Args:
        df (pd.DataFrame): DataFrame containing synchronized prices and returns from Step 04.
        cfg (Config): Pipeline configuration supplying feature and audit parameters.

    Returns:
        pd.DataFrame: Comprehensive feature-engineered market panel ready for
            news enrichment and train/test partitioning.
    """
    out = add_refining_features(df)
    out = add_lag_features(out, cfg)
    out = add_volatility_and_regime(out, cfg)

    logger.info(
        "STEP 05 COMPLETE | total_columns=%d | rows=%d",
        len(out.columns),
        len(out),
    )
    return out
