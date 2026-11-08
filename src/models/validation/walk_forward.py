"""Expanding-window walk-forward engine for SPAFS V5.2 (single engine for all horizons).

Interface:

    run_walk_forward_evaluation(model_factory, X, y, *, initial_train_size,
                                refit_every=1, horizon=1, embargo=0) -> WalkForwardResult
    run_walk_forward_quantiles(model_factory, X, y, *, initial_train_size,
                               refit_every=1, horizon=1, embargo=0) -> pd.DataFrame

Both share one loop, so purging/embargo/refit rules are identical for point and
quantile forecasters. A quantile forecaster exposes ``fit(X, y)`` and
``predict_quantiles(X) -> DataFrame`` (columns = probability levels).

Invariants enforced inside (callers cannot opt out):

* ``y`` is the *return* target r_{t,h} observed at row t and realised h rows later.
  Rows must be consecutive trading sessions, sorted in time.
* Purging + embargo: at forecast origin tau the model is fit only on rows
  t <= tau - horizon - embargo, so every training label is realised by tau - embargo.
  A violated invariant raises immediately (no silent clamping).
* ``model.predict`` receives every feature row after the training window up to and
  including tau (features are known at tau; only labels are purged). Stateless models
  ignore the extra rows; stateful ones (ARMA) need them to update their filter.
* Direction is the sign of the forecast return: up = (r_hat > 0).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


@dataclass(frozen=True)
class WalkForwardResult:
    """Walk-forward out-of-sample predictions and protocol metadata."""

    model_id: str
    initial_train_size: int
    num_oos_forecasts: int
    refit_frequency: int
    horizon: int
    embargo: int
    predictions_df: pd.DataFrame


def purged_train_end(tau: int, horizon: int, embargo: int) -> int:
    """Last row position (inclusive) usable for training at origin ``tau``."""
    return tau - horizon - embargo


def _check_inputs(X, y, initial_train_size, refit_every, horizon, embargo, min_train_size) -> None:
    T = len(y)
    if len(X) != T or not X.index.equals(y.index):
        raise ValueError("X and y must share the same index.")
    if initial_train_size >= T:
        raise ValueError(f"initial_train_size ({initial_train_size}) must be < sample size ({T}).")
    if horizon < 1 or embargo < 0 or refit_every < 1:
        raise ValueError("horizon >= 1, embargo >= 0 and refit_every >= 1 are required.")
    first_end = purged_train_end(initial_train_size, horizon, embargo)
    if first_end + 1 < min_train_size:
        raise ValueError(
            f"Only {first_end + 1} purged training rows at the first origin (< {min_train_size}). "
            "Increase initial_train_size."
        )
    if y.isna().any():
        raise ValueError("y contains NaN; drop unrealised targets before walk-forward.")


def _walk_forward(model_factory, X, y, initial_train_size, refit_every, horizon, embargo, predict):
    """Shared loop: yields predict(model, X_rows_after_training_up_to_tau) for every origin tau."""
    model = None
    train_end = -1
    for i, tau in enumerate(range(initial_train_size, len(y))):
        if model is None or i % refit_every == 0:
            train_end = purged_train_end(tau, horizon, embargo)
            # Leakage guard: every training label realised no later than tau - embargo.
            assert train_end + horizon <= tau - embargo
            model = model_factory()
            model.fit(X.iloc[: train_end + 1], y.iloc[: train_end + 1])
        yield predict(model, X.iloc[train_end + 1 : tau + 1])


def run_walk_forward_evaluation(
    model_factory: Callable[[], BaseForecastingModel],
    X: pd.DataFrame,
    y: pd.Series,
    initial_train_size: int = 2500,
    refit_every: int = 1,
    horizon: int = 1,
    embargo: int = 0,
    min_train_size: int = 50,
) -> WalkForwardResult:
    """Run expanding-window walk-forward OOS point forecasting.

    Args:
        model_factory: Returns a fresh, unfitted model.
        X: Feature matrix (rows aligned with ``y``).
        y: Return target r_{t,h}.
        initial_train_size: First forecast origin (row position).
        refit_every: Re-estimate every this many origins (1 = every step).
        horizon: Forecast horizon h in rows (label at t is realised at t + h).
        embargo: Extra rows dropped between the training window and the origin.
        min_train_size: Minimum number of training rows; violating it raises.
    """
    _check_inputs(X, y, initial_train_size, refit_every, horizon, embargo, min_train_size)
    T = len(y)
    model_id = model_factory().model_id
    logger.info(
        "Walk-forward %s: T=%d, warmup=%d, OOS=%d, refit=%d, h=%d, embargo=%d",
        model_id, T, initial_train_size, T - initial_train_size, refit_every, horizon, embargo,
    )
    preds = np.fromiter(
        _walk_forward(model_factory, X, y, initial_train_size, refit_every, horizon, embargo,
                      lambda m, rows: float(m.predict(rows).iloc[-1])),
        dtype=float,
        count=T - initial_train_size,
    )

    oos_index = y.index[initial_train_size:]
    actual = y.iloc[initial_train_size:].to_numpy(dtype=float)
    act_dir = (actual > 0.0).astype(int)
    pred_dir = (preds > 0.0).astype(int)
    results_df = pd.DataFrame(
        {
            "actual_return": actual,
            "predicted_return": preds,
            "residual": actual - preds,
            "actual_direction": act_dir,
            "predicted_direction": pred_dir,
            "direction_correct": act_dir == pred_dir,
        },
        index=oos_index,
    )
    if isinstance(oos_index, pd.DatetimeIndex):
        results_df.insert(0, "market_date", oos_index)

    return WalkForwardResult(
        model_id=model_id,
        initial_train_size=initial_train_size,
        num_oos_forecasts=len(results_df),
        refit_frequency=refit_every,
        horizon=horizon,
        embargo=embargo,
        predictions_df=results_df,
    )


def run_walk_forward_quantiles(
    model_factory: Callable[[], Any],
    X: pd.DataFrame,
    y: pd.Series,
    initial_train_size: int,
    refit_every: int = 1,
    horizon: int = 1,
    embargo: int = 0,
    min_train_size: int = 50,
) -> pd.DataFrame:
    """Walk-forward OOS quantile forecasting with the same purging rules.

    Returns a DataFrame indexed like ``y`` over the OOS window with column
    ``actual_return`` followed by one float-named column per probability level.
    """
    _check_inputs(X, y, initial_train_size, refit_every, horizon, embargo, min_train_size)
    rows = list(
        _walk_forward(model_factory, X, y, initial_train_size, refit_every, horizon, embargo,
                      lambda m, r: m.predict_quantiles(r).iloc[-1])
    )
    q = pd.DataFrame(rows)
    q.index = y.index[initial_train_size:]
    q.insert(0, "actual_return", y.iloc[initial_train_size:].to_numpy(dtype=float))
    return q


__all__ = ["WalkForwardResult", "run_walk_forward_evaluation", "run_walk_forward_quantiles", "purged_train_end"]
