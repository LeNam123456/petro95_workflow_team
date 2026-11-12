from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from experiments.benchmark import run_naive_benchmark


def test_end_to_end_naive_walking_skeleton(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    leaderboard_df = run_naive_benchmark(
        manifest_path=Path("data/splits/splits_manifest.json"),
        splits_dir=Path("data/splits"),
        output_dir=output_dir,
        horizons=(1, 5, 21),
    )

    # 1. Leaderboard has exactly 3 rows
    assert len(leaderboard_df) == 3
    assert list(leaderboard_df["horizon"]) == [1, 5, 21]
    assert list(leaderboard_df["n_samples"]) == [664, 660, 644]
    assert list(leaderboard_df["model"]) == ["Naive", "Naive", "Naive"]

    # 2. Check leaderboard file written to disk
    leaderboard_csv = output_dir / "benchmark_leaderboard.csv"
    assert leaderboard_csv.exists()
    disk_df = pd.read_csv(leaderboard_csv)
    assert len(disk_df) == 3

    # 3. Check predictions files written to disk
    preds_dir = output_dir / "predictions"
    assert (preds_dir / "predictions_h1.csv").exists()
    assert (preds_dir / "predictions_h5.csv").exists()
    assert (preds_dir / "predictions_h21.csv").exists()

    df_h1 = pd.read_csv(preds_dir / "predictions_h1.csv")
    assert len(df_h1) == 664
    assert "forecast_origin" in df_h1.columns
    assert "target_timestamp" in df_h1.columns
    assert "actual_price" in df_h1.columns
    assert "predicted_price" in df_h1.columns

    df_h5 = pd.read_csv(preds_dir / "predictions_h5.csv")
    assert len(df_h5) == 660

    df_h21 = pd.read_csv(preds_dir / "predictions_h21.csv")
    assert len(df_h21) == 644

    # 4. Check audit manifest exists and passes PIT audit
    manifest_file = output_dir / "audit_manifest.json"
    assert manifest_file.exists()
    audit_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert audit_data["pit_audit"]["passed"] is True
    assert audit_data["splits_integrity"]["all_valid"] is True
