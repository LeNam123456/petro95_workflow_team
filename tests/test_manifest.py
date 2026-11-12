from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.manifest import (
    build_experiment_manifest,
    compute_proxy_flag_statistics,
    get_library_environment,
    save_experiment_manifest,
)


def test_get_library_environment() -> None:
    env_info = get_library_environment()
    assert "python_version" in env_info
    assert "os" in env_info
    assert "libraries" in env_info
    libs = env_info["libraries"]
    assert "numpy" in libs
    assert "pandas" in libs
    assert "torch" in libs
    assert "xgboost" in libs
    assert "matplotlib" in libs


def test_compute_proxy_flag_statistics() -> None:
    df = pd.DataFrame({
        "publication_datetime_is_proxy": [True, True, False, True],
        "availability_datetime_is_proxy": [True, True, True, True],
        "brent_availability_datetime_is_proxy": [False, False, True, False],
        "brent_calendar_exact_match": [True, True, True, False],
    })
    stats = compute_proxy_flag_statistics(df)

    assert "canonical_panel" in stats
    panel_stats = stats["canonical_panel"]

    assert panel_stats["publication_datetime_is_proxy"]["true_count"] == 3
    assert panel_stats["publication_datetime_is_proxy"]["false_count"] == 1
    assert pytest.approx(panel_stats["publication_datetime_is_proxy"]["true_pct"]) == 75.0

    assert panel_stats["availability_datetime_is_proxy"]["true_count"] == 4
    assert panel_stats["availability_datetime_is_proxy"]["false_count"] == 0

    assert panel_stats["brent_calendar_exact_match"]["true_count"] == 3
    assert panel_stats["brent_calendar_exact_match"]["false_count"] == 1


def test_build_and_save_experiment_manifest(tmp_path: Path) -> None:
    canonical_df = pd.DataFrame({
        "publication_datetime_is_proxy": [True, True],
        "availability_datetime_is_proxy": [True, True],
        "brent_availability_datetime_is_proxy": [True, True],
        "brent_calendar_exact_match": [True, True],
    })

    leaderboard_df = pd.DataFrame([
        {
            "model": "Naive",
            "scenario": "univariate",
            "target_representation": "relative_change",
            "horizon": 1,
            "mae": 1.25,
            "runtime_seconds": 0.05,
        },
        {
            "model": "XGBoost",
            "scenario": "multivariate",
            "target_representation": "relative_change",
            "horizon": 1,
            "mae": 1.10,
            "runtime_seconds": 0.42,
        },
    ])

    manifest = build_experiment_manifest(
        benchmark_stage="Stage 7 - Visualization Suite, Experiment Manifest & Audit",
        seed=42,
        models_evaluated=["naive", "xgboost"],
        target_representations_evaluated=["relative_change"],
        horizons_evaluated=[1],
        splits_manifest_path="data/splits/splits_manifest.json",
        canonical_df=canonical_df,
        pit_audit_report={"passed": True, "total_rows": 2, "feature_violations": 0, "target_violations": 0},
        splits_integrity={"all_valid": True},
        hyperparameters={"xgboost": {"max_depth": 4}},
        leaderboard_df=leaderboard_df,
        saved_checkpoints=[],
        total_runtime_seconds=1.23,
    )

    assert manifest["pipeline"] == "Pipeline Du bao Diem & Chieu huong Xang Platts Singapore Mogas 95"
    assert manifest["seed"] == 42
    assert "data_checksums" in manifest
    assert "proxy_availability_flag_statistics" in manifest
    assert "pit_audit" in manifest
    assert "hyperparameters" in manifest
    assert "library_environment" in manifest
    assert "execution_runtimes" in manifest
    assert manifest["execution_runtimes"]["total_benchmark_runtime_seconds"] == 1.23
    assert len(manifest["execution_runtimes"]["configurations"]) == 2

    out_file = tmp_path / "experiment_manifest.json"
    save_experiment_manifest(manifest, out_file)
    assert out_file.exists()

    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["seed"] == 42
    assert loaded["execution_runtimes"]["total_benchmark_runtime_seconds"] == 1.23
