"""Tests for LSTM and GRU recurrent sequence models (Seam E).

Verifies:
1. 3D Sequence input tensors (N, 30, 1) and (N, 30, 2) processed correctly.
2. LSTM and GRU forward passes and Forecaster protocol compliance.
3. Predictions output in target representation space (relative change).
4. Price reconstruction to USD/barrel: P_hat = P_o * (1 + R_hat).
5. Deterministic reproducibility with canonical seed 42.
6. Absence of NaN or infinite outputs.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch

from src.data.dataset import build_supervised_samples
from src.models.base import Forecaster
from src.models.gru import GRUForecaster
from src.models.lstm import LSTMForecaster


@pytest.fixture
def sample_partitions() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create Train, Val, and Test synthetic DataFrames."""
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


@pytest.mark.parametrize("model_cls,model_name", [
    (LSTMForecaster, "LSTM"),
    (GRUForecaster, "GRU"),
])
@pytest.mark.parametrize("scenario,input_dim", [
    ("univariate", 1),
    ("multivariate", 2),
])
def test_recurrent_forecaster_fit_predict(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    model_cls: type,
    model_name: str,
    scenario: str,
    input_dim: int,
) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario=scenario, target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario=scenario, target_representation="relative_change")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=1, scenario=scenario, target_representation="relative_change")

    assert train_batch.features.ndim == 3
    assert train_batch.features.shape[1] == 30
    assert train_batch.features.shape[2] == input_dim

    model = model_cls(
        hidden_dim=16,
        num_layers=1,
        epochs=3,
        batch_size=16,
        random_state=42,
    )
    assert isinstance(model, Forecaster)
    assert model.name == model_name

    model.fit(train_batch, val_batch=val_batch)

    # 1. Predict in target representation
    rel_preds = model.predict(test_batch)
    assert isinstance(rel_preds, np.ndarray)
    assert rel_preds.shape == (len(test_batch),)
    assert not np.isnan(rel_preds).any()
    assert not np.isinf(rel_preds).any()

    # 2. Predict prices in USD/barrel
    pred_prices = model.predict_prices(test_batch)
    assert isinstance(pred_prices, np.ndarray)
    assert pred_prices.shape == (len(test_batch),)
    assert (pred_prices > 0).all()

    # 3. Verify exact reconstruction: P_hat = P_o * (1 + R_hat)
    expected_prices = test_batch.origin_prices * (1.0 + rel_preds)
    np.testing.assert_allclose(pred_prices, expected_prices, rtol=1e-6)


@pytest.mark.parametrize("model_cls", [LSTMForecaster, GRUForecaster])
def test_recurrent_forecaster_determinism_seed_42(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    model_cls: type,
) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")

    model1 = model_cls(hidden_dim=16, num_layers=1, epochs=3, batch_size=16, random_state=42)
    model1.fit(train_batch, val_batch=val_batch)
    preds1 = model1.predict(test_batch)

    model2 = model_cls(hidden_dim=16, num_layers=1, epochs=3, batch_size=16, random_state=42)
    model2.fit(train_batch, val_batch=val_batch)
    preds2 = model2.predict(test_batch)

    np.testing.assert_allclose(preds1, preds2, rtol=1e-5, atol=1e-6)


def test_lstm_fit_predict_price_level(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")

    model = LSTMForecaster(hidden_dim=16, num_layers=1, epochs=3, batch_size=16, random_state=42)
    model.fit(train_batch, val_batch=val_batch)

    # 1. Scaler exists and is fitted
    assert model.scaler is not None
    assert model.scaler.is_fitted_

    # 2. Predict prices in USD/barrel
    pred_prices = model.predict_prices(test_batch)
    assert isinstance(pred_prices, np.ndarray)
    assert pred_prices.shape == (len(test_batch),)
    assert (pred_prices > 50.0).all()
    assert (pred_prices < 150.0).all()


def test_lstm_checkpoint_restores_scaler(
    sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    tmp_path: Path,
) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")

    cp_path = tmp_path / "test_checkpoint.pt"
    model = LSTMForecaster(hidden_dim=16, num_layers=1, epochs=3, batch_size=16, random_state=42)
    model.fit(train_batch, val_batch=val_batch, checkpoint_path=cp_path)
    orig_preds = model.predict_prices(test_batch)

    # Instantiate fresh model without fit and load checkpoint
    loaded_model = LSTMForecaster(hidden_dim=16, num_layers=1)
    loaded_model.load_checkpoint(cp_path)

    # Scaler must be restored and fitted
    assert loaded_model.scaler is not None
    assert loaded_model.scaler.is_fitted_

    loaded_preds = loaded_model.predict_prices(test_batch)
    np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-5)


