"""Train-only scalers for Price Level ablation (Seam B).

Enforces:
1. Scalers are fitted exclusively on the Train partition.
2. Validation and Test data are strictly transformed using Train statistics.
3. Out-of-bounds values are never clipped or clamped.
4. Support for 3D sequence tensors (LSTM) and 2D tabular features (XGBoost).
5. Exact inverse transformation back to physical USD/barrel.
"""

from __future__ import annotations

from typing import Any, overload
import numpy as np

from src.data.dataset import SupervisedBatch


class PriceLevelScaler:
    """Train-only scaler for 3D sequence batches in Price Level ablation."""

    def __init__(self) -> None:
        self.is_fitted_: bool = False
        self.feature_mean_: np.ndarray | None = None
        self.feature_std_: np.ndarray | None = None
        self.target_mean_: float | None = None
        self.target_std_: float | None = None

    def fit(self, train_batch: SupervisedBatch) -> PriceLevelScaler:
        """Compute mean and standard deviation exclusively on the Train partition."""
        if len(train_batch) == 0:
            raise ValueError("train_batch cannot be empty to fit PriceLevelScaler.")

        # Features shape: (N, lookback, n_channels)
        # Compute mean and std per channel across samples and timesteps
        self.feature_mean_ = np.mean(train_batch.features, axis=(0, 1)).astype(np.float64)
        raw_feat_std = np.std(train_batch.features, axis=(0, 1)).astype(np.float64)
        self.feature_std_ = np.where(raw_feat_std < 1e-12, 1.0, raw_feat_std)

        # Target shape: (N,)
        self.target_mean_ = float(np.mean(train_batch.targets))
        raw_target_std = float(np.std(train_batch.targets))
        self.target_std_ = raw_target_std if raw_target_std >= 1e-12 else 1.0

        self.is_fitted_ = True
        return self

    def _check_fitted(self) -> None:
        if not self.is_fitted_ or self.feature_mean_ is None or self.target_mean_ is None:
            raise RuntimeError("PriceLevelScaler must be fitted before calling transform/inverse.")

    def transform_features(self, features: np.ndarray) -> np.ndarray:
        """Transform 3D sequence features without clipping."""
        self._check_fitted()
        assert self.feature_mean_ is not None and self.feature_std_ is not None
        # features shape: (N, lookback, n_channels)
        # broadcast over channels
        return (features - self.feature_mean_) / self.feature_std_

    @overload
    def transform_targets(self, targets: np.ndarray) -> np.ndarray: ...

    @overload
    def transform_targets(self, targets: float) -> float: ...

    def transform_targets(self, targets: np.ndarray | float) -> np.ndarray | float:
        """Transform target price levels without clipping."""
        self._check_fitted()
        assert self.target_mean_ is not None and self.target_std_ is not None
        return (targets - self.target_mean_) / self.target_std_

    def transform(self, batch: SupervisedBatch) -> SupervisedBatch:
        """Transform a SupervisedBatch using the Train statistics."""
        self._check_fitted()
        scaled_features = self.transform_features(batch.features)
        scaled_targets = np.asarray(self.transform_targets(batch.targets), dtype=np.float64)

        return SupervisedBatch(
            features=scaled_features,
            targets=scaled_targets,
            origin_prices=batch.origin_prices,
            actual_prices=batch.actual_prices,
            forecast_origins=batch.forecast_origins,
            target_timestamps=batch.target_timestamps,
            feature_available_ats=batch.feature_available_ats,
            horizon=batch.horizon,
            scenario=batch.scenario,
            target_representation=batch.target_representation,
        )

    @overload
    def inverse_transform_targets(self, targets_scaled: np.ndarray) -> np.ndarray: ...

    @overload
    def inverse_transform_targets(self, targets_scaled: float) -> float: ...

    def inverse_transform_targets(self, targets_scaled: np.ndarray | float) -> np.ndarray | float:
        """Reconstruct scaled targets/predictions back to USD/barrel without clipping."""
        self._check_fitted()
        assert self.target_mean_ is not None and self.target_std_ is not None
        return targets_scaled * self.target_std_ + self.target_mean_

    def inverse_transform_features(self, features_scaled: np.ndarray) -> np.ndarray:
        """Reconstruct scaled features back to USD/barrel."""
        self._check_fitted()
        assert self.feature_mean_ is not None and self.feature_std_ is not None
        return features_scaled * self.feature_std_ + self.feature_mean_

    def to_dict(self) -> dict[str, Any]:
        """Serialize scaler statistics to dictionary."""
        return {
            "feature_mean": self.feature_mean_.tolist() if self.feature_mean_ is not None else None,
            "feature_std": self.feature_std_.tolist() if self.feature_std_ is not None else None,
            "target_mean": self.target_mean_,
            "target_std": self.target_std_,
            "is_fitted": self.is_fitted_,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PriceLevelScaler:
        """Instantiate and restore scaler from dictionary."""
        scaler = cls()
        if data.get("is_fitted", False) or data.get("target_mean") is not None:
            if data.get("feature_mean") is not None:
                scaler.feature_mean_ = np.array(data["feature_mean"], dtype=np.float64)
            if data.get("feature_std") is not None:
                scaler.feature_std_ = np.array(data["feature_std"], dtype=np.float64)
            scaler.target_mean_ = data.get("target_mean")
            scaler.target_std_ = data.get("target_std")
            scaler.is_fitted_ = True
        return scaler


class TabularPriceLevelScaler:
    """Train-only scaler for 2D tabular features and targets (e.g. for XGBoost)."""

    def __init__(self) -> None:
        self.is_fitted_: bool = False
        self.feature_mean_: np.ndarray | None = None
        self.feature_std_: np.ndarray | None = None
        self.target_mean_: float | None = None
        self.target_std_: float | None = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray | None = None,
    ) -> TabularPriceLevelScaler:
        """Fit feature (and optional target) scaling statistics exclusively on Train partition."""
        if len(X_train) == 0:
            raise ValueError("X_train cannot be empty to fit TabularPriceLevelScaler.")

        self.feature_mean_ = np.mean(X_train, axis=0).astype(np.float64)
        raw_feat_std = np.std(X_train, axis=0).astype(np.float64)
        self.feature_std_ = np.where(raw_feat_std < 1e-12, 1.0, raw_feat_std)

        if y_train is not None and len(y_train) > 0:
            self.target_mean_ = float(np.mean(y_train))
            raw_target_std = float(np.std(y_train))
            self.target_std_ = raw_target_std if raw_target_std >= 1e-12 else 1.0

        self.is_fitted_ = True
        return self

    def _check_fitted(self) -> None:
        if not self.is_fitted_ or self.feature_mean_ is None:
            raise RuntimeError("TabularPriceLevelScaler must be fitted before calling transform.")

    def transform_features(self, X: np.ndarray) -> np.ndarray:
        """Transform 2D tabular features without clipping."""
        self._check_fitted()
        assert self.feature_mean_ is not None and self.feature_std_ is not None
        return (X - self.feature_mean_) / self.feature_std_

    @overload
    def transform_targets(self, y: np.ndarray) -> np.ndarray: ...

    @overload
    def transform_targets(self, y: float) -> float: ...

    def transform_targets(self, y: np.ndarray | float) -> np.ndarray | float:
        """Transform target prices without clipping."""
        self._check_fitted()
        if self.target_mean_ is None or self.target_std_ is None:
            raise RuntimeError("Target statistics not fitted on TabularPriceLevelScaler.")
        return (y - self.target_mean_) / self.target_std_

    @overload
    def inverse_transform_targets(self, y_scaled: np.ndarray) -> np.ndarray: ...

    @overload
    def inverse_transform_targets(self, y_scaled: float) -> float: ...

    def inverse_transform_targets(self, y_scaled: np.ndarray | float) -> np.ndarray | float:
        """Reconstruct targets/predictions back to USD/barrel without clipping."""
        self._check_fitted()
        if self.target_mean_ is None or self.target_std_ is None:
            raise RuntimeError("Target statistics not fitted on TabularPriceLevelScaler.")
        return y_scaled * self.target_std_ + self.target_mean_

    def inverse_transform_features(self, X_scaled: np.ndarray) -> np.ndarray:
        """Reconstruct features back to original scale."""
        self._check_fitted()
        assert self.feature_mean_ is not None and self.feature_std_ is not None
        return X_scaled * self.feature_std_ + self.feature_mean_

    def to_dict(self) -> dict[str, Any]:
        """Serialize scaler statistics to dictionary."""
        return {
            "feature_mean": self.feature_mean_.tolist() if self.feature_mean_ is not None else None,
            "feature_std": self.feature_std_.tolist() if self.feature_std_ is not None else None,
            "target_mean": self.target_mean_,
            "target_std": self.target_std_,
            "is_fitted": self.is_fitted_,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TabularPriceLevelScaler:
        """Instantiate and restore scaler from dictionary."""
        scaler = cls()
        if data.get("is_fitted", False) or data.get("target_mean") is not None:
            if data.get("feature_mean") is not None:
                scaler.feature_mean_ = np.array(data["feature_mean"], dtype=np.float64)
            if data.get("feature_std") is not None:
                scaler.feature_std_ = np.array(data["feature_std"], dtype=np.float64)
            scaler.target_mean_ = data.get("target_mean")
            scaler.target_std_ = data.get("target_std")
            scaler.is_fitted_ = True
        return scaler
