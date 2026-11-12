"""End-to-end integration tests for Sequence Deep Learning Benchmark (Seam A).

Verifies:
1. All 12 recurrent configurations (LSTM/GRU x uni/multi x h in {1, 5, 21}) trained and evaluated.
2. Leaderboard contains exactly 21 rows (3 Naive + 6 XGBoost + 12 Recurrent).
3. Prediction files updated with 7 configurations per horizon and verified sample counts.
4. Checkpoints saved for all 12 neural models in outputs/checkpoints/.
5. Training/validation loss curves generated in outputs/figures/loss_curves.png.
6. Audit manifest updated with neural training metadata and seed.
"""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from experiments.benchmark import run_benchmark


def test_end_to_end_recurrent_benchmark(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"

    leaderboard_df = run_benchmark(
        models=["naive", "xgboost", "lstm", "gru"],
        manifest_path=Path("data/splits/splits_manifest.json"),
        splits_dir=Path("data/splits"),
        output_dir=output_dir,
        horizons=(1, 5, 21),
        seed=42,
        xgb_n_estimators=10,
        nn_epochs=2,
        nn_batch_size=64,
        verbose=False,
    )

    # 1. Leaderboard has exactly 21 rows
    assert len(leaderboard_df) == 21
    assert set(leaderboard_df["model"]) == {"Naive", "XGBoost", "LSTM", "GRU"}
    assert set(leaderboard_df["scenario"]) == {"univariate", "multivariate"}
    assert set(leaderboard_df["target_representation"]) == {"relative_change"}
    assert set(leaderboard_df["horizon"]) == {1, 5, 21}

    # Verify counts per model
    model_counts = leaderboard_df["model"].value_counts().to_dict()
    assert model_counts["Naive"] == 3
    assert model_counts["XGBoost"] == 6
    assert model_counts["LSTM"] == 6
    assert model_counts["GRU"] == 6

    # 2. Check leaderboard file on disk
    leaderboard_csv = output_dir / "benchmark_leaderboard.csv"
    assert leaderboard_csv.exists()
    disk_df = pd.read_csv(leaderboard_csv)
    assert len(disk_df) == 21

    # 3. Check predictions files
    preds_dir = output_dir / "predictions"
    for h, n_samples in [(1, 664), (5, 660), (21, 644)]:
        pred_csv = preds_dir / f"predictions_h{h}.csv"
        assert pred_csv.exists()
        df_h = pd.read_csv(pred_csv)
        # 7 models per horizon: Naive (1), XGBoost uni/multi (2), LSTM uni/multi (2), GRU uni/multi (2)
        assert len(df_h) == n_samples * 7
        assert set(df_h["model"]) == {"Naive", "XGBoost", "LSTM", "GRU"}
        assert "actual_price" in df_h.columns
        assert "predicted_price" in df_h.columns
        assert not df_h["predicted_price"].isna().any()

    # 4. Checkpoints directory has 12 .pt files
    cp_dir = output_dir / "checkpoints"
    assert cp_dir.exists()
    pt_files = list(cp_dir.glob("*.pt"))
    assert len(pt_files) == 12

    # 5. Loss curves plot exists
    figures_dir = output_dir / "figures"
    assert (figures_dir / "loss_curves.png").exists()

    # 6. Audit manifest
    manifest_file = output_dir / "audit_manifest.json"
    assert manifest_file.exists()
    audit_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert set(audit_data.get("models_evaluated", [])) == {"naive", "xgboost", "lstm", "gru"}
    assert "lstm" in audit_data.get("hyperparameters", {})
    assert "gru" in audit_data.get("hyperparameters", {})
    assert audit_data["pit_audit"]["passed"] is True
