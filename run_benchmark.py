"""Main entry point for running the forecasting benchmark pipeline.

Usage:
    python run_benchmark.py --model naive
    python run_benchmark.py --model xgboost
    python run_benchmark.py --model lstm
    python run_benchmark.py --model gru
    python run_benchmark.py --model recurrent
    python run_benchmark.py --model all
    python run_benchmark.py --model recurrent --seeds 42,43,44
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from experiments.benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Mogas 95 Forecasting Pipeline Benchmark Runner")
    parser.add_argument(
        "--model",
        type=str,
        default="all",
        choices=["naive", "xgboost", "lstm", "gru", "recurrent", "all"],
        help="Forecasting model to benchmark: 'naive', 'xgboost', 'lstm', 'gru', 'recurrent', or 'all' (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for leaderboard, predictions, checkpoints, and manifest",
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
        help="Canonical random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Optional comma-separated list of seeds for sensitivity analysis (e.g. '42,43,44')",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Optional override for neural network training epochs",
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    horizons = tuple(args.horizons)

    if args.model == "all":
        selected_models = ["naive", "xgboost", "lstm", "gru"]
    elif args.model == "recurrent":
        selected_models = ["lstm", "gru"]
    else:
        selected_models = [args.model]

    # Parse seeds
    if args.seeds is not None:
        seed_list = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    else:
        seed_list = [args.seed]

    print("=" * 80)
    print("MOGAS 95 FORECASTING BENCHMARK — EXECUTION")
    print(f"Models: {[m.upper() for m in selected_models]} | Horizons: {horizons} | Seeds: {seed_list} | Output: {output_path}")
    print("=" * 80)

    all_leaderboards: list[pd.DataFrame] = []

    for current_seed in seed_list:
        if len(seed_list) > 1:
            print(f"\n--- Running benchmark with seed = {current_seed} ---")
            current_out_dir = output_path if current_seed == seed_list[0] else output_path / f"seed_{current_seed}"
        else:
            current_out_dir = output_path

        leaderboard = run_benchmark(
            models=selected_models,
            manifest_path="data/splits/splits_manifest.json",
            splits_dir="data/splits",
            output_dir=current_out_dir,
            config_path="configs/models.yaml",
            horizons=horizons,
            seed=current_seed,
            nn_epochs=args.epochs,
        )
        leaderboard["seed"] = current_seed
        all_leaderboards.append(leaderboard)

    combined_leaderboard = all_leaderboards[0]

    print("\n>>> BENCHMARK LEADERBOARD RESULTS (USD/bbl & Directional %):")
    cols_to_print = [
        "model", "scenario", "horizon", "n_samples", "mae", "rmse", "mape", "r2",
        "directional_accuracy", "majority_class_baseline", "up_pct", "down_pct", "flat_pct",
    ]
    available_cols = [c for c in cols_to_print if c in combined_leaderboard.columns]
    print(combined_leaderboard[available_cols].to_string(index=False))

    if len(seed_list) > 1:
        print("\n>>> MULTI-SEED SENSITIVITY SUMMARY (Mean +/- Std):")
        multi_df = pd.concat(all_leaderboards, ignore_index=True)
        summary = (
            multi_df.groupby(["model", "scenario", "horizon"])[["mae", "rmse", "mape", "r2", "directional_accuracy"]]
            .agg(["mean", "std"])
            .round(4)
        )
        print(summary.to_string())
        # Save sensitivity summary
        summary_path = output_path / "multi_seed_sensitivity.csv"
        summary.to_csv(summary_path)
        print(f"[OK] Multi-seed sensitivity summary written to: {summary_path}")

    print(f"\n[OK] Leaderboard written to: {output_path / 'benchmark_leaderboard.csv'}")
    print(f"[OK] Predictions written to: {output_path / 'predictions'}")
    if (output_path / "checkpoints").exists():
        print(f"[OK] Neural checkpoints written to: {output_path / 'checkpoints'}")
    if (output_path / "figures" / "loss_curves.png").exists():
        print(f"[OK] Loss curves written to: {output_path / 'figures' / 'loss_curves.png'}")
    if (output_path / "feature_importance.csv").exists():
        print(f"[OK] Feature importance written to: {output_path / 'feature_importance.csv'}")
    print(f"[OK] Audit manifest written to: {output_path / 'audit_manifest.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
