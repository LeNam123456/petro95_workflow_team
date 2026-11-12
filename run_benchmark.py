"""Main entry point for running the forecasting benchmark pipeline.

Usage:
    python run_benchmark.py --audit-only
    python run_benchmark.py --model naive
    python run_benchmark.py --model xgboost
    python run_benchmark.py --model lstm
    python run_benchmark.py --model gru
    python run_benchmark.py --model recurrent
    python run_benchmark.py --model all
    python run_benchmark.py --model recurrent --seeds 42,43,44
    python run_benchmark.py --export-only-plots
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd

from experiments.benchmark import run_benchmark
from src.data.validation import audit_point_in_time, verify_splits_integrity
from src.evaluation.visualization import (
    plot_actual_vs_predicted,
    plot_directional_confusion_matrices,
    plot_loss_curves,
)


def run_audit_mode(
    manifest_path: str | Path = "data/splits/splits_manifest.json",
    horizons: tuple[int, ...] = (1, 5, 21),
) -> int:
    """Execute standalone Point-in-Time and dataset integrity audit."""
    m_path = Path(manifest_path)
    print("=" * 80)
    print("POINT-IN-TIME (PIT) & SPLIT INTEGRITY AUDIT")
    print(f"Manifest: {m_path.resolve()}")
    print("=" * 80)

    if not m_path.exists():
        print(f"[ERROR] Splits manifest not found: {m_path}")
        return 1

    try:
        integrity_report = verify_splits_integrity(m_path, raise_on_error=True)
        print("[OK] Split files and canonical source checksum verification: PASSED")
    except Exception as e:
        print(f"[FAIL] Split integrity verification failed: {e}")
        return 1

    try:
        manifest_data = json.loads(m_path.read_text(encoding="utf-8"))
        canonical_source = manifest_data.get("dataset_source", "data/interim/canonical_market_panel.parquet")
        canonical_path = Path(canonical_source)
        if not canonical_path.is_absolute():
            canonical_path = m_path.parent.parent.parent / canonical_source
        canonical_df = pd.read_parquet(canonical_path)

        pit_report = audit_point_in_time(canonical_df, horizons=horizons, raise_on_error=True)
        print("[OK] Point-in-Time (PIT) Causal Ordering Audit: PASSED")
        print(f"     - Total rows audited: {pit_report.total_rows:,}")
        print(f"     - Feature timestamp violations: {pit_report.feature_violations}")
        print(f"     - Target timestamp violations: {pit_report.target_violations}")
        print(f"     - Zero Lookahead Bias Verified: {pit_report.passed}")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"[FAIL] PIT audit failed: {e}")
        return 1


def export_plots_from_existing_outputs(
    output_dir: str | Path,
    horizons: tuple[int, ...] = (1, 5, 21),
) -> int:
    """Generate publication figures from existing prediction files without retraining."""
    out_p = Path(output_dir)
    preds_dir = out_p / "predictions"
    figs_dir = out_p / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting publication figures from predictions in: {preds_dir}")
    preds_by_h: dict[int, pd.DataFrame] = {}

    for h in horizons:
        p_file = preds_dir / f"predictions_h{h}.csv"
        if p_file.exists():
            df_h = pd.read_csv(p_file)
            preds_by_h[h] = df_h
            fig_path = figs_dir / f"actual_vs_predicted_h{h}.png"
            plot_actual_vs_predicted(df_h, horizon=h, output_path=fig_path)
            print(f"[OK] Generated: {fig_path}")
        else:
            print(f"[WARN] Prediction file not found: {p_file}")

    if preds_by_h:
        cm_path = figs_dir / "directional_confusion_matrix.png"
        plot_directional_confusion_matrices(preds_by_h, output_path=cm_path)
        print(f"[OK] Generated: {cm_path}")

    # Loss history
    loss_hist_file = out_p / "loss_history.json"
    if loss_hist_file.exists():
        loss_histories = json.loads(loss_hist_file.read_text(encoding="utf-8"))
        lc_path = figs_dir / "loss_curves.png"
        plot_loss_curves(loss_histories, output_path=lc_path)
        print(f"[OK] Generated: {lc_path}")

    return 0


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
    parser.add_argument(
        "--include-ablation",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include 12 Price Level ablation models ({XGBoost, LSTM} x {uni, multi} x {1, 5, 21}) to complete all 33 MVP configurations (default: True)",
    )
    parser.add_argument(
        "--target-representation",
        type=str,
        default="relative_change",
        choices=["relative_change", "price_level", "all"],
        help="Target representation to evaluate: 'relative_change', 'price_level', or 'all' (default: relative_change)",
    )
    parser.add_argument(
        "--generate-plots",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate publication-ready figures in outputs/figures (default: True)",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        default=False,
        help="Execute dataset checksum and Point-in-Time (PIT) audit only and exit",
    )
    parser.add_argument(
        "--export-only-plots",
        action="store_true",
        default=False,
        help="Generate publication figures from existing prediction files without retraining models",
    )
    args = parser.parse_args()

    horizons = tuple(args.horizons)

    if args.audit_only:
        code = run_audit_mode(horizons=horizons)
        sys.exit(code)

    if args.export_only_plots:
        code = export_plots_from_existing_outputs(output_dir=args.output_dir, horizons=horizons)
        sys.exit(code)

    output_path = Path(args.output_dir)

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

    include_ablation = args.include_ablation or (args.target_representation == "all")

    print("=" * 80)
    print("MOGAS 95 FORECASTING BENCHMARK — EXECUTION")
    print(f"Models: {[m.upper() for m in selected_models]} | Horizons: {horizons} | Target Rep: {args.target_representation} | Ablation: {include_ablation} | Seeds: {seed_list} | Output: {output_path}")
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
            target_representation=args.target_representation,
            include_price_level_ablation=include_ablation,
            seed=current_seed,
            nn_epochs=args.epochs,
            generate_plots=args.generate_plots,
        )
        leaderboard["seed"] = current_seed
        all_leaderboards.append(leaderboard)

    combined_leaderboard = all_leaderboards[0]

    print("\n>>> BENCHMARK LEADERBOARD RESULTS (USD/bbl & Directional %):")
    cols_to_print = [
        "model", "scenario", "target_representation", "horizon", "n_samples", "mae", "rmse", "mape", "r2",
        "directional_accuracy", "majority_class_baseline", "up_pct", "down_pct", "flat_pct", "runtime_seconds",
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
        summary_path = output_path / "multi_seed_sensitivity.csv"
        summary.to_csv(summary_path)
        print(f"[OK] Multi-seed sensitivity summary written to: {summary_path}")

    print(f"\n[OK] Leaderboard written to: {output_path / 'benchmark_leaderboard.csv'}")
    print(f"[OK] Predictions written to: {output_path / 'predictions'}")
    if (output_path / "checkpoints").exists():
        print(f"[OK] Neural checkpoints written to: {output_path / 'checkpoints'}")
    if (output_path / "figures").exists():
        print(f"[OK] Publication figures written to: {output_path / 'figures'}")
    if (output_path / "feature_importance.csv").exists():
        print(f"[OK] Feature importance written to: {output_path / 'feature_importance.csv'}")
    print(f"[OK] Full experiment manifest written to: {output_path / 'experiment_manifest.json'}")
    print(f"[OK] Audit manifest written to: {output_path / 'audit_manifest.json'}")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
