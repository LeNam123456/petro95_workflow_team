"""Tests for XGBoost forecasting model (Seam D).

Verifies:
1. Model trains on SupervisedBatch with early stopping on validation batch.
2. Predictions output in target representation space (relative change).
3. Price reconstruction to physical price levels (USD/barrel).
4. Feature importance extraction returns valid mappings for all features.
5. Deterministic reproducibility with seed 42.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.dataset import build_supervised_samples
from src.models.xgboost_model import XGBoostForecaster


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


def test_xgboost_fit_predict_relative_change(sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=1, scenario="univariate", target_representation="relative_change")

    model = XGBoostForecaster(n_estimators=50, max_depth=3, random_state=42)
    model.fit(train_batch, val_batch=val_batch)

    # 1. Predict in target representation
    rel_preds = model.predict(test_batch)
    assert isinstance(rel_preds, np.ndarray)
    assert rel_preds.shape == (len(test_batch),)
    assert not np.isnan(rel_preds).any()

    # 2. Predict prices in USD/barrel
    pred_prices = model.predict_prices(test_batch)
    assert isinstance(pred_prices, np.ndarray)
    assert pred_prices.shape == (len(test_batch),)
    assert (pred_prices > 0).all()

    # Verify reconstruction relation: pred_price = origin_price * (1 + rel_pred)
    expected_prices = test_batch.origin_prices * (1.0 + rel_preds)
    np.testing.assert_allclose(pred_prices, expected_prices, rtol=1e-6)


def test_xgboost_feature_importance_export(sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    train_df, val_df, _ = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=1, scenario="multivariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=1, scenario="multivariate", target_representation="relative_change")

    model = XGBoostForecaster(n_estimators=30, max_depth=3, random_state=42)
    model.fit(train_batch, val_batch=val_batch)

    fi_df = model.get_feature_importance_df(horizon=1, scenario="multivariate")
    assert isinstance(fi_df, pd.DataFrame)
    assert len(fi_df) == 64
    assert set(fi_df.columns) >= {"feature_name", "importance_gain", "importance_weight", "horizon", "scenario"}
    assert (fi_df["importance_gain"] >= 0).all()


def test_xgboost_determinism_seed_42(sample_partitions: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    train_df, val_df, test_df = sample_partitions

    train_batch = build_supervised_samples(train_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")
    val_batch = build_supervised_samples(val_df, prior_df=train_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")
    test_batch = build_supervised_samples(test_df, prior_df=val_df, lookback=30, horizon=5, scenario="univariate", target_representation="relative_change")

    model1 = XGBoostForecaster(n_estimators=40, max_depth=3, random_state=42)
    model1.fit(train_batch, val_batch=val_batch)
    preds1 = model1.predict(test_batch)

    model2 = XGBoostForecaster(n_estimators=40, max_depth=3, random_state=42)
    model2.fit(train_batch, val_batch=val_batch)
    preds2 = model2.predict(test_batch)

    np.testing.assert_array_equal(preds1, preds2)
