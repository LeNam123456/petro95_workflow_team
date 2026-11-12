from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.dataset import build_supervised_samples
from src.models.baseline import NaivePersistenceModel


@pytest.fixture
def split_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    splits_dir = Path("data/splits")
    val = pd.read_parquet(splits_dir / "val_2021_2023.parquet")
    test = pd.read_parquet(splits_dir / "test_2024_2025.parquet")
    return val, test


def test_naive_persistence_predict_relative_change(split_data: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    val, test = split_data
    batch = build_supervised_samples(test, prior_df=val, lookback=30, horizon=1, target_representation="relative_change")
    model = NaivePersistenceModel()
    preds = model.predict(batch)
    # Under relative change, naive predicts 0.0 change
    np.testing.assert_array_equal(preds, np.zeros(len(batch)))

    pred_prices = model.predict_prices(batch)
    # Price level is origin price * (1 + 0) = origin price
    np.testing.assert_array_equal(pred_prices, batch.origin_prices)


def test_naive_persistence_predict_price_level(split_data: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    val, test = split_data
    batch = build_supervised_samples(test, prior_df=val, lookback=30, horizon=5, target_representation="price_level")
    model = NaivePersistenceModel()
    pred_prices = model.predict_prices(batch)
    np.testing.assert_array_equal(pred_prices, batch.origin_prices)
