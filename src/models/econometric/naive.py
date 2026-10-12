"""Baseline Naive Models (M0a and M0b) for SPAFS V5.2.

Provides:
- M0a: NaiveZeroModel (Predicts zero return under Efficient Market Hypothesis / Random Walk).
- M0b: NaiveDirectionModel (Predicts directional momentum based on sign of current return).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


class NaiveZeroModel(BaseForecastingModel):
    """M0a: Naive Zero Return Benchmark (Random Walk / Martingale Difference).

    Formulation:
        E[r_{t+1}] = 0.0%  for all t.
        ŷ_{t+1} = 0
    Zero parameters estimated (K = 0). Acts as global theoretical benchmark for OOS-R².
    """

    def __init__(self) -> None:
        super().__init__(model_id="M0a")
        self.fitted_n: int = 0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> NaiveZeroModel:
        """Fit M0a (records sample size, no parameters estimated)."""
        self.fitted_n = len(y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate zero return forecasts with matching index."""
        self._check_is_fitted()
        return pd.Series(0.0, index=X.index, name="pred_return_M0a")

    def predict_direction(self, X: pd.DataFrame) -> pd.Series:
        """Generate zero directional forecasts."""
        self._check_is_fitted()
        return pd.Series(0, index=X.index, name="pred_direction_M0a", dtype=int)

    def get_params_summary(self) -> dict[str, Any]:
        """Return parameter summary for M0a."""
        return {
            "model_id": self.model_id,
            "name": self.spec.name,
            "num_parameters": 0,
            "constant": 0.0,
            "sample_size": self.fitted_n,
            "hypothesis": "Efficient Market Hypothesis (EMH): E[r_{t+1}] = 0",
        }


class NaiveDirectionModel(BaseForecastingModel):
    """M0b: Naive Directional Momentum Benchmark.

    Formulation:
        ŷ_{t+1} = 1 if r_{MG95, t} > 0 else 0
        r̂_{t+1} = r_{MG95, t} (persistence baseline)
    """

    def __init__(self) -> None:
        super().__init__(model_id="M0b")
        self.fitted_n: int = 0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> NaiveDirectionModel:
        """Fit M0b (validates input feature presence)."""
        _ = self._validate_input_x(X)
        self.fitted_n = len(y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Predict persistence return r̂_{t+1} = r_{MG95, t}."""
        self._check_is_fitted()
        X_val = self._validate_input_x(X)
        return pd.Series(X_val["mg95_return_pct"].copy(), name="pred_return_M0b")

    def predict_direction(self, X: pd.DataFrame) -> pd.Series:
        """Predict direction based on current observed return sign."""
        self._check_is_fitted()
        X_val = self._validate_input_x(X)
        dir_series = (X_val["mg95_return_pct"] > 0.0).astype(int)
        dir_series.name = "pred_direction_M0b"
        return dir_series

    def get_params_summary(self) -> dict[str, Any]:
        """Return parameter summary for M0b."""
        return {
            "model_id": self.model_id,
            "name": self.spec.name,
            "num_parameters": 0,
            "sample_size": self.fitted_n,
            "rule": "Directional persistence: ŷ_{t+1} = sign(r_{MG95, t})",
        }


__all__ = ["NaiveZeroModel", "NaiveDirectionModel"]
