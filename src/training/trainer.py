"""PyTorch training loop, deterministic seeding, and checkpoint management."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import random
from typing import Any
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.training.callbacks import EarlyStopping


def set_seed(seed: int = 42) -> None:
    """Enforce deterministic seed control across Python, NumPy, and PyTorch (CPU & CUDA)."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@dataclass
class RecurrentTrainingConfig:
    """Hyperparameters and configuration for training recurrent sequence models."""

    hidden_dim: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 15
    random_state: int = 42
    weight_decay: float = 0.0


@dataclass
class TrainingHistory:
    """Loss history and best epoch tracking for model training."""

    train_losses: list[float]
    val_losses: list[float]
    best_epoch: int
    best_val_loss: float


def train_recurrent_model(
    model: nn.Module,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray | None = None,
    y_val: np.ndarray | None = None,
    config: RecurrentTrainingConfig | None = None,
    checkpoint_path: str | Path | None = None,
    model_metadata: dict[str, Any] | None = None,
    device: torch.device | None = None,
) -> TrainingHistory:
    """Train a PyTorch recurrent neural model with Early Stopping and Checkpointing.

    Parameters:
    - model: nn.Module instance (LSTMNet or GRUNet).
    - X_train: Training sequence features (N, lookback, input_dim).
    - y_train: Training targets (N,).
    - X_val: Optional validation sequence features.
    - y_val: Optional validation targets.
    - config: Training configuration dataclass.
    - checkpoint_path: Optional path to save best checkpoint.
    - model_metadata: Optional dictionary with metadata to embed into checkpoint.
    - device: Target torch device (defaults to CPU).
    """
    cfg = config or RecurrentTrainingConfig()
    set_seed(cfg.random_state)

    dev = device or torch.device("cpu")
    model.to(dev)

    # Convert inputs to torch tensors
    train_tensor_x = torch.from_numpy(X_train).float()
    train_tensor_y = torch.from_numpy(y_train).float()

    train_dataset = TensorDataset(train_tensor_x, train_tensor_y)
    g = torch.Generator()
    g.manual_seed(cfg.random_state)
    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        generator=g,
        drop_last=False,
    )

    has_val = X_val is not None and y_val is not None and len(X_val) > 0
    if has_val:
        assert X_val is not None and y_val is not None
        val_tensor_x = torch.from_numpy(X_val).float().to(dev)
        val_tensor_y = torch.from_numpy(y_val).float().to(dev)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    early_stopping = EarlyStopping(patience=cfg.early_stopping_patience)
    best_state_dict: dict[str, torch.Tensor] | None = None
    best_epoch = 0
    best_val_loss = float("inf")

    train_losses: list[float] = []
    val_losses: list[float] = []

    for epoch in range(1, cfg.epochs + 1):
        # 1. Training step
        model.train()
        batch_losses: list[float] = []
        for bx, by in train_loader:
            bx, by = bx.to(dev), by.to(dev)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())

        epoch_train_loss = float(np.mean(batch_losses))
        train_losses.append(epoch_train_loss)

        # 2. Validation step
        if has_val:
            model.eval()
            with torch.no_grad():
                val_out = model(val_tensor_x)
                val_loss = criterion(val_out, val_tensor_y).item()
            val_losses.append(val_loss)

            early_stopping.step(val_loss)
            if early_stopping.is_best:
                best_val_loss = val_loss
                best_epoch = epoch
                best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}

                if checkpoint_path is not None:
                    cp_path = Path(checkpoint_path)
                    cp_path.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(
                        {
                            "epoch": epoch,
                            "best_val_loss": best_val_loss,
                            "model_state_dict": model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(),
                            "config": asdict(cfg),
                            "metadata": model_metadata or {},
                        },
                        cp_path,
                    )

            if early_stopping.should_stop:
                break
        else:
            # No validation provided
            best_epoch = epoch
            best_val_loss = epoch_train_loss
            best_state_dict = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    # Restore best weights
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)

    return TrainingHistory(
        train_losses=train_losses,
        val_losses=val_losses,
        best_epoch=best_epoch,
        best_val_loss=best_val_loss,
    )
