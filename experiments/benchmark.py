"""Benchmark orchestrator for the walking skeleton pipeline.

Executes:
1. Integrity verification and PIT audit.
2. Naive persistence baseline across horizons h in {1, 5, 21}.
3. Generation of per-horizon prediction files, benchmark leaderboard, and audit manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd

from src.data.dataset import build_supervised_samples
from src.data.validation import audit_point_in_time, verify_splits_integrity
from src.evaluation.metrics import compute_metrics
from src.models.baseline import NaivePersistenceModel


def run_naive_benchmark(
    manifest_path: str | Path = "data/splits/splits_manifest.json",
    splits_dir: str | Path = "data/splits",
    output_dir: str | Path = "outputs",
    horizons: tuple[int, ...] = (1, 5, 21),
    lookback: int = 30,
    scenario: str = "univariate",
    target_representation: str = "relative_change",
) -> pd.DataFrame:
    """Execute the Naive baseline benchmark pipeline across horizons."""
    m_path = Path(manifest_path)
    s_dir = Path(splits_dir)
    out_dir = Path(output_dir)
    preds_dir = out_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify split integrity
    integrity_report = verify_splits_integrity(m_path, raise_on_error=True)

    # 2. Load splits in read-only mode
    val_df = pd.read_parquet(s_dir / "val_2021_2023.parquet")
    test_df = pd.read_parquet(s_dir / "test_2024_2025.parquet")

    # 3. Audit PIT governance
    manifest_data = json.loads(m_path.read_text(encoding="utf-8"))
    canonical_source = manifest_data.get("dataset_source", "data/interim/canonical_market_panel.parquet")
    canonical_path = Path(canonical_source)
    if not canonical_path.is_absolute():
        canonical_path = m_path.parent.parent.parent / canonical_source
    canonical_df = pd.read_parquet(canonical_path)
    pit_report = audit_point_in_time(canonical_df, horizons=horizons, raise_on_error=True)

    leaderboard_rows: list[dict[str, Any]] = []

    # 4. Iterate over horizons
    for h in horizons:
        batch = build_supervised_samples(
            partition_df=test_df,
            prior_df=val_df,
            lookback=lookback,
            horizon=h,
            scenario=scenario,
            target_representation=target_representation,
        )

        model = NaivePersistenceModel()
        pred_prices = model.predict_prices(batch)

        metrics = compute_metrics(
            actual_prices=batch.actual_prices,
            predicted_prices=pred_prices,
            origin_prices=batch.origin_prices,
        )

        # Build prediction file
        pred_df = pd.DataFrame({
            "forecast_origin": batch.forecast_origins,
            "feature_available_at": batch.feature_available_ats,
            "target_timestamp": batch.target_timestamps,
            "horizon": h,
            "model": "Naive",
            "scenario": scenario,
            "target_representation": target_representation,
            "origin_price": batch.origin_prices,
            "actual_price": batch.actual_prices,
            "predicted_price": pred_prices,
            "error": pred_prices - batch.actual_prices,
        })
        pred_csv_path = preds_dir / f"predictions_h{h}.csv"
        pred_df.to_csv(pred_csv_path, index=False)

        leaderboard_entry = {
            "model": "Naive",
            "scenario": scenario,
            "target_representation": target_representation,
            "horizon": h,
            **metrics,
        }
        leaderboard_rows.append(leaderboard_entry)

    leaderboard_df = pd.DataFrame(leaderboard_rows)
    leaderboard_path = out_dir / "benchmark_leaderboard.csv"
    leaderboard_df.to_csv(leaderboard_path, index=False)

    # 5. Save audit manifest
    audit_manifest = {
        "pipeline": "Mogas 95 Walking Skeleton Pipeline",
        "benchmark_stage": "Stage 3 - Naive Persistence Baseline",
        "splits_integrity": integrity_report,
        "pit_audit": pit_report.to_dict(),
        "horizons_evaluated": list(horizons),
        "test_sample_counts": {f"h{h}": int(leaderboard_df.loc[leaderboard_df['horizon'] == h, 'n_samples'].iloc[0]) for h in horizons},
    }
    manifest_out_path = out_dir / "audit_manifest.json"
    manifest_out_path.write_text(json.dumps(audit_manifest, indent=2, default=str), encoding="utf-8")

    return leaderboard_df
