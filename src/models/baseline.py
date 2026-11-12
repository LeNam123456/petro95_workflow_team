"""Naive Persistence baseline forecasting model.

Predicts that the future price at horizon h will equal the latest available price
at the forecast origin:
    P_hat_{o+h} = P_o
"""

from __future__ import annotations

import numpy as np

from src.data.dataset import SupervisedBatch
from src.evaluation.reconstruction import reconstruct_price


class NaivePersistenceModel:
    """Naive persistence baseline forecaster."""

    def __init__(self) -> None:
        self.name = "Naive"

    def fit(
        self,
        train_batch: SupervisedBatch,
        val_batch: SupervisedBatch | None = None,
    ) -> NaivePersistenceModel:
        """No parameters to train for Naive Persistence."""
        return self

    def predict(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate predictions in target representation space.

        - For relative change: returns 0.0 (no change predicted)
        - For price level: returns origin price P_o
        """
        n_samples = len(batch)
        if batch.target_representation == "relative_change":
            return np.zeros(n_samples, dtype=np.float64)
        elif batch.target_representation == "price_level":
            return np.asarray(batch.origin_prices, dtype=np.float64).copy()
        else:
            raise ValueError(f"Unknown target representation: {batch.target_representation}")

    def predict_prices(self, batch: SupervisedBatch) -> np.ndarray:
        """Generate reconstructed price level predictions in USD/barrel."""
        preds = self.predict(batch)
        if batch.target_representation == "relative_change":
            return np.asarray(reconstruct_price(batch.origin_prices, preds), dtype=np.float64)
        return preds
