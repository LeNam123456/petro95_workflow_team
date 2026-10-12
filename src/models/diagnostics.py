"""Econometric and Statistical Diagnostics for SPAFS V5.2.

Provides:
1. Multicollinearity diagnostics: Variance Inflation Factor (VIF) and Condition Number (Belsley et al. 1980).
2. Residual diagnostics:
   - Ljung-Box Q-test for serial correlation in forecast residuals.
   - ARCH-LM test (Engle 1982) for autoregressive conditional heteroskedasticity.
   - Jarque-Bera test for departure from residual Gaussian normality.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch

from src.data_proccessing.model_schemas import (
    MulticollinearityReport,
    diagnose_multicollinearity,
)

logger = logging.getLogger("SPAFS_V5.2")


def diagnose_residuals(
    residuals: pd.Series,
    lags: tuple[int, ...] = (1, 5, 10),
) -> dict[str, Any]:
    """Execute econometric diagnostics on model forecast residuals.

    Args:
        residuals (pd.Series): Time series of estimation or forecast residuals e_t = y_t - ŷ_t.
        lags (tuple[int, ...], optional): Lag orders for Ljung-Box and ARCH-LM tests.
            Defaults to (1, 5, 10).

    Returns:
        dict[str, Any]: Comprehensive diagnostic report containing:
            - Descriptive stats (mean, std, skewness, kurtosis)
            - Jarque-Bera normality test (stat, p_value, is_normal)
            - Ljung-Box serial correlation tests at requested lags
            - ARCH-LM test for volatility clustering
    """
    clean_res = residuals.dropna().to_numpy(dtype=float)
    n = len(clean_res)
    if n < 15:
        raise ValueError(f"Insufficient residual observations ({n} < 15) for econometric diagnostics.")

    # 1. Summary Moments
    mean_val = float(np.mean(clean_res))
    std_val = float(np.std(clean_res, ddof=1))
    skew_val = float(stats.skew(clean_res))
    kurt_val = float(stats.kurtosis(clean_res, fisher=True))  # Excess kurtosis

    # 2. Jarque-Bera Normality Test
    jb_stat, jb_p = stats.jarque_bera(clean_res)

    # 3. Ljung-Box Autocorrelation Test
    max_lag = max(lags)
    lb_df = acorr_ljungbox(clean_res, lags=list(lags), return_df=True)
    ljung_box_results = {}
    for lag in lags:
        if lag in lb_df.index:
            ljung_box_results[f"lag_{lag}"] = {
                "stat": float(lb_df.loc[lag, "lb_stat"]),
                "p_value": float(lb_df.loc[lag, "lb_pvalue"]),
                "serial_correlation_detected": bool(lb_df.loc[lag, "lb_pvalue"] < 0.05),
            }

    # 4. ARCH-LM Test for Heteroskedasticity (Engle 1982)
    arch_lag = min(5, n // 5)
    arch_test_res = {}
    try:
        lm_stat, lm_p, f_stat, f_p = het_arch(clean_res, nlags=arch_lag)
        arch_test_res = {
            "lm_stat": float(lm_stat),
            "lm_p_value": float(lm_p),
            "f_stat": float(f_stat),
            "f_p_value": float(f_p),
            "arch_effect_detected": bool(lm_p < 0.05),
        }
    except Exception as exc:
        logger.warning("ARCH-LM test could not be computed: %s", exc)
        arch_test_res = {"error": str(exc)}

    return {
        "n_obs": n,
        "moments": {
            "mean": mean_val,
            "std": std_val,
            "skewness": skew_val,
            "excess_kurtosis": kurt_val,
        },
        "jarque_bera": {
            "stat": float(jb_stat),
            "p_value": float(jb_p),
            "reject_normality_at_005": bool(jb_p < 0.05),
        },
        "ljung_box": ljung_box_results,
        "arch_lm": arch_test_res,
    }


__all__ = [
    "MulticollinearityReport",
    "diagnose_multicollinearity",
    "diagnose_residuals",
]