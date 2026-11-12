"""Base definitions and protocols for forecasters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
import numpy as np

from src.data.dataset import SupervisedBatch


@runtime_checkable
class Forecaster(Protocol):
    """Protocol defining common forecaster interface."""

    name: str

    def fit(
        self,
        train_batch: SupervisedBatch,
        val_batch: SupervisedBatch | None = None,
    ) -> Forecaster:
        """Fit model parameters on train_batch, optionally validating on val_batch."""
        ...

    def predict(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate forecasts in target representation space (e.g. relative change)."""
        ...

    def predict_prices(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate reconstructed price level forecasts in USD/barrel."""
        ...
