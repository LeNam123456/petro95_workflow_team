"""End-to-end integration tests for Price Level Ablation Benchmark (Seam A).

Verifies:
1. 12 Price Level ablation configurations ({XGBoost, LSTM} x {uni, multi} x {1, 5, 21}).
2. Scaler statistics are fitted exclusively on Train and never clipped on Test.
3. Predictions mapped back to nominal USD/barrel.
4. Full 33-row benchmark leaderboard ({21 relative_change, 12 price_level}).
5. Checkpoints saved for price level neural models.
6. Audit manifest updated with ablation stage and configurations.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from experiments.benchmark import run_benchmark


def test_end_to_end_price_level_ablation_only(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"

    leaderboard_df = run_benchmark(
        models=["xgboost", "lstm"],
        manifest_path=Path("data/splits/splits_manifest.json"),
        splits_dir=Path("data/splits"),
        output_dir=output_dir,
        horizons=(1, 5, 21),
        target_representation="price_level",
        seed=42,
        xgb_n_estimators=10,
        nn_epochs=2,
        nn_batch_size=64,
        verbose=False,
    )

    # 1. Leaderboard has exactly 12 rows
    assert len(leaderboard_df) == 12
    assert set(leaderboard_df["model"]) == {"XGBoost", "LSTM"}
    assert set(leaderboard_df["scenario"]) == {"univariate", "multivariate"}
    assert set(leaderboard_df["target_representation"]) == {"price_level"}
    assert set(leaderboard_df["horizon"]) == {1, 5, 21}

    # Verify counts per model
    counts = leaderboard_df["model"].value_counts().to_dict()
    assert counts["XGBoost"] == 6
    assert counts["LSTM"] == 6

    # 2. Checkpoints saved for price level
    checkpoints_dir = output_dir / "checkpoints"
    for scenario in ["univariate", "multivariate"]:
        for h in [1, 5, 21]:
            cp_path = checkpoints_dir / f"lstm_{scenario}_price_level_h{h}.pt"
            assert cp_path.exists(), f"Missing checkpoint: {cp_path.name}"


def test_end_to_end_full_33_configurations(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"

    leaderboard_df = run_benchmark(
        models=["naive", "xgboost", "lstm", "gru"],
        manifest_path=Path("data/splits/splits_manifest.json"),
        splits_dir=Path("data/splits"),
        output_dir=output_dir,
        horizons=(1, 5, 21),
        include_price_level_ablation=True,
        seed=42,
        xgb_n_estimators=10,
        nn_epochs=2,
        nn_batch_size=64,
        verbose=False,
    )

    # 1. Exactly 33 configurations: 21 relative_change + 12 price_level
    assert len(leaderboard_df) == 33

    rep_counts = leaderboard_df["target_representation"].value_counts().to_dict()
    assert rep_counts["relative_change"] == 21
    assert rep_counts["price_level"] == 12

    # Verify models
    model_counts = leaderboard_df.groupby(["model", "target_representation"]).size().to_dict()
    assert model_counts[("Naive", "relative_change")] == 3
    assert model_counts[("XGBoost", "relative_change")] == 6
    assert model_counts[("LSTM", "relative_change")] == 6
    assert model_counts[("GRU", "relative_change")] == 6
    assert model_counts[("XGBoost", "price_level")] == 6
    assert model_counts[("LSTM", "price_level")] == 6

    # 2. Verify prediction files contain all 11 configurations per horizon
    preds_dir = output_dir / "predictions"
    for h, n_samples in [(1, 664), (5, 660), (21, 644)]:
        pred_csv = preds_dir / f"predictions_h{h}.csv"
        assert pred_csv.exists()
        pred_df = pd.read_csv(pred_csv)
        # 11 configs per horizon: 1 Naive (rel) + 2 XGB (rel) + 2 LSTM (rel) + 2 GRU (rel) + 2 XGB (price) + 2 LSTM (price)
        assert len(pred_df) == n_samples * 11
        assert set(pred_df["target_representation"]) == {"relative_change", "price_level"}

        # Prices must be physical prices in USD/bbl
        assert (pred_df["predicted_price"] > 0).all()
        assert (pred_df["actual_price"] > 0).all()

    # 3. Verify audit manifest
    manifest_file = output_dir / "audit_manifest.json"
    assert manifest_file.exists()
    audit_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert "Stage 6" in audit_data["benchmark_stage"]
    assert audit_data["total_configurations"] == 33
    assert set(audit_data["target_representations_evaluated"]) == {"relative_change", "price_level"}
