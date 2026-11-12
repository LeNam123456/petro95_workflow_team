"""Unit tests for Train-Only Scaler and Price Level Normalization Policy (Seam B).

Verifies:
1. Scaler statistics (mean, std) are fitted exclusively on Train data.
2. Modifying or evaluating on Test/Validation data does not alter Train-fitted scaler statistics (zero leakage).
3. Out-of-bounds values in Validation/Test are strictly never clipped or clamped.
4. Inverse transform reconstructs exact original physical values in USD/barrel.
5. Both 3D sequence tensors (LSTM) and 2D tabular matrices (XGBoost) are supported.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.data.dataset import SupervisedBatch
from src.data.scaling import PriceLevelScaler, TabularPriceLevelScaler


@pytest.fixture
def sample_batches() -> tuple[SupervisedBatch, SupervisedBatch]:
    """Create synthetic train and test batches with known price ranges."""
    rng = np.random.RandomState(42)

    # Train: 100 samples, lookback 30, 2 channels, prices around 80-100
    n_train = 100
    lookback = 30
    n_feats = 2
    train_feats = rng.uniform(80.0, 100.0, size=(n_train, lookback, n_feats))
    train_targets = rng.uniform(82.0, 102.0, size=(n_train,))
    train_origin = train_feats[:, -1, 0]
    train_actual = train_targets.copy()

    train_batch = SupervisedBatch(
        features=train_feats,
        targets=train_targets,
        origin_prices=train_origin,
        actual_prices=train_actual,
        forecast_origins=[f"2020-01-{i+1}" for i in range(n_train)],
        target_timestamps=[f"2020-01-{i+2}" for i in range(n_train)],
        feature_available_ats=[f"2020-01-{i+1}" for i in range(n_train)],
        horizon=1,
        scenario="multivariate",
        target_representation="price_level",
    )

    # Test: 20 samples with extreme out-of-bounds prices (e.g. 150-200, well above Train max 102)
    n_test = 20
    test_feats = rng.uniform(150.0, 200.0, size=(n_test, lookback, n_feats))
    test_targets = rng.uniform(155.0, 205.0, size=(n_test,))
    test_origin = test_feats[:, -1, 0]
    test_actual = test_targets.copy()

    test_batch = SupervisedBatch(
        features=test_feats,
        targets=test_targets,
        origin_prices=test_origin,
        actual_prices=test_actual,
        forecast_origins=[f"2024-01-{i+1}" for i in range(n_test)],
        target_timestamps=[f"2024-01-{i+2}" for i in range(n_test)],
        feature_available_ats=[f"2024-01-{i+1}" for i in range(n_test)],
        horizon=1,
        scenario="multivariate",
        target_representation="price_level",
    )

    return train_batch, test_batch


def test_scaler_fitted_exclusively_on_train(
    sample_batches: tuple[SupervisedBatch, SupervisedBatch]
) -> None:
    train_batch, _ = sample_batches
    scaler = PriceLevelScaler()
    assert not scaler.is_fitted_

    scaler.fit(train_batch)
    assert scaler.is_fitted_

    # Feature statistics should match train features
    expected_feat_mean = np.mean(train_batch.features, axis=(0, 1))
    expected_feat_std = np.std(train_batch.features, axis=(0, 1))
    np.testing.assert_allclose(scaler.feature_mean_, expected_feat_mean, rtol=1e-5)
    np.testing.assert_allclose(scaler.feature_std_, expected_feat_std, rtol=1e-5)

    # Target statistics should match train targets
    expected_target_mean = float(np.mean(train_batch.targets))
    expected_target_std = float(np.std(train_batch.targets))
    assert scaler.target_mean_ == pytest.approx(expected_target_mean)
    assert scaler.target_std_ == pytest.approx(expected_target_std)


def test_test_data_modification_does_not_alter_train_scaler(
    sample_batches: tuple[SupervisedBatch, SupervisedBatch]
) -> None:
    train_batch, test_batch = sample_batches
    scaler = PriceLevelScaler().fit(train_batch)

    # Snapshot train stats
    assert scaler.feature_mean_ is not None and scaler.feature_std_ is not None
    feat_mean_before = scaler.feature_mean_.copy()
    feat_std_before = scaler.feature_std_.copy()
    target_mean_before = scaler.target_mean_
    target_std_before = scaler.target_std_

    # Transform test batch
    _ = scaler.transform(test_batch)

    # Now mutate test batch with extreme spike values
    mutated_feats = test_batch.features * 100.0
    mutated_targets = test_batch.targets * 100.0
    mutated_batch = SupervisedBatch(
        features=mutated_feats,
        targets=mutated_targets,
        origin_prices=test_batch.origin_prices,
        actual_prices=test_batch.actual_prices,
        forecast_origins=test_batch.forecast_origins,
        target_timestamps=test_batch.target_timestamps,
        feature_available_ats=test_batch.feature_available_ats,
        horizon=test_batch.horizon,
        scenario=test_batch.scenario,
        target_representation=test_batch.target_representation,
    )
    _ = scaler.transform(mutated_batch)

    # Scaler stats MUST be completely unchanged
    np.testing.assert_array_equal(scaler.feature_mean_, feat_mean_before)
    np.testing.assert_array_equal(scaler.feature_std_, feat_std_before)
    assert scaler.target_mean_ == target_mean_before
    assert scaler.target_std_ == target_std_before


def test_out_of_range_values_never_clipped(
    sample_batches: tuple[SupervisedBatch, SupervisedBatch]
) -> None:
    train_batch, test_batch = sample_batches
    scaler = PriceLevelScaler().fit(train_batch)

    # Transform test data which has prices 150-205, well above train max ~102
    scaled_test = scaler.transform(test_batch)

    # Because test prices are much higher than train, scaled values must be > 0 and unclipped
    assert np.all(scaled_test.features > 2.0)
    assert np.all(scaled_test.targets > 2.0)

    # Reconstruct via inverse transform
    reconstructed_targets = scaler.inverse_transform_targets(scaled_test.targets)
    np.testing.assert_allclose(reconstructed_targets, test_batch.targets, rtol=1e-5)

    reconstructed_feats = scaler.inverse_transform_features(scaled_test.features)
    np.testing.assert_allclose(reconstructed_feats, test_batch.features, rtol=1e-5)


def test_tabular_scaler_train_only_and_unclipped() -> None:
    rng = np.random.RandomState(42)
    X_train = rng.uniform(80.0, 100.0, size=(100, 32))
    y_train = rng.uniform(82.0, 102.0, size=(100,))

    X_test = rng.uniform(150.0, 200.0, size=(20, 32))
    y_test = rng.uniform(155.0, 205.0, size=(20,))

    scaler = TabularPriceLevelScaler().fit(X_train, y_train)

    X_test_scaled = scaler.transform_features(X_test)
    y_test_scaled = scaler.transform_targets(y_test)

    # Verify no clipping (values > 2.0)
    assert np.all(X_test_scaled > 2.0)
    assert np.all(y_test_scaled > 2.0)

    # Inverse transform
    y_rec = scaler.inverse_transform_targets(y_test_scaled)
    np.testing.assert_allclose(y_rec, y_test, rtol=1e-5)

    X_rec = scaler.inverse_transform_features(X_test_scaled)
    np.testing.assert_allclose(X_rec, X_test, rtol=1e-5)


def test_scaler_to_and_from_dict(
    sample_batches: tuple[SupervisedBatch, SupervisedBatch]
) -> None:
    train_batch, test_batch = sample_batches
    scaler = PriceLevelScaler().fit(train_batch)

    scaler_dict = scaler.to_dict()
    assert scaler_dict["is_fitted"] is True
    assert scaler_dict["target_mean"] is not None

    restored = PriceLevelScaler.from_dict(scaler_dict)
    assert restored.is_fitted_ is True
    assert restored.feature_mean_ is not None and scaler.feature_mean_ is not None
    np.testing.assert_allclose(restored.feature_mean_, scaler.feature_mean_)
    assert restored.target_mean_ == scaler.target_mean_
    assert restored.target_std_ == scaler.target_std_

    # Verify identical transformation
    out_orig = scaler.transform(test_batch)
    out_restored = restored.transform(test_batch)
    np.testing.assert_allclose(out_orig.features, out_restored.features)
    np.testing.assert_allclose(out_orig.targets, out_restored.targets)

