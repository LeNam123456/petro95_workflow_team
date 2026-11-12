"""Tests for tabular feature engineering (Seam C).

Verifies:
1. Exact 32 features for Univariate (30 locally normalized relative lags + R1, R5).
2. Exact 64 features for Multivariate (32 Mogas + 32 Brent features).
3. Zero raw price spread (P^M - P^B) in feature set.
4. Exact numerical values of relative lags and momentum returns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data.dataset import build_supervised_samples
from src.features.engineering import extract_xgboost_features, get_feature_names


@pytest.fixture
def sample_market_df() -> pd.DataFrame:
    """Create a synthetic market DataFrame with known prices for 40 sessions."""
    dates = pd.date_range("2020-01-01", periods=40, freq="B")
    # Mogas prices: starting at 100, step +1 each day
    mg95 = np.linspace(100.0, 139.0, 40)
    # Brent prices: starting at 80, step +0.5 each day
    brent = np.linspace(80.0, 99.5, 40)

    df = pd.DataFrame({
        "observation_datetime": dates + pd.Timedelta(hours=16, minutes=30),
        "availability_datetime": dates + pd.Timedelta(hours=16, minutes=30),
        "target_market_date": dates,
        "forecast_origin_datetime": dates + pd.Timedelta(days=1, hours=8, minutes=30),
        "MG95": mg95,
        "brent_close": brent,
    })
    return df


def test_univariate_feature_shape_and_names(sample_market_df: pd.DataFrame) -> None:
    batch = build_supervised_samples(
        partition_df=sample_market_df,
        lookback=30,
        horizon=1,
        scenario="univariate",
        target_representation="relative_change",
    )
    features, names = extract_xgboost_features(batch)

    # 1. Exact 32 features
    assert features.shape == (len(batch), 32)
    assert len(names) == 32

    # 2. Check feature names
    expected_names = [f"mg95_lag_{k}" for k in range(30)] + ["mg95_r1", "mg95_r5"]
    assert names == expected_names


def test_multivariate_feature_shape_and_names(sample_market_df: pd.DataFrame) -> None:
    batch = build_supervised_samples(
        partition_df=sample_market_df,
        lookback=30,
        horizon=1,
        scenario="multivariate",
        target_representation="relative_change",
    )
    features, names = extract_xgboost_features(batch)

    # 1. Exact 64 features
    assert features.shape == (len(batch), 64)
    assert len(names) == 64

    # 2. Check feature names
    expected_names = (
        [f"mg95_lag_{k}" for k in range(30)]
        + ["mg95_r1", "mg95_r5"]
        + [f"brent_lag_{k}" for k in range(30)]
        + ["brent_r1", "brent_r5"]
    )
    assert names == expected_names


def test_feature_numerical_accuracy(sample_market_df: pd.DataFrame) -> None:
    batch = build_supervised_samples(
        partition_df=sample_market_df,
        lookback=30,
        horizon=1,
        scenario="univariate",
        target_representation="relative_change",
    )
    features, names = extract_xgboost_features(batch)

    # For the first sample (index 0):
    # Origin session is k = 29. MG95[29] = 129.0
    # Lag 0 is at origin: z_{o,0} = 129/129 - 1 = 0.0
    assert features[0, names.index("mg95_lag_0")] == pytest.approx(0.0)

    # Lag 1 is session 28: MG95[28] = 128.0. z_{o,1} = 128/129 - 1 = -1/129
    assert features[0, names.index("mg95_lag_1")] == pytest.approx(128.0 / 129.0 - 1.0)

    # Lag 29 is session 0: MG95[0] = 100.0. z_{o,29} = 100/129 - 1
    assert features[0, names.index("mg95_lag_29")] == pytest.approx(100.0 / 129.0 - 1.0)

    # R1 momentum: (P_o - P_{o-1}) / P_{o-1} = (129 - 128) / 128 = 1/128
    assert features[0, names.index("mg95_r1")] == pytest.approx(1.0 / 128.0)

    # R5 momentum: (P_o - P_{o-5}) / P_{o-5} = (129 - 124) / 124 = 5/124
    assert features[0, names.index("mg95_r5")] == pytest.approx(5.0 / 124.0)


def test_raw_price_spread_completely_excluded(sample_market_df: pd.DataFrame) -> None:
    batch = build_supervised_samples(
        partition_df=sample_market_df,
        lookback=30,
        horizon=1,
        scenario="multivariate",
        target_representation="relative_change",
    )
    _, names = extract_xgboost_features(batch)

    for name in names:
        assert "spread" not in name.lower()
        assert "crack" not in name.lower()
