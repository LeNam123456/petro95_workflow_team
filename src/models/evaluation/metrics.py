"""Evaluation Metrics and Statistical Tests for SPAFS V5.2.

Provides:
1. Pointwise regression loss metrics (RMSE, MAE, R², OOS-R²).
2. Directional metrics (Directional Accuracy, Confusion Matrix, MCC).
3. Pesaran & Timmermann (1992) Non-parametric Directional Accuracy Test.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import matthews_corrcoef

logger = logging.getLogger("SPAFS_V5.2")


def compute_regression_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    y_benchmark: Optional[pd.Series | np.ndarray] = None,
) -> dict[str, float]:
    """Compute standard regression accuracy and Out-of-Sample R² metrics.

    Args:
        y_true: Ground truth target returns.
        y_pred: Model predicted returns.
        y_benchmark (optional): Benchmark predictions (e.g. M0a zero returns) for OOS-R².

    Returns:
        dict[str, float]: Dictionary containing:
            - 'rmse': Root Mean Squared Error
            - 'mae': Mean Absolute Error
            - 'mse': Mean Squared Error
            - 'r2': Standard in-sample R²
            - 'oos_r2': Campbell-Thompson (2008) OOS R² relative to benchmark (if provided)
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    valid_mask = ~np.isnan(yt) & ~np.isnan(yp)
    yt = yt[valid_mask]
    yp = yp[valid_mask]

    n = len(yt)
    if n == 0:
        return {"rmse": np.nan, "mae": np.nan, "mse": np.nan, "r2": np.nan}

    errors = yt - yp
    mse = float(np.mean(errors ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(errors)))

    # Standard In-sample R² relative to historical mean
    tss = float(np.sum((yt - np.mean(yt)) ** 2))
    rss = float(np.sum(errors ** 2))
    r2 = float(1.0 - (rss / tss)) if tss > 1e-12 else 0.0

    metrics = {
        "rmse": rmse,
        "mae": mae,
        "mse": mse,
        "r2": r2,
    }

    # OOS-R² relative to benchmark predictions (Campbell & Thompson 2008)
    if y_benchmark is not None:
        yb = np.asarray(y_benchmark, dtype=float)[valid_mask]
        bench_errors = yt - yb
        mse_bench = float(np.mean(bench_errors ** 2))
        oos_r2 = float(1.0 - (mse / mse_bench)) if mse_bench > 1e-12 else 0.0
        metrics["oos_r2"] = oos_r2

    return metrics


def compute_directional_metrics(
    y_true_dir: pd.Series | np.ndarray,
    y_pred_dir: pd.Series | np.ndarray,
) -> dict[str, Any]:
    """Compute directional classification metrics and Pesaran-Timmermann test.

    Args:
        y_true_dir: Actual direction in {0, 1}.
        y_pred_dir: Predicted direction in {0, 1}.

    Returns:
        dict[str, Any]: Directional metrics dictionary containing:
            - 'directional_accuracy': Ratio of correct directional calls in [0, 1]
            - 'mcc': Matthews Correlation Coefficient in [-1, 1]
            - 'pt_stat': Pesaran-Timmermann test statistic (~ N(0, 1))
            - 'pt_p_value': Two-sided p-value for directional market timing ability
    """
    yt = np.asarray(y_true_dir, dtype=int)
    yp = np.asarray(y_pred_dir, dtype=int)

    n = len(yt)
    if n == 0:
        return {
            "directional_accuracy": np.nan,
            "mcc": np.nan,
            "pt_stat": np.nan,
            "pt_p_value": np.nan,
        }

    correct = yt == yp
    acc = float(np.mean(correct))
    mcc = float(matthews_corrcoef(yt, yp)) if len(np.unique(yt)) > 1 and len(np.unique(yp)) > 1 else 0.0

    # Pesaran & Timmermann (1992) Non-parametric Directional Test
    p_hat = acc
    p_y = float(np.mean(yt))
    p_x = float(np.mean(yp))

    p_star = p_y * p_x + (1.0 - p_y) * (1.0 - p_x)

    var_p_hat = (p_star * (1.0 - p_star)) / n
    var_p_y = (p_y * (1.0 - p_y)) / n
    var_p_x = (p_x * (1.0 - p_x)) / n

    v_hat = (
        var_p_hat
        + ((2.0 * p_y - 1.0) ** 2) * var_p_x
        + ((2.0 * p_x - 1.0) ** 2) * var_p_y
    )

    if v_hat > 1e-12:
        pt_stat = float((p_hat - p_star) / np.sqrt(v_hat))
        pt_pvalue = float(2.0 * (1.0 - stats.norm.cdf(abs(pt_stat))))
    else:
        pt_stat = 0.0
        pt_pvalue = 1.0

    return {
        "directional_accuracy": acc,
        "mcc": mcc,
        "pt_stat": pt_stat,
        "pt_p_value": pt_pvalue,
        "reject_no_market_timing_at_005": bool(pt_pvalue < 0.05),
    }


__all__ = ["compute_regression_metrics", "compute_directional_metrics"]
