"""End-to-end integration tests for XGBoost benchmark execution (Seam A).

Verifies:
1. 6 XGBoost configurations trained and evaluated on Test partition.
2. Leaderboard contains 9 rows (3 Naive + 6 XGBoost).
3. Predictions files updated with exact sample counts per horizon.
4. Feature importance exported to outputs/feature_importance.csv.
5. Audit manifest updated with XGBoost training metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from experiments.benchmark import run_benchmark


def test_end_to_end_xgboost_benchmark(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    leaderboard_df = run_benchmark(
        models=["naive", "xgboost"],
        manifest_path=Path("data/splits/splits_manifest.json"),
        splits_dir=Path("data/splits"),
        output_dir=output_dir,
        horizons=(1, 5, 21),
        seed=42,
        # Use smaller n_estimators for fast integration test
        xgb_n_estimators=20,
    )

    # 1. Leaderboard has exactly 9 rows (3 Naive + 6 XGBoost)
    assert len(leaderboard_df) == 9
    assert set(leaderboard_df["model"]) == {"Naive", "XGBoost"}
    assert set(leaderboard_df["scenario"]) == {"univariate", "multivariate"}
    assert set(leaderboard_df["target_representation"]) == {"relative_change"}
    assert set(leaderboard_df["horizon"]) == {1, 5, 21}

    # 2. Check leaderboard file on disk
    leaderboard_csv = output_dir / "benchmark_leaderboard.csv"
    assert leaderboard_csv.exists()
    disk_df = pd.read_csv(leaderboard_csv)
    assert len(disk_df) == 9

    # 3. Check predictions files
    preds_dir = output_dir / "predictions"
    for h, n_samples in [(1, 664), (5, 660), (21, 644)]:
        pred_csv = preds_dir / f"predictions_h{h}.csv"
        assert pred_csv.exists()
        df_h = pd.read_csv(pred_csv)
        # Should have 3 configurations per horizon: Naive (uni), XGBoost (uni), XGBoost (multi)
        assert len(df_h) == n_samples * 3
        assert set(df_h["model"]) == {"Naive", "XGBoost"}
        assert "actual_price" in df_h.columns
        assert "predicted_price" in df_h.columns

    # 4. Check feature importance file
    fi_csv = output_dir / "feature_importance.csv"
    assert fi_csv.exists()
    fi_df = pd.read_csv(fi_csv)
    # 6 XGBoost models: 3 uni (32 features each) + 3 multi (64 features each) = 3*32 + 3*64 = 288 rows
    assert len(fi_df) == 3 * 32 + 3 * 64
    assert set(fi_df["horizon"]) == {1, 5, 21}
    assert set(fi_df["scenario"]) == {"univariate", "multivariate"}

    # 5. Check audit manifest
    manifest_file = output_dir / "audit_manifest.json"
    assert manifest_file.exists()
    audit_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert "xgboost" in audit_data.get("models_evaluated", [])
    assert audit_data["pit_audit"]["passed"] is True
