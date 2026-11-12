from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.metrics import (
    compute_directional_accuracy,
    compute_metrics,
    three_state_sign,
)
from src.evaluation.reconstruction import reconstruct_price


def test_three_state_sign() -> None:
    values = np.array([-5.0, -0.0001, 0.0, 0.0001, 12.5])
    signs = three_state_sign(values)
    np.testing.assert_array_equal(signs, np.array([-1, -1, 0, 1, 1]))


def test_directional_accuracy_3_state() -> None:
    # origin: 100
    # actual: 105 (up), 95 (down), 100 (flat), 102 (up)
    # pred:   103 (up), 90 (down), 100 (flat),  98 (down)
    # Signs actual: [+1, -1,  0, +1]
    # Signs pred:   [+1, -1,  0, -1]
    # Matches:       [True, True, True, False] -> 3/4 = 75.0%
    origin = np.array([100.0, 100.0, 100.0, 100.0])
    actual = np.array([105.0, 95.0, 100.0, 102.0])
    pred = np.array([103.0, 90.0, 100.0, 98.0])

    da_info = compute_directional_accuracy(actual, pred, origin)
    assert pytest.approx(da_info["directional_accuracy"]) == 75.0
    assert pytest.approx(da_info["up_pct"]) == 50.0
    assert pytest.approx(da_info["down_pct"]) == 25.0
    assert pytest.approx(da_info["flat_pct"]) == 25.0
    assert pytest.approx(da_info["majority_class_baseline"]) == 50.0


def test_directional_accuracy_naive_rule() -> None:
    # Naive persistence: pred == origin (pred delta is always 0)
    # It is ONLY correct when actual delta == 0
    origin = np.array([100.0, 100.0, 100.0, 100.0])
    actual = np.array([105.0, 95.0, 100.0, 102.0]) # 1 flat out of 4
    pred = origin.copy()

    da_info = compute_directional_accuracy(actual, pred, origin)
    assert pytest.approx(da_info["directional_accuracy"]) == 25.0


def test_compute_metrics_exact() -> None:
    origin = np.array([100.0, 100.0, 100.0, 100.0])
    actual = np.array([100.0, 105.0, 95.0, 100.0])
    pred = np.array([100.0, 103.0, 97.0, 102.0])
    # errors: pred - actual = [0, -2, +2, +2]
    # abs errors: [0, 2, 2, 2] -> MAE = 6 / 4 = 1.5
    # sq errors: [0, 4, 4, 4] -> MSE = 12 / 4 = 3.0, RMSE = sqrt(3) ~ 1.73205
    # mape: [0, 2/105, 2/95, 2/100] * 100 / 4

    metrics = compute_metrics(actual, pred, origin)
    assert pytest.approx(metrics["mae"]) == 1.5
    assert pytest.approx(metrics["mse"]) == 3.0
    assert pytest.approx(metrics["rmse"]) == np.sqrt(3.0)
    assert "r2" in metrics
    assert "directional_accuracy" in metrics
    assert metrics["n_samples"] == 4


def test_reconstruct_price_relative_change() -> None:
    origin = np.array([100.0, 80.0])
    rel_change = np.array([0.05, -0.10])
    # 100 * (1 + 0.05) = 105.0
    # 80 * (1 - 0.10) = 72.0
    reconstructed = reconstruct_price(origin, rel_change)
    np.testing.assert_allclose(reconstructed, np.array([105.0, 72.0]))
