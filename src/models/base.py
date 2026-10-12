"""Base Forecasting Model Interface for SPAFS V5.2.

Defines the abstract base class and common contracts for all empirical models
in the SPAFS matrix (M0a through M6).

Guarantees:
1. Unified API: Every model adheres strictly to .fit(), .predict(), .predict_direction(),
   and .get_params_summary().
2. Time-series indexing preservation: Predictions preserve DatetimeIndex from input X.
3. Serialization integrity: Zero-retrain artifact persistence via joblib.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd

from src.data_proccessing.exceptions import DataContractViolationError
from src.data_proccessing.model_schemas import ModelSpec, get_model_spec

logger = logging.getLogger("SPAFS_V5.2")


class BaseForecastingModel(ABC):
    """Abstract base class for all forecasting models in SPAFS V5.2.

    Args:
        model_id (str): Identifier of the model in MODEL_REGISTRY (e.g. 'M0a', 'M3', 'M4').
    """

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.spec: ModelSpec = get_model_spec(model_id)
        self.is_fitted: bool = False
        self.feature_names: list[str] = list(self.spec.features)
        self.target_name: str = self.spec.target

    def _check_is_fitted(self) -> None:
        """Raise RuntimeError if model has not been fitted."""
        if not self.is_fitted:
            raise RuntimeError(
                f"Model '{self.model_id}' is not fitted yet. Call .fit(X, y) before predicting."
            )

    def _validate_input_x(self, X: pd.DataFrame) -> pd.DataFrame:
        """Validate feature matrix against model schema."""
        if len(self.feature_names) > 0:
            missing = [f for f in self.feature_names if f not in X.columns]
            if missing:
                raise DataContractViolationError(
                    f"Model '{self.model_id}' expects features {self.feature_names}, "
                    f"but X is missing: {missing}"
                )
            return X[self.feature_names].copy()
        return X.copy()

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> BaseForecastingModel:
        """Fit the model parameters on historical features X and target y.

        Args:
            X (pd.DataFrame): Design matrix of stationary predictor features.
            y (pd.Series): Target return series or binary direction.

        Returns:
            BaseForecastingModel: Fitted model instance.
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate out-of-sample or in-sample point return forecasts r̂_{t+1}.

        Args:
            X (pd.DataFrame): Feature matrix for forecast origin(s).

        Returns:
            pd.Series: Continuous return forecast r̂_{t+1} with matching DatetimeIndex.
        """
        pass

    def predict_direction(self, X: pd.DataFrame) -> pd.Series:
        """Generate binary directional forecasts ŷ_{t+1} in {0, 1}.

        Default implementation converts continuous return forecast r̂_{t+1} via indicator:
        ŷ_{t+1} = 1 if r̂_{t+1} > 0 else 0.
        Subclasses (e.g. M0b) may override with specialized directional logic.

        Args:
            X (pd.DataFrame): Feature matrix for forecast origin(s).

        Returns:
            pd.Series: Binary direction forecast in {0, 1} with matching DatetimeIndex.
        """
        pred_ret = self.predict(X)
        dir_series = (pred_ret > 0.0).astype(int)
        dir_series.name = "pred_direction"
        return dir_series

    @abstractmethod
    def get_params_summary(self) -> dict[str, Any]:
        """Return structural parameters, coefficients, standard errors, and fit metrics.

        Returns:
            dict[str, Any]: Model-specific parameter dictionary for artifact persistence.
        """
        pass

    def save(self, filepath: Path | str) -> Path:
        """Serialize fitted model to binary file via joblib.

        Args:
            filepath (Path | str): Target file path (e.g. 'artifacts/models/M3.joblib').

        Returns:
            Path: Resolved Path where model was saved.
        """
        self._check_is_fitted()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Saved model '%s' to %s", self.model_id, path)
        return path

    @classmethod
    def load(cls, filepath: Path | str) -> BaseForecastingModel:
        """Load serialized model from disk.

        Args:
            filepath (Path | str): Path to saved .joblib file.

        Returns:
            BaseForecastingModel: Loaded model instance.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at: {path}")
        model = joblib.load(path)
        if not isinstance(model, BaseForecastingModel):
            raise TypeError(f"Loaded object from {path} is not a BaseForecastingModel instance.")
        logger.info("Loaded model '%s' from %s", model.model_id, path)
        return model
