"""LightGBM Machine Learning Models for SPAFS V5.2.

Provides:
- M4: TechnicalLGBMModel (Non-linear GBDT capturing autoregressive momentum and trailing volatility
  across a multi-seed ensemble).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


class TechnicalLGBMModel(BaseForecastingModel):
    """M4: Technical LightGBM Model (Momentum & Volatility).

    Features (K = 10):
        1. mg95_return_pct: Current return
        2-4. mg95_return_lag1..3: Mogas autoregressive lags
        5. brent_return_pct_aligned: Aligned Brent return
        6-8. brent_return_lag1..3: Brent exogenous lags
        9. vol_mg95_30d: Trailing 30-day volatility
        10. economic_shock_flag: Boolean extreme shock flag

    Args:
        learning_rate (float, optional): GBDT shrinkage rate. Defaults to 0.03.
        num_leaves (int, optional): Max tree leaves per base learner. Defaults to 15.
        min_child_samples (int, optional): Min samples per leaf. Defaults to 20.
        n_estimators (int, optional): Boosting iterations. Defaults to 100.
        subsample (float, optional): Subsample ratio of training instances. Defaults to 0.8.
        colsample_bytree (float, optional): Subsample ratio of columns. Defaults to 0.8.
        seeds (tuple[int, ...], optional): Random seeds for ensemble averaging.
            Defaults to (42, 101, 202, 303, 404, 505, 606, 707, 808, 909).
    """

    def __init__(
        self,
        learning_rate: float = 0.03,
        num_leaves: int = 15,
        min_child_samples: int = 20,
        n_estimators: int = 100,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        seeds: tuple[int, ...] = (42, 101, 202, 303, 404, 505, 606, 707, 808, 909),
    ) -> None:
        super().__init__(model_id="M4")
        self.learning_rate = learning_rate
        self.num_leaves = num_leaves
        self.min_child_samples = min_child_samples
        self.n_estimators = n_estimators
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.seeds = seeds

        self.fitted_models_: list[lgb.LGBMRegressor] = []
        self.feature_importances_gain_: dict[str, float] = {}
        self.feature_importances_split_: dict[str, float] = {}
        self.fitted_n_: int = 0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> TechnicalLGBMModel:
        """Fit LightGBM models across the configured random seeds.

        Args:
            X (pd.DataFrame): Whitelisted feature matrix.
            y (pd.Series): Target continuous return series.
        """
        X_val = self._validate_input_x(X)
        self.fitted_n_ = len(y)
        self.fitted_models_ = []

        # Convert boolean flags to integers for LightGBM
        X_clean = X_val.copy()
        for col in X_clean.select_dtypes(include=["bool"]).columns:
            X_clean[col] = X_clean[col].astype(int)

        feature_cols = list(X_clean.columns)
        gain_acc = np.zeros(len(feature_cols))
        split_acc = np.zeros(len(feature_cols))

        for seed in self.seeds:
            model = lgb.LGBMRegressor(
                objective="regression",
                metric="rmse",
                learning_rate=self.learning_rate,
                num_leaves=self.num_leaves,
                min_child_samples=self.min_child_samples,
                n_estimators=self.n_estimators,
                subsample=self.subsample,
                subsample_freq=1,
                colsample_bytree=self.colsample_bytree,
                random_state=seed,
                n_jobs=-1,
                verbosity=-1,
            )
            model.fit(X_clean, y)
            self.fitted_models_.append(model)

            # Accumulate feature importances
            gain_acc += model.booster_.feature_importance(importance_type="gain")
            split_acc += model.booster_.feature_importance(importance_type="split")

        # Average importances across seeds
        n_seeds = len(self.seeds)
        self.feature_importances_gain_ = {
            col: float(val / n_seeds) for col, val in zip(feature_cols, gain_acc)
        }
        self.feature_importances_split_ = {
            col: float(val / n_seeds) for col, val in zip(feature_cols, split_acc)
        }

        self.is_fitted = True
        logger.debug(
            "Fitted M4 LightGBM ensemble (%d seeds, N=%d, features=%d)",
            n_seeds,
            self.fitted_n_,
            len(feature_cols),
        )
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate ensemble-averaged point return forecasts."""
        self._check_is_fitted()
        X_val = self._validate_input_x(X)

        X_clean = X_val.copy()
        for col in X_clean.select_dtypes(include=["bool"]).columns:
            X_clean[col] = X_clean[col].astype(int)

        preds = np.zeros(len(X_clean))
        for model in self.fitted_models_:
            preds += model.predict(X_clean)
        preds /= len(self.fitted_models_)

        return pd.Series(preds, index=X.index, name="pred_return_M4")

    def get_params_summary(self) -> dict[str, Any]:
        """Return hyperparameters and feature importance tables."""
        self._check_is_fitted()

        return {
            "model_id": self.model_id,
            "name": self.spec.name,
            "num_seeds": len(self.seeds),
            "sample_size": self.fitted_n_,
            "hyperparameters": {
                "learning_rate": self.learning_rate,
                "num_leaves": self.num_leaves,
                "min_child_samples": self.min_child_samples,
                "n_estimators": self.n_estimators,
                "subsample": self.subsample,
                "colsample_bytree": self.colsample_bytree,
            },
            "feature_importance_gain": dict(
                sorted(
                    self.feature_importances_gain_.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ),
            "feature_importance_split": dict(
                sorted(
                    self.feature_importances_split_.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ),
        }


__all__ = ["TechnicalLGBMModel"]
