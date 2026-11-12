"""GRU recurrent forecaster implementation."""

from __future__ import annotations

import torch
import torch.nn as nn

from src.models.recurrent_base import BaseRecurrentForecaster


class GRUNet(nn.Module):
    """GRU sequence network with unconstrained linear head."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        dropout_val = dropout if num_layers > 1 else 0.0
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout_val,
        )
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through GRU sequence model.

        Parameters:
        - x: Tensor of shape (batch_size, seq_len, input_dim)

        Returns:
        - Tensor of shape (batch_size,)
        """
        # out shape: (batch_size, seq_len, hidden_dim)
        out, _ = self.gru(x)
        last_step = out[:, -1, :]  # shape: (batch_size, hidden_dim)
        pred = self.fc(last_step)  # shape: (batch_size, 1)
        return pred.view(-1)


class GRUForecaster(BaseRecurrentForecaster):
    """Forecaster wrapper for GRU architecture."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = "GRU"

    def _build_network(self, input_dim: int) -> nn.Module:
        return GRUNet(
            input_dim=input_dim,
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout,
        )
