from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.dataset import (
    SupervisedBatch,
    build_supervised_samples,
)


@pytest.fixture
def split_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    splits_dir = Path("data/splits")
    train = pd.read_parquet(splits_dir / "train_2008_2020.parquet")
    val = pd.read_parquet(splits_dir / "val_2021_2023.parquet")
    test = pd.read_parquet(splits_dir / "test_2024_2025.parquet")
    return train, val, test


def test_exact_test_sample_counts(split_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    _, val, test = split_data
    # Required exact counts on Test: 664 for h=1, 660 for h=5, 644 for h=21
    batch_h1 = build_supervised_samples(test, prior_df=val, lookback=30, horizon=1)
    assert len(batch_h1) == 664
    assert batch_h1.features.shape[0] == 664
    assert batch_h1.targets.shape[0] == 664

    batch_h5 = build_supervised_samples(test, prior_df=val, lookback=30, horizon=5)
    assert len(batch_h5) == 660

    batch_h21 = build_supervised_samples(test, prior_df=val, lookback=30, horizon=21)
    assert len(batch_h21) == 644


def test_context_borrowing_early_samples(split_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    _, val, test = split_data
    batch = build_supervised_samples(test, prior_df=val, lookback=30, horizon=1, scenario="univariate", target_representation="price_level")

    # Sample 0 in test set:
    # Lookback window has 30 rows.
    # The last row of sample 0 window should be row 0 of test: test.iloc[0]['MG95']
    # The first row of sample 0 window should be row -29 of val: val.iloc[-29]['MG95']
    window_0 = batch.features[0]
    expected_first = val.iloc[-29]["MG95"]
    expected_last = test.iloc[0]["MG95"]

    assert pytest.approx(window_0[0, 0]) == expected_first
    assert pytest.approx(window_0[-1, 0]) == expected_last


def test_relative_change_normalization(split_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    _, val, test = split_data
    batch = build_supervised_samples(
        test,
        prior_df=val,
        lookback=30,
        horizon=1,
        scenario="univariate",
        target_representation="relative_change",
    )
    # Under relative change:
    # z_k = P_{o-k}/P_o - 1
    # At the forecast origin (last timestep of window, index -1):
    # z = P_o / P_o - 1 = 0.0
    for i in range(10):
        assert pytest.approx(batch.features[i, -1, 0]) == 0.0

    # Target is (P_{o+h} - P_o) / P_o
    expected_target_0 = (test.iloc[1]["MG95"] - test.iloc[0]["MG95"]) / test.iloc[0]["MG95"]
    assert pytest.approx(batch.targets[0]) == expected_target_0
    assert pytest.approx(batch.origin_prices[0]) == test.iloc[0]["MG95"]
    assert pytest.approx(batch.actual_prices[0]) == test.iloc[1]["MG95"]


def test_multivariate_shape(split_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    _, val, test = split_data
    batch_multi = build_supervised_samples(test, prior_df=val, lookback=30, horizon=5, scenario="multivariate")
    assert batch_multi.features.shape == (660, 30, 2)
