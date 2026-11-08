"""CLI Runner for Machine Learning Models (M4 Technical LightGBM, M5 Economic LightGBM) in SPAFS V5.2.

Executes:
- Branch A: Full-sample model estimation, multi-seed ensemble aggregation,
  feature importance extraction (Gain & Split), and artifact persistence.
- Branch B: Expanding Walk-Forward 1-step-ahead validation generating true OOS predictions,
  regression metrics, directional metrics, pairwise statistical tests (Diebold-Mariano HLN 1997,
  Clark-West 2007), and cryptographic SHA-256 manifests.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_proccessing.model_schemas import extract_model_matrix
from src.models.base import BaseForecastingModel
from src.models.evaluation.forecast_tests import cw_test, dm_test, forecast_metrics
from src.models.ml.lgbm import EconomicLGBMModel, TechnicalLGBMModel
from src.models.persistence import ArtifactManager
from src.models.validation.walk_forward import run_walk_forward_evaluation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SPAFS_V5.2.MLRunner")


def _get_model_factory(model_id: str) -> tuple[Callable[[], BaseForecastingModel], str]:
    """Return model instantiation factory and description for given model ID."""
    if model_id == "M4":
        return lambda: TechnicalLGBMModel(), "Technical LightGBM (Momentum & Volatility)"
    elif model_id == "M5":
        return lambda: EconomicLGBMModel(), "Economic LightGBM (Refining Economics Benchmark)"
    else:
        raise ValueError(f"Unsupported ML model ID: {model_id}. Expected 'M4' or 'M5'.")


def run_stream2_ml_pipeline(
    models: list[str] | tuple[str, ...] = ("M4", "M5"),
    data_path: str = "data/processed/stream2_aligned_nlp_2017_2025.parquet",
    walk_forward: bool = True,
    initial_window: int = 1500,
    refit_every: int = 20,
    artifacts_dir: str = "artifacts",
) -> None:
    """Execute complete machine learning pipeline for Stream 2 models (M4, M5).

    Args:
        models: List of model IDs to execute (e.g. ['M4'], ['M5'], or ['M4', 'M5']).
        data_path: Path to Stream 2 Parquet dataset.
        walk_forward: If True, execute Branch B walk-forward out-of-sample evaluation.
        initial_window: Initial warmup observation count for expanding walk-forward.
        refit_every: Re-estimation frequency in trading days (20 = monthly refit).
        artifacts_dir: Target directory for artifacts.
    """
    logger.info("================================================================================")
    logger.info("           SPAFS V5.2: STREAM 2 MACHINE LEARNING PIPELINE (%s)                  ", ", ".join(models))
    logger.info("================================================================================")
    start_total = time.time()
    artifact_mgr = ArtifactManager(base_dir=artifacts_dir)

    # 1. Load validated Stream 2 dataset
    path = Path(data_path)
    if not path.exists():
        logger.error("Dataset not found at %s. Please run data preparation pipeline first.", path)
        sys.exit(1)

    df_stream2 = pd.read_parquet(path)
    df_stream2["market_date"] = pd.to_datetime(df_stream2["market_date"])
    df_stream2 = df_stream2.sort_values("market_date").reset_index(drop=True)
    logger.info(
        "Loaded Stream 2 dataset: %d rows (%s to %s)",
        len(df_stream2),
        df_stream2["market_date"].min().date(),
        df_stream2["market_date"].max().date(),
    )

    executed_models = []
    leaderboard_records = []
    predictions_map: dict[str, pd.DataFrame] = {}

    # Try loading existing predictions if evaluating a single model
    for mid in ("M4", "M5"):
        pred_path = artifact_mgr.predictions_dir / f"pred_{mid}_stream2.parquet"
        if pred_path.exists():
            try:
                predictions_map[mid] = pd.read_parquet(pred_path)
            except Exception as e:
                logger.warning("Could not read cached predictions for %s: %s", mid, e)

    # Run each requested model
    for model_id in models:
        model_id = model_id.upper()
        factory, model_name = _get_model_factory(model_id)

        # 2. Extract whitelisted feature matrix
        mat = extract_model_matrix(df_stream2, model_id)
        logger.info(
            "Extracted %s matrix: %d observations, %d features: %s",
            model_id,
            len(mat.y),
            len(mat.spec.features),
            list(mat.spec.features),
        )

        # =========================================================================
        # BRANCH A: FULL-SAMPLE ESTIMATION & FEATURE IMPORTANCE PERSISTENCE
        # =========================================================================
        logger.info("--------------------------------------------------------------------------------")
        logger.info("[BRANCH A] Full-Sample Model Estimation & Multi-Seed Ensemble for %s (N=%d)", model_id, len(mat.y))
        logger.info("--------------------------------------------------------------------------------")

        model_inst = factory()
        model_inst.fit(mat.X, mat.y)
        artifact_mgr.save_model(model_inst)
        artifact_mgr.save_coefficients(model_inst)

        logger.info("%s Top 5 Features (Gain Importance):", model_id)
        for feat, gain in list(model_inst.feature_importances_gain_.items())[:5]:
            logger.info("  - %-30s: %.4f", feat, gain)

        if not walk_forward:
            logger.info("Walk-forward evaluation skipped for %s.", model_id)
            executed_models.append(model_id)
            continue

        # =========================================================================
        # BRANCH B: EXPANDING WALK-FORWARD VALIDATION
        # =========================================================================
        logger.info("--------------------------------------------------------------------------------")
        logger.info("[BRANCH B] Expanding Walk-Forward OOS Forecasting for %s (Warmup=%d, Refit=%d)", model_id, initial_window, refit_every)
        logger.info("--------------------------------------------------------------------------------")

        wf_res = run_walk_forward_evaluation(
            model_factory=factory,
            X=mat.X,
            y=mat.y,
            initial_train_size=initial_window,
            refit_every=refit_every,
        )
        artifact_mgr.save_predictions(wf_res.predictions_df, model_id=model_id, tag="stream2")
        predictions_map[model_id] = wf_res.predictions_df

        pred_df = wf_res.predictions_df
        met = forecast_metrics(pred_df["actual_return"], pred_df["predicted_return"])  # vs zero (M0a)
        m_metrics = {"model_id": model_id, "name": model_name, **met}
        leaderboard_records.append(m_metrics)
        executed_models.append(model_id)

    # =========================================================================
    # PAIRWISE STATISTICAL COMPARISON: M5 vs M4
    # =========================================================================
    pairwise_results: list[dict[str, Any]] = []
    if "M4" in predictions_map and "M5" in predictions_map:
        logger.info("--------------------------------------------------------------------------------")
        logger.info("[PAIRWISE TESTING] Formal Comparison: Candidate M5 vs Benchmark M4")
        logger.info("--------------------------------------------------------------------------------")

        pred_m4 = predictions_map["M4"]
        pred_m5 = predictions_map["M5"]

        common_idx = pred_m5.index.intersection(pred_m4.index)
        if len(common_idx) > 0:
            df_m4_common = pred_m4.loc[common_idx]
            df_m5_common = pred_m5.loc[common_idx]

            y_c = df_m5_common["actual_return"]
            p5, p4 = df_m5_common["predicted_return"], df_m4_common["predicted_return"]
            dm_sq = dm_test(y_c, p5, p4, loss="squared", horizon=1, candidate_id="M5", benchmark_id="M4")
            dm_abs = dm_test(y_c, p5, p4, loss="absolute", horizon=1, candidate_id="M5", benchmark_id="M4")
            cw = cw_test(y_c, p5, p4, horizon=1, candidate_id="M5", benchmark_id="M4")

            pw_record = {
                "candidate_id": "M5",
                "benchmark_id": "M4",
                "hypothesis": "H0: Refining spreads (M5) do not reduce OOS forecast error over technical momentum (M4).",
                "n_obs": len(common_idx),
                "dm_squared_hln_stat": dm_sq.statistic,
                "dm_squared_p_value_one_sided": dm_sq.p_value_one_sided,
                "dm_squared_reject_005": dm_sq.reject_at(0.05),
                "dm_squared_loss_diff_mean": dm_sq.mean_differential,
                "dm_absolute_hln_stat": dm_abs.statistic,
                "dm_absolute_p_value_one_sided": dm_abs.p_value_one_sided,
                "dm_absolute_reject_005": dm_abs.reject_at(0.05),
                "dm_absolute_loss_diff_mean": dm_abs.mean_differential,
                "cw_stat": cw.statistic,
                "cw_p_value_one_sided": cw.p_value_one_sided,
                "cw_reject_005": cw.reject_at(0.05),
                "cw_adjusted_loss_diff": cw.mean_differential,
            }
            pairwise_results.append(pw_record)
            artifact_mgr.save_metrics(pairwise_results, filename="stream2_pairwise_tests.json")

            logger.info("DM squared: stat=%.4f p1=%.4g | DM absolute: stat=%.4f p1=%.4g | CW: stat=%.4f p1=%.4g",
                        dm_sq.statistic, dm_sq.p_value_one_sided, dm_abs.statistic, dm_abs.p_value_one_sided,
                        cw.statistic, cw.p_value_one_sided)
        else:
            logger.warning("No overlapping evaluation indices between M4 and M5 for pairwise testing.")

    # =========================================================================
    # LEADERBOARD CONSOLIDATION
    # =========================================================================
    if leaderboard_records:
        # Load any existing leaderboard records to avoid overwriting un-run models
        existing_board_path = artifact_mgr.metrics_dir / "stream2_ml_leaderboard.json"
        all_records_map = {}
        if existing_board_path.exists():
            try:
                with open(existing_board_path, "r", encoding="utf-8") as f:
                    for rec in json.load(f):
                        all_records_map[rec["model_id"]] = rec
            except Exception:
                pass

        for rec in leaderboard_records:
            all_records_map[rec["model_id"]] = rec

        consolidated_leaderboard = list(all_records_map.values())
        artifact_mgr.save_metrics(consolidated_leaderboard, filename="stream2_ml_leaderboard.json")

        df_leaderboard = pd.DataFrame(consolidated_leaderboard)
        artifact_mgr.save_leaderboard(df_leaderboard, filename="stream2_ml_leaderboard.csv")

        print("\n" + "=" * 90)
        print("                 SPAFS V5.2 - STREAM 2 ML LEADERBOARD")
        print("=" * 90)
        print(df_leaderboard[["model_id", "n", "rmse", "mae", "r2_oos_pct", "da_pct", "mcc", "pt_stat"]].to_string(index=False))
        print("=" * 90)

    # Manifest creation
    manifest_name = f"stream2_ml_{'_'.join(m.lower() for m in executed_models)}"
    artifact_mgr.create_manifest(
        stream_name=manifest_name,
        models_executed=executed_models,
        data_path=path,
        extra_meta={
            "initial_window": initial_window,
            "refit_every": refit_every,
            "models": executed_models,
        },
    )
    logger.info("Pipeline completed successfully in %.2f seconds.", time.time() - start_total)


def main():
    parser = argparse.ArgumentParser(description="SPAFS V5.2 Machine Learning Runner (M4, M5)")
    parser.add_argument(
        "--model",
        choices=["M4", "M5", "all"],
        default="M5",
        help="Model ID to execute (M4, M5, or all)",
    )
    parser.add_argument(
        "--data-path",
        default="data/processed/stream2_aligned_nlp_2017_2025.parquet",
        help="Path to Stream 2 dataset",
    )
    parser.add_argument(
        "--initial-window",
        type=int,
        default=1500,
        help="Initial training warmup size for Walk-Forward (default: 1500)",
    )
    parser.add_argument(
        "--refit-every",
        type=int,
        default=20,
        help="Refitting frequency in trading days (default: 20 days)",
    )
    parser.add_argument(
        "--skip-walk-forward",
        action="store_true",
        help="Run only Branch A full-sample estimation without walk-forward",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Target directory for generated artifacts",
    )
    args = parser.parse_args()

    models_to_run = ["M4", "M5"] if args.model == "all" else [args.model]

    run_stream2_ml_pipeline(
        models=models_to_run,
        data_path=args.data_path,
        walk_forward=not args.skip_walk_forward,
        initial_window=args.initial_window,
        refit_every=args.refit_every,
        artifacts_dir=args.artifacts_dir,
    )


if __name__ == "__main__":
    main()
