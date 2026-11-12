"""Evaluation metrics for time-series forecasting.

Computes:
- Point metrics: MAE, MSE, RMSE, MAPE, R^2 (evaluated in USD/barrel)
- Directional metric: 3-state Directional Accuracy (DA)
- Class distributions: Up%, Down%, Flat%
- Majority class baseline
"""

from __future__ import annotations

from typing import Any
import numpy as np


def three_state_sign(values: np.ndarray) -> np.ndarray:
    """Compute 3-state sign (+1 for > 0, -1 for < 0, 0 for == 0).

    Uses a small tolerance for floating point zeros.
    """
    arr = np.asarray(values, dtype=np.float64)
    signs = np.zeros_like(arr, dtype=np.int64)
    tol = 1e-9
    signs[arr > tol] = 1
    signs[arr < -tol] = -1
    return signs


def compute_directional_accuracy(
    actual_prices: np.ndarray,
    predicted_prices: np.ndarray,
    origin_prices: np.ndarray,
) -> dict[str, float]:
    """Compute 3-state Directional Accuracy and direction distributions."""
    act = np.asarray(actual_prices, dtype=np.float64)
    pred = np.asarray(predicted_prices, dtype=np.float64)
    orig = np.asarray(origin_prices, dtype=np.float64)

    delta_act = act - orig
    delta_pred = pred - orig

    sgn_act = three_state_sign(delta_act)
    sgn_pred = three_state_sign(delta_pred)

    n_samples = len(act)
    if n_samples == 0:
        return {
            "directional_accuracy": 0.0,
            "majority_class_baseline": 0.0,
            "up_pct": 0.0,
            "down_pct": 0.0,
            "flat_pct": 0.0,
        }

    correct_mask = (sgn_act == sgn_pred)
    da = float(np.mean(correct_mask) * 100.0)

    up_count = int(np.sum(sgn_act == 1))
    down_count = int(np.sum(sgn_act == -1))
    flat_count = int(np.sum(sgn_act == 0))

    up_pct = float(up_count / n_samples * 100.0)
    down_pct = float(down_count / n_samples * 100.0)
    flat_pct = float(flat_count / n_samples * 100.0)
    majority_class_baseline = float(max(up_pct, down_pct, flat_pct))

    return {
        "directional_accuracy": da,
        "majority_class_baseline": majority_class_baseline,
        "up_pct": up_pct,
        "down_pct": down_pct,
        "flat_pct": flat_pct,
    }


def compute_metrics(
    actual_prices: np.ndarray,
    predicted_prices: np.ndarray,
    origin_prices: np.ndarray,
) -> dict[str, Any]:
    """Compute all 6 standard forecasting metrics + directional stats in USD/barrel."""
    act = np.asarray(actual_prices, dtype=np.float64)
    pred = np.asarray(predicted_prices, dtype=np.float64)
    orig = np.asarray(origin_prices, dtype=np.float64)

    n_samples = len(act)
    if n_samples == 0:
        raise ValueError("Cannot compute metrics on empty arrays.")

    errors = pred - act
    abs_errors = np.abs(errors)
    sq_errors = errors ** 2

    mae = float(np.mean(abs_errors))
    mse = float(np.mean(sq_errors))
    rmse = float(np.sqrt(mse))

    # MAPE: avoid divide by zero if any actual is zero
    non_zero_act = np.where(act != 0, act, np.nan)
    mape = float(np.nanmean(np.abs(errors / non_zero_act)) * 100.0)

    # R^2
    ss_res = float(np.sum(sq_errors))
    ss_tot = float(np.sum((act - np.mean(act)) ** 2))
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    da_stats = compute_directional_accuracy(act, pred, orig)

    return {
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "mape": mape,
        "r2": r2,
        "directional_accuracy": da_stats["directional_accuracy"],
        "majority_class_baseline": da_stats["majority_class_baseline"],
        "up_pct": da_stats["up_pct"],
        "down_pct": da_stats["down_pct"],
        "flat_pct": da_stats["flat_pct"],
        "n_samples": n_samples,
    }
