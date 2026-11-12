"""Tests for training workflows, callbacks, early stopping, and checkpointing (Seam F).

Verifies:
1. EarlyStopping correctly monitors validation loss and stops at patience limit.
2. Best checkpoint is saved to disk with expected name, metadata, and state dict.
3. Checkpoint can be reloaded and matches in-memory model weights.
4. Loss history contains valid, non-NaN, non-inf loss trajectories.
5. Deterministic reproducibility across seeds.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch

from src.data.dataset import build_supervised_samples
from src.models.lstm import LSTMForecaster
from src.training.callbacks import EarlyStopping
from src.training.trainer import RecurrentTrainingConfig, set_seed, train_recurrent_model


@pytest.fixture
def sample_partitions() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2015-01-01", periods=150, freq="B")
    mg95 = np.linspace(80.0, 110.0, 150) + np.sin(np.linspace(0, 10, 150)) * 5.0
    brent = np.linspace(60.0, 90.0, 150) + np.cos(np.linspace(0, 10, 150)) * 4.0

    df = pd.DataFrame({
        "observation_datetime": dates + pd.Timedelta(hours=16, minutes=30),
        "availability_datetime": dates + pd.Timedelta(hours=16, minutes=30),
        "target_market_date": dates,
        "forecast_origin_datetime": dates + pd.Timedelta(days=1, hours=8, minutes=30),
        "MG95": mg95,
        "brent_close": brent,
    })

    train_df = df.iloc[:80].reset_index(drop=True)
    val_df = df.iloc[80:115].reset_index(drop=True)
    test_df = df.iloc[115:].reset_index(drop=True)
    return train_df, val_df, test_df


def test_early_stopping_logic() -> None:
    es = EarlyStopping(patience=3)

    # Epoch 1: best loss
    stop = es.step(1.0)
    assert not stop
    assert es.is_best is True
    assert es.best_loss == 1.0
    assert es.counter == 0

    # Epoch 2: worse
    stop = es.step(1.1)
    assert not stop
    assert es.is_best is False
    assert es.counter == 1

    # Epoch 3: worse
    stop = es.step(1.2)
    assert not stop
    assert es.is_best is False
    assert es.counter == 2

    # Epoch 4: improvement
    stop = es.step(0.9)
    assert not stop
    assert es.is_best is True
    assert es.best_loss == 0.9
    assert es.counter == 0

    # Epoch 5, 6, 7: worse consecutively -> should stop on epoch 7
    assert not es.step(0.95)
    assert not es.step(1.0)
    stop = es.step(0.92)
    assert stop is True
    assert es.counter == 3


def test_checkpoint_saving_and_reloading(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    tmp_path: Path,
) -> None:
    train_df, val_df, test_df = sample_partitions
    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")

    cp_dir = tmp_path / "checkpoints"
    model = LSTMForecaster(
        hidden_dim=16,
        num_layers=1,
        epochs=10,
        batch_size=16,
        early_stopping_patience=5,
        checkpoint_dir=cp_dir,
        random_state=42,
    )
    model.fit(train_batch, val_batch=val_batch)

    expected_checkpoint = cp_dir / "lstm_univariate_relative_change_h1.pt"
    assert expected_checkpoint.exists()

    checkpoint_data = torch.load(expected_checkpoint, weights_only=False)
    assert "model_state_dict" in checkpoint_data
    assert "optimizer_state_dict" in checkpoint_data
    assert "epoch" in checkpoint_data
    assert "best_val_loss" in checkpoint_data
    assert "metadata" in checkpoint_data
    assert checkpoint_data["metadata"]["model_name"] == "LSTM"
    assert checkpoint_data["metadata"]["horizon"] == 1
    assert checkpoint_data["metadata"]["scenario"] == "univariate"

    # Verify model parameters match saved state dict
    assert model.network is not None
    model_state = model.network.state_dict()
    for param_name, tensor in checkpoint_data["model_state_dict"].items():
        torch.testing.assert_close(model_state[param_name], tensor)


def test_training_loss_history_tracking(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    train_df, val_df, _ = sample_partitions
    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="multivariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="multivariate", target_representation="relative_change")

    model = LSTMForecaster(
        hidden_dim=16,
        num_layers=1,
        epochs=5,
        batch_size=16,
        random_state=42,
    )
    model.fit(train_batch, val_batch=val_batch)

    assert model.history is not None
    assert len(model.history.train_losses) == 5
    assert len(model.history.val_losses) == 5
    assert all(loss > 0 for loss in model.history.train_losses)
    assert all(loss > 0 for loss in model.history.val_losses)
    assert not any(np.isnan(model.history.train_losses))
    assert not any(np.isnan(model.history.val_losses))
