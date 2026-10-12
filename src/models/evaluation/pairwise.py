"""Pairwise Model Comparison Tests for SPAFS V5.2.

Provides:
1. Diebold & Mariano (1995) test with Harvey, Leybourne & Newbold (HLN 1997) small-sample correction
   for non-nested models (e.g. M1 vs M2, LightGBM vs linear).
2. Clark & West (2007) adjusted test for nested models (e.g. M0a vs M1, M2 vs M3).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger("SPAFS_V5.2")


@dataclass(frozen=True)
class PairwiseTestResult:
    """Immutable result container for pairwise forecast comparison tests."""

    test_name: str
    candidate_id: str
    benchmark_id: str
    sample_size: int
    loss_differential_mean: float
    test_statistic: float
    p_value: float
    alternative: str
    reject_h0_at_005: bool


def diebold_mariano_test(
    e_candidate: pd.Series | np.ndarray,
    e_benchmark: pd.Series | np.ndarray,
    loss: Literal["squared", "absolute"] = "squared",
    h: int = 1,
    small_sample_correction: bool = True,
    candidate_id: str = "Candidate",
    benchmark_id: str = "Benchmark",
) -> PairwiseTestResult:
    """Execute Diebold-Mariano (1995) test with Harvey-Leybourne-Newbold (HLN 1997) correction.

    Tests null hypothesis:
        H0: E[d_t] = 0 (Candidate and Benchmark have equal forecast accuracy).
        H1: E[d_t] < 0 (Candidate has smaller forecast loss than Benchmark).

    Args:
        e_candidate: Out-of-sample forecast errors from candidate model: e_cand = y - ŷ_cand.
        e_benchmark: Out-of-sample forecast errors from benchmark model: e_bench = y - ŷ_bench.
        loss: Loss function ('squared' for MSE or 'absolute' for MAE). Defaults to 'squared'.
        h: Forecast horizon (steps ahead). Defaults to 1.
        small_sample_correction: Apply HLN (1997) degrees of freedom adjustment. Defaults to True.
        candidate_id: Name of candidate model.
        benchmark_id: Name of benchmark model.

    Returns:
        PairwiseTestResult: DM test statistic, p-value, and decision.
    """
    ec = np.asarray(e_candidate, dtype=float)
    eb = np.asarray(e_benchmark, dtype=float)

    valid = ~np.isnan(ec) & ~np.isnan(eb)
    ec = ec[valid]
    eb = eb[valid]
    T = len(ec)

    if T < 10:
        raise ValueError(f"Insufficient paired observations ({T} < 10) for Diebold-Mariano test.")

    # 1. Loss Differential d_t = Loss(ec) - Loss(eb)
    if loss == "squared":
        d = ec ** 2 - eb ** 2
    elif loss == "absolute":
        d = np.abs(ec) - np.abs(eb)
    else:
        raise ValueError(f"Unknown loss metric '{loss}'")

    d_mean = float(np.mean(d))

    # 2. Long-run autocovariance via Bartlett kernel (Newey-West)
    gamma_0 = float(np.var(d, ddof=0))
    gamma_sum = 0.0
    max_lag = max(1, h - 1)
    for k in range(1, max_lag + 1):
        weight = 1.0 - (k / (max_lag + 1.0))
        gamma_k = float(np.sum((d[k:] - d_mean) * (d[:-k] - d_mean)) / T)
        gamma_sum += 2.0 * weight * gamma_k

    long_run_var = max(1e-12, (gamma_0 + gamma_sum) / T)
    dm_stat = float(d_mean / np.sqrt(long_run_var))

    # 3. Small-Sample HLN (1997) Correction Factor
    if small_sample_correction:
        hln_factor = np.sqrt((T + 1.0 - 2.0 * h + (h * (h - 1.0)) / T) / T)
        hln_stat = float(dm_stat * hln_factor)
        # One-sided p-value from Student's t distribution with T-1 degrees of freedom
        # H1: Candidate loss < Benchmark loss => d_mean < 0 => hln_stat < 0
        p_val = float(stats.t.cdf(hln_stat, df=T - 1))
        test_stat = hln_stat
    else:
        p_val = float(stats.norm.cdf(dm_stat))
        test_stat = dm_stat

    return PairwiseTestResult(
        test_name="Diebold-Mariano (HLN 1997)",
        candidate_id=candidate_id,
        benchmark_id=benchmark_id,
        sample_size=T,
        loss_differential_mean=d_mean,
        test_statistic=test_stat,
        p_value=p_val,
        alternative="Candidate loss < Benchmark loss (one-sided)",
        reject_h0_at_005=bool(p_val < 0.05),
    )


def clark_west_test(
    y_true: pd.Series | np.ndarray,
    y_pred_small: pd.Series | np.ndarray,
    y_pred_large: pd.Series | np.ndarray,
    candidate_id: str = "LargeModel",
    benchmark_id: str = "SmallModel",
) -> PairwiseTestResult:
    """Execute Clark & West (2007) test for nested forecasting models.

    Under the null hypothesis that the additional parameters in the large model
    are zero, the large model introduces extra parameter estimation noise that inflates
    its sample MSPE. Clark-West corrects for this noise bias:
        f_t = (y_t - ŷ_small,t)² - [ (y_t - ŷ_large,t)² - (ŷ_small,t - ŷ_large,t)² ]

    Args:
        y_true: Actual continuous returns.
        y_pred_small: Predictions from nested restricted benchmark model.
        y_pred_large: Predictions from larger candidate model.
        candidate_id: Identifier of large model.
        benchmark_id: Identifier of small model.

    Returns:
        PairwiseTestResult: CW test statistic, p-value, and decision.
    """
    yt = np.asarray(y_true, dtype=float)
    y1 = np.asarray(y_pred_small, dtype=float)
    y2 = np.asarray(y_pred_large, dtype=float)

    valid = ~np.isnan(yt) & ~np.isnan(y1) & ~np.isnan(y2)
    yt, y1, y2 = yt[valid], y1[valid], y2[valid]
    T = len(yt)

    if T < 10:
        raise ValueError(f"Insufficient paired observations ({T} < 10) for Clark-West test.")

    e1 = yt - y1  # Small model error
    e2 = yt - y2  # Large model error

    # Adjusted loss differential
    f = (e1 ** 2) - ((e2 ** 2) - ((y1 - y2) ** 2))
    f_mean = float(np.mean(f))

    # Regress f on constant with Newey-West HAC standard error
    X = np.ones((T, 1))
    ols = sm.OLS(f, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    cw_stat = float(ols.tvalues[0])
    p_val = float(1.0 - stats.norm.cdf(cw_stat))  # One-sided test (H1: CW stat > 0)

    return PairwiseTestResult(
        test_name="Clark-West (2007)",
        candidate_id=candidate_id,
        benchmark_id=benchmark_id,
        sample_size=T,
        loss_differential_mean=f_mean,
        test_statistic=cw_stat,
        p_value=p_val,
        alternative="Large model MSPE < Small model MSPE (one-sided)",
        reject_h0_at_005=bool(p_val < 0.05),
    )


__all__ = ["PairwiseTestResult", "diebold_mariano_test", "clark_west_test"]
