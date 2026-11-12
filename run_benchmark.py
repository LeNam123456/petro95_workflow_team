"""Main entry point for running the forecasting benchmark pipeline.

Usage:
    python run_benchmark.py --model naive
    python run_benchmark.py --model xgboost
    python run_benchmark.py --model all
"""

from __future__ import annotations

import argparse
from pathlib import Path
from experiments.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Mogas 95 Forecasting Pipeline Benchmark Runner")
    parser.add_argument(
        "--model",
        type=str,
        default="all",
        choices=["naive", "xgboost", "all"],
        help="Forecasting model to benchmark: 'naive', 'xgboost', or 'all' (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for leaderboard, predictions, and manifest",
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        default=[1, 5, 21],
        help="Forecast horizons in trading sessions (default: 1 5 21)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    horizons = tuple(args.horizons)

    if args.model == "all":
        selected_models = ["naive", "xgboost"]
    else:
        selected_models = [args.model]

    print("=" * 80)
    print("MOGAS 95 FORECASTING BENCHMARK — EXECUTION")
    print(f"Models: {[m.upper() for m in selected_models]} | Horizons: {horizons} | Seed: {args.seed} | Output: {output_path}")
    print("=" * 80)

    leaderboard = run_benchmark(
        models=selected_models,
        manifest_path="data/splits/splits_manifest.json",
        splits_dir="data/splits",
        output_dir=output_path,
        config_path="configs/models.yaml",
        horizons=horizons,
        seed=args.seed,
    )

    print("\n>>> BENCHMARK LEADERBOARD RESULTS (USD/bbl & Directional %):")
    cols_to_print = [
        "model", "scenario", "horizon", "n_samples", "mae", "rmse", "mape", "r2",
        "directional_accuracy", "majority_class_baseline", "up_pct", "down_pct", "flat_pct",
    ]
    available_cols = [c for c in cols_to_print if c in leaderboard.columns]
    print(leaderboard[available_cols].to_string(index=False))
    print(f"\n[OK] Leaderboard written to: {output_path / 'benchmark_leaderboard.csv'}")
    print(f"[OK] Predictions written to: {output_path / 'predictions'}")
    if (output_path / "feature_importance.csv").exists():
        print(f"[OK] Feature importance written to: {output_path / 'feature_importance.csv'}")
    print(f"[OK] Audit manifest written to: {output_path / 'audit_manifest.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
