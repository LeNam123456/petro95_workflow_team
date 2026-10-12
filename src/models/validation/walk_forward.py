"""Expanding Window Walk-Forward 1-Step-Ahead Forecasting Engine for SPAFS V5.2.

Implements the Branch B Out-of-Sample evaluation protocol:
- Sequential expanding window: At each forecast origin τ, models are estimated solely
  on historical information set 1:τ.
- Zero lookahead: Exactly 1 step ahead is forecasted (τ+1).
- Generates pure out-of-sample prediction time series for Campbell-Thompson OOS-R²
  and Diebold-Mariano testing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import pandas as pd

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


@dataclass(frozen=True)
class WalkForwardResult:
    """Container holding walk-forward out-of-sample predictions and metadata."""

    model_id: str
    initial_train_size: int
    num_oos_forecasts: int
    refit_frequency: int
    predictions_df: pd.DataFrame


def run_walk_forward_evaluation(
    model_factory: Callable[[], BaseForecastingModel],
    X: pd.DataFrame,
    y: pd.Series,
    initial_train_size: int = 2500,
    refit_every: int = 1,
) -> WalkForwardResult:
    """Execute expanding window walk-forward out-of-sample forecasting.

    Args:
        model_factory: Callable that instantiates a fresh BaseForecastingModel instance.
        X (pd.DataFrame): Whitelisted feature matrix with DatetimeIndex.
        y (pd.Series): Target return series with matching DatetimeIndex.
        initial_train_size (int, optional): Number of initial trading days in training warm-up.
            Defaults to 2500.
        refit_every (int, optional): Frequency of parameter re-estimation.
            1 = daily full refit (most rigorous); 20 = monthly refit. Defaults to 1.

    Returns:
        WalkForwardResult: Out-of-sample predictions DataFrame and audit details.
    """
    T = len(y)
    if initial_train_size >= T:
        raise ValueError(f"initial_train_size ({initial_train_size}) must be strictly less than sample size ({T}).")

    sample_model = model_factory()
    model_id = sample_model.model_id

    dates = y.index
    pred_returns = []
    pred_directions = []
    actual_returns = []
    actual_directions = []
    oos_dates = []

    current_model = model_factory()
    fitted_step = -1

    logger.info(
        "Starting Walk-Forward for %s: Total T=%d, Warmup=%d, OOS Horizon=%d, Refit Frequency=%d",
        model_id,
        T,
        initial_train_size,
        T - initial_train_size,
        refit_every,
    )

    for tau in range(initial_train_size, T):
        # Determine if refitting is required
        if fitted_step < 0 or (tau - initial_train_size) % refit_every == 0:
            X_train = X.iloc[:tau]
            y_train = y.iloc[:tau]
            current_model = model_factory()
            current_model.fit(X_train, y_train)
            fitted_step = tau

        # 1-step ahead out-of-sample forecast origin
        X_test = X.iloc[tau : tau + 1]
        y_test_actual = float(y.iloc[tau])

        p_ret = float(current_model.predict(X_test).iloc[0])
        p_dir = int(current_model.predict_direction(X_test).iloc[0])
        a_dir = int(y_test_actual > 0.0)

        oos_dates.append(dates[tau])
        pred_returns.append(p_ret)
        pred_directions.append(p_dir)
        actual_returns.append(y_test_actual)
        actual_directions.append(a_dir)

    dt_idx = pd.DatetimeIndex(oos_dates)
    results_df = pd.DataFrame(
        {
            "market_date": dt_idx,
            "actual_return": actual_returns,
            "predicted_return": pred_returns,
            "residual": np.array(actual_returns) - np.array(pred_returns),
            "actual_direction": actual_directions,
            "predicted_direction": pred_directions,
            "direction_correct": (np.array(actual_directions) == np.array(pred_directions)).astype(bool),
        },
        index=dt_idx,
    )

    return WalkForwardResult(
        model_id=model_id,
        initial_train_size=initial_train_size,
        num_oos_forecasts=len(results_df),
        refit_frequency=refit_every,
        predictions_df=results_df,
    )


__all__ = ["WalkForwardResult", "run_walk_forward_evaluation"]
