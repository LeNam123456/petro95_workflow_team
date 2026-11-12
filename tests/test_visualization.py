from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.evaluation.visualization import (
    compute_directional_confusion_matrix,
    plot_actual_vs_predicted,
    plot_directional_confusion_matrices,
    plot_loss_curves,
)


def test_compute_directional_confusion_matrix_binary_counts() -> None:
    # 5 samples:
    # 1. origin=100, act=105 (Up), pred=103 (Up) -> TP
    # 2. origin=100, act=105 (Up), pred=95 (Down) -> FN
    # 3. origin=100, act=95 (Down), pred=102 (Up) -> FP
    # 4. origin=100, act=95 (Down), pred=90 (Down) -> TN
    # 5. origin=100, act=102 (Up), pred=104 (Up) -> TP
    origin = np.array([100.0, 100.0, 100.0, 100.0, 100.0])
    actual = np.array([105.0, 105.0, 95.0, 95.0, 102.0])
    pred = np.array([103.0, 95.0, 102.0, 90.0, 104.0])

    cm_info = compute_directional_confusion_matrix(
        actual_prices=actual,
        predicted_prices=pred,
        origin_prices=origin,
        binary_mode=True,
    )

    assert cm_info["tp"] == 2
    assert cm_info["fn"] == 1
    assert cm_info["fp"] == 1
    assert cm_info["tn"] == 1
    assert cm_info["total"] == 5
    # Accuracy: (2 + 1) / 5 = 60.0%
    assert pytest.approx(cm_info["accuracy"]) == 60.0
    # Up Recall (Sensitivity): TP / (TP + FN) = 2 / 3 = 66.67%
    assert pytest.approx(cm_info["sensitivity_up"]) == (2 / 3) * 100.0
    # Down Recall (Specificity): TN / (TN + FP) = 1 / 2 = 50.0%
    assert pytest.approx(cm_info["specificity_down"]) == 50.0
    # Precision Up: TP / (TP + FP) = 2 / 3
    assert pytest.approx(cm_info["precision_up"]) == (2 / 3) * 100.0
    # Precision Down: TN / (TN + FN) = 1 / 2
    assert pytest.approx(cm_info["precision_down"]) == 50.0


def test_plot_actual_vs_predicted_generates_valid_png(tmp_path: Path) -> None:
    dates = pd.date_range("2024-01-01", periods=10, freq="B", tz="UTC")
    origin_prices = np.linspace(80.0, 85.0, 10)
    actual_prices = origin_prices + np.array([0.5, -0.2, 0.8, -0.4, 0.3, -0.1, 0.6, -0.5, 0.2, 0.4])

    rows = []
    for model_name in ["Naive", "XGBoost", "LSTM"]:
        scenario = "multivariate" if model_name != "Naive" else "univariate"
        pred = actual_prices + (0.1 if model_name == "LSTM" else -0.1)
        for d, orig, act, p in zip(dates, origin_prices, actual_prices, pred):
            rows.append({
                "target_timestamp": d,
                "horizon": 1,
                "model": model_name,
                "scenario": scenario,
                "target_representation": "relative_change",
                "origin_price": orig,
                "actual_price": act,
                "predicted_price": p,
                "error": p - act,
            })
    pred_df = pd.DataFrame(rows)

    out_file = tmp_path / "actual_vs_predicted_h1.png"
    result_path = plot_actual_vs_predicted(pred_df, horizon=1, output_path=out_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 1000
    # Verify PNG header bytes
    with open(result_path, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n"


def test_plot_directional_confusion_matrices_generates_valid_png(tmp_path: Path) -> None:
    horizons = [1, 5, 21]
    preds_by_h: dict[int, pd.DataFrame] = {}

    for h in horizons:
        dates = pd.date_range("2024-01-01", periods=20, freq="B", tz="UTC")
        origin_prices = np.linspace(80.0, 90.0, 20)
        actual_prices = origin_prices + np.random.RandomState(42).normal(0, 1.0, 20)
        rows = []
        for model_name in ["XGBoost", "LSTM", "GRU"]:
            pred = origin_prices + np.random.RandomState(42 + h).normal(0, 1.0, 20)
            for d, orig, act, p in zip(dates, origin_prices, actual_prices, pred):
                rows.append({
                    "target_timestamp": d,
                    "horizon": h,
                    "model": model_name,
                    "scenario": "multivariate",
                    "target_representation": "relative_change",
                    "origin_price": orig,
                    "actual_price": act,
                    "predicted_price": p,
                    "error": p - act,
                })
        preds_by_h[h] = pd.DataFrame(rows)

    out_file = tmp_path / "directional_confusion_matrix.png"
    result_path = plot_directional_confusion_matrices(preds_by_h, output_path=out_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 1000
    with open(result_path, "rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n"
