"""Base class and common functionality for PyTorch recurrent forecasters."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import torch
import torch.nn as nn

from src.data.dataset import SupervisedBatch
from src.data.scaling import PriceLevelScaler
from src.evaluation.reconstruction import reconstruct_from_price_level, reconstruct_price
from src.training.trainer import RecurrentTrainingConfig, TrainingHistory, train_recurrent_model


class BaseRecurrentForecaster:
    """Base class for sequence-based neural forecasters."""

    name: str = "BaseRecurrent"

    def __init__(
        self,
        config: RecurrentTrainingConfig | None = None,
        checkpoint_dir: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        base_config = config or RecurrentTrainingConfig()
        if kwargs:
            valid_fields = set(base_config.__dataclass_fields__.keys())  # type: ignore[attr-defined]
            override_dict = {k: v for k, v in kwargs.items() if k in valid_fields}
            self.config = RecurrentTrainingConfig(**{**base_config.__dict__, **override_dict})
        else:
            self.config = base_config

        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self.network: nn.Module | None = None
        self.history: TrainingHistory | None = None
        self.input_dim: int | None = None
        self.horizon: int | None = None
        self.scenario: str | None = None
        self.target_representation: str | None = None
        self.scaler: PriceLevelScaler | None = None

    def _build_network(self, input_dim: int) -> nn.Module:
        """Construct the specific neural architecture (implemented by subclasses)."""
        raise NotImplementedError

    def fit(
        self,
        train_batch: SupervisedBatch,
        val_batch: SupervisedBatch | None = None,
        checkpoint_path: str | Path | None = None,
    ) -> BaseRecurrentForecaster:
        """Fit recurrent neural model using SupervisedBatch with Early Stopping."""
        if len(train_batch) == 0:
            raise ValueError("train_batch cannot be empty.")

        self.input_dim = train_batch.features.shape[2]
        self.horizon = train_batch.horizon
        self.scenario = train_batch.scenario
        self.target_representation = train_batch.target_representation

        self.network = self._build_network(self.input_dim)

        if self.target_representation == "price_level":
            self.scaler = PriceLevelScaler().fit(train_batch)
            train_batch_to_use = self.scaler.transform(train_batch)
            val_batch_to_use = (
                self.scaler.transform(val_batch)
                if val_batch is not None and len(val_batch) > 0
                else None
            )
        else:
            train_batch_to_use = train_batch
            val_batch_to_use = val_batch

        X_train = train_batch_to_use.features
        y_train = train_batch_to_use.targets

        X_val = val_batch_to_use.features if val_batch_to_use is not None and len(val_batch_to_use) > 0 else None
        y_val = val_batch_to_use.targets if val_batch_to_use is not None and len(val_batch_to_use) > 0 else None

        # Resolve checkpoint destination
        cp_path = checkpoint_path
        if cp_path is None and self.checkpoint_dir is not None:
            filename = (
                f"{self.name.lower()}_{self.scenario}_{self.target_representation}_h{self.horizon}.pt"
            )
            cp_path = self.checkpoint_dir / filename

        metadata: dict[str, Any] = {
            "model_name": self.name,
            "horizon": self.horizon,
            "scenario": self.scenario,
            "target_representation": self.target_representation,
            "input_dim": self.input_dim,
        }
        if self.scaler is not None:
            metadata["scaler"] = self.scaler.to_dict()

        self.history = train_recurrent_model(
            model=self.network,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            config=self.config,
            checkpoint_path=cp_path,
            model_metadata=metadata,
        )

        return self

    def predict(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate forecasts in target representation space."""
        if self.network is None:
            raise RuntimeError("Model must be fitted before calling predict().")

        if len(batch) == 0:
            return np.empty((0,), dtype=np.float64)

        if self.target_representation == "price_level" and self.scaler is not None:
            batch_to_use = self.scaler.transform(batch)
        else:
            batch_to_use = batch

        self.network.eval()
        with torch.no_grad():
            tensor_x = torch.from_numpy(batch_to_use.features).float()
            out = self.network(tensor_x)
            preds = out.cpu().numpy().astype(np.float64)

        if self.target_representation == "price_level" and self.scaler is not None:
            preds = np.asarray(self.scaler.inverse_transform_targets(preds), dtype=np.float64)

        return preds

    def load_checkpoint(self, checkpoint_path: str | Path) -> BaseRecurrentForecaster:
        """Restore model weights, network configuration, and coupled scaler from checkpoint."""
        cp_path = Path(checkpoint_path)
        if not cp_path.exists():
            raise FileNotFoundError(f"Checkpoint not found at: {cp_path}")

        ckpt = torch.load(cp_path, map_location="cpu", weights_only=False)
        metadata = ckpt.get("metadata", {})
        self.input_dim = metadata.get("input_dim", self.input_dim)
        self.horizon = metadata.get("horizon", self.horizon)
        self.scenario = metadata.get("scenario", self.scenario)
        self.target_representation = metadata.get("target_representation", self.target_representation)

        if self.network is None and self.input_dim is not None:
            self.network = self._build_network(self.input_dim)

        if self.network is not None and "model_state_dict" in ckpt:
            self.network.load_state_dict(ckpt["model_state_dict"])

        if "scaler" in metadata and metadata["scaler"] is not None:
            self.scaler = PriceLevelScaler.from_dict(metadata["scaler"])

        return self

    def predict_prices(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate reconstructed price level forecasts in USD/barrel."""
        preds = self.predict(batch)
        if batch.target_representation == "relative_change":
            return np.asarray(reconstruct_price(batch.origin_prices, preds), dtype=np.float64)
        elif batch.target_representation == "price_level":
            return np.asarray(reconstruct_from_price_level(preds), dtype=np.float64)
        else:
            raise ValueError(f"Unknown target representation: {batch.target_representation}")
