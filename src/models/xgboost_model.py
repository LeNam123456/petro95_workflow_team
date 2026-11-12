"""XGBoost forecaster model for direct multi-horizon forecasting (Seam D).

Implements direct regression on stationary relative change targets
(R_{o,h} = (P_{o+h} - P_o) / P_o) and price levels with:
1. Feature extraction from SupervisedBatch via Seam C.
2. Training with early stopping on validation loss.
3. Price reconstruction in USD/barrel.
4. Feature importance extraction (gain, weight).
5. Canonical seed determinism (default 42).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
import xgboost as xgb

from src.data.dataset import SupervisedBatch
from src.data.scaling import TabularPriceLevelScaler
from src.evaluation.reconstruction import reconstruct_from_price_level, reconstruct_price
from src.features.engineering import extract_xgboost_features


@dataclass
class XGBoostConfig:
    """Hyperparameters and execution configuration for XGBoost."""

    n_estimators: int = 500
    max_depth: int = 4
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    early_stopping_rounds: int = 15
    random_state: int = 42
    eval_metric: str = "rmse"


class XGBoostForecaster:
    """Direct multi-horizon XGBoost forecaster."""

    def __init__(
        self,
        config: XGBoostConfig | None = None,
        **kwargs: Any,
    ) -> None:
        self.name = "XGBoost"
        base_config = config or XGBoostConfig()
        if kwargs:
            # Override any explicitly supplied config parameters
            valid_fields = set(base_config.__dataclass_fields__.keys())  # type: ignore[attr-defined]
            override_dict = {k: v for k, v in kwargs.items() if k in valid_fields}
            self.config = XGBoostConfig(**{**base_config.__dict__, **override_dict})
        else:
            self.config = base_config

        self.estimator: xgb.XGBRegressor | None = None
        self.feature_names_: list[str] = []
        self.best_iteration_: int | None = None
        self.best_score_: float | None = None
        self.scaler: TabularPriceLevelScaler | None = None
        self.target_representation: str | None = None

    def fit(
        self,
        train_batch: SupervisedBatch,
        val_batch: SupervisedBatch | None = None,
        verbose: bool = False,
    ) -> XGBoostForecaster:
        """Fit XGBoost model on train_batch with early stopping on val_batch."""
        self.target_representation = train_batch.target_representation
        X_train, feature_names = extract_xgboost_features(train_batch)
        y_train = train_batch.targets
        self.feature_names_ = feature_names

        if self.target_representation == "price_level":
            self.scaler = TabularPriceLevelScaler().fit(X_train, y_train)
            X_train = self.scaler.transform_features(X_train)
            y_train = self.scaler.transform_targets(y_train)

        df_train = pd.DataFrame(X_train, columns=feature_names)

        eval_set = []
        if val_batch is not None and len(val_batch) > 0:
            X_val, _ = extract_xgboost_features(val_batch)
            y_val = val_batch.targets
            if self.target_representation == "price_level" and self.scaler is not None:
                X_val = self.scaler.transform_features(X_val)
                y_val = self.scaler.transform_targets(y_val)
            df_val = pd.DataFrame(X_val, columns=feature_names)
            eval_set.append((df_val, y_val))

        early_stopping = self.config.early_stopping_rounds if eval_set else None

        self.estimator = xgb.XGBRegressor(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            random_state=self.config.random_state,
            eval_metric=self.config.eval_metric,
            early_stopping_rounds=early_stopping,
            n_jobs=-1,
        )

        self.estimator.fit(
            df_train,
            y_train,
            eval_set=eval_set if eval_set else None,
            verbose=verbose,
        )

        if hasattr(self.estimator, "best_iteration"):
            self.best_iteration_ = self.estimator.best_iteration
        if hasattr(self.estimator, "best_score"):
            self.best_score_ = float(self.estimator.best_score)

        return self

    def predict(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate predictions in target representation space."""
        if self.estimator is None:
            raise RuntimeError("Model must be fitted before calling predict().")

        X, _ = extract_xgboost_features(batch)
        if self.target_representation == "price_level" and self.scaler is not None:
            X = self.scaler.transform_features(X)

        df_x = pd.DataFrame(X, columns=self.feature_names_)
        preds = self.estimator.predict(df_x)

        if self.target_representation == "price_level" and self.scaler is not None:
            preds = np.asarray(self.scaler.inverse_transform_targets(preds), dtype=np.float64)

        return np.asarray(preds, dtype=np.float64)

    def predict_prices(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate reconstructed price level predictions in USD/barrel."""
        preds = self.predict(batch)
        if batch.target_representation == "relative_change":
            return np.asarray(reconstruct_price(batch.origin_prices, preds), dtype=np.float64)
        elif batch.target_representation == "price_level":
            return np.asarray(reconstruct_from_price_level(preds), dtype=np.float64)
        else:
            raise ValueError(f"Unknown target representation: {batch.target_representation}")

    def get_feature_importance_df(self, horizon: int, scenario: str) -> pd.DataFrame:
        """Export feature importance metrics (gain, weight, relative) for analysis."""
        if self.estimator is None or not self.feature_names_:
            raise RuntimeError("Model must be fitted before accessing feature importance.")

        booster = self.estimator.get_booster()
        gain_scores = booster.get_score(importance_type="gain")
        weight_scores = booster.get_score(importance_type="weight")

        rows: list[dict[str, Any]] = []
        target_rep = self.target_representation or "relative_change"
        for name in self.feature_names_:
            raw_gain = gain_scores.get(name, 0.0)
            raw_weight = weight_scores.get(name, 0.0)
            gain = float(np.mean(raw_gain)) if isinstance(raw_gain, (list, tuple, np.ndarray)) else float(raw_gain)
            weight = float(np.mean(raw_weight)) if isinstance(raw_weight, (list, tuple, np.ndarray)) else float(raw_weight)
            rows.append({
                "feature_name": name,
                "importance_gain": gain,
                "importance_weight": weight,
                "horizon": horizon,
                "scenario": scenario,
                "target_representation": target_rep,
            })

        df = pd.DataFrame(rows)
        total_gain = df["importance_gain"].sum()
        df["importance_relative"] = (
            df["importance_gain"] / total_gain if total_gain > 0 else 0.0
        )
        df["rank"] = df["importance_gain"].rank(ascending=False, method="min").astype(int)
        df = df.sort_values(by="rank").reset_index(drop=True)
        return df
