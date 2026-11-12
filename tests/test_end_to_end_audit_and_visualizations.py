from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from experiments.benchmark import run_benchmark


def test_end_to_end_visualizations_and_manifest(tmp_path: Path) -> None:
    """Verify that benchmark runner produces all publication figures, runtime metrics, and manifest."""
    out_dir = tmp_path / "test_outputs"

    leaderboard = run_benchmark(
        models=["naive", "xgboost"],
        manifest_path="data/splits/splits_manifest.json",
        splits_dir="data/splits",
        output_dir=out_dir,
        config_path="configs/models.yaml",
        horizons=(1, 5),
        scenarios=("univariate", "multivariate"),
        target_representation="relative_change",
        include_price_level_ablation=False,
        xgb_n_estimators=5,
        xgb_early_stopping_rounds=2,
        seed=42,
    )

    # 1. Leaderboard & Runtimes
    assert not leaderboard.empty
    assert "runtime_seconds" in leaderboard.columns
    assert (leaderboard["runtime_seconds"] >= 0).all()
    assert leaderboard["runtime_seconds"].sum() > 0

    # 2. Predictions
    assert (out_dir / "predictions" / "predictions_h1.csv").exists()
    assert (out_dir / "predictions" / "predictions_h5.csv").exists()

    # 3. Publication Figures
    fig_h1 = out_dir / "figures" / "actual_vs_predicted_h1.png"
    fig_h5 = out_dir / "figures" / "actual_vs_predicted_h5.png"
    fig_cm = out_dir / "figures" / "directional_confusion_matrix.png"

    assert fig_h1.exists(), "actual_vs_predicted_h1.png must be generated"
    assert fig_h5.exists(), "actual_vs_predicted_h5.png must be generated"
    assert fig_cm.exists(), "directional_confusion_matrix.png must be generated"

    for fig_path in [fig_h1, fig_h5, fig_cm]:
        assert fig_path.stat().st_size > 1000
        with open(fig_path, "rb") as f:
            header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n"

    # 4. Manifest
    manifest_path = out_dir / "experiment_manifest.json"
    assert manifest_path.exists(), "experiment_manifest.json must be generated"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["seed"] == 42
    assert "data_checksums" in manifest
    assert "proxy_availability_flag_statistics" in manifest
    assert "canonical_panel" in manifest["proxy_availability_flag_statistics"]
    assert "pit_audit" in manifest
    assert manifest["pit_audit"]["passed"] is True
    assert "library_environment" in manifest
    assert "python_version" in manifest["library_environment"]
    assert "execution_runtimes" in manifest
    assert manifest["execution_runtimes"]["total_benchmark_runtime_seconds"] > 0
    assert len(manifest["execution_runtimes"]["configurations"]) == len(leaderboard)
