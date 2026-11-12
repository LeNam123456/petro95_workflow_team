"""Training callbacks for deep learning models."""

from __future__ import annotations


class EarlyStopping:
    """Early stopping monitor for validation loss.

    Stops training when validation loss fails to improve after `patience` consecutive epochs.
    """

    def __init__(
        self,
        patience: int = 15,
        min_delta: float = 0.0,
    ) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss: float = float("inf")
        self.counter: int = 0
        self.should_stop: bool = False
        self.is_best: bool = False

    def step(self, current_loss: float) -> bool:
        """Update monitor with current epoch's validation loss.

        Returns True if early stopping criteria is met and training should halt.
        """
        if current_loss < (self.best_loss - self.min_delta):
            self.best_loss = current_loss
            self.counter = 0
            self.is_best = True
        else:
            self.counter += 1
            self.is_best = False
            if self.counter >= self.patience:
                self.should_stop = True

        return self.should_stop
