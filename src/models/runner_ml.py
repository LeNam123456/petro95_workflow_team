"""CLI Runner for Machine Learning Model (M4 Technical LightGBM) in SPAFS V5.2.

Executes:
- Branch A: Full-sample model estimation, multi-seed ensemble aggregation,
  feature importance extraction (Gain & Split), and artifact persistence.
- Branch B: Expanding Walk-Forward 1-step-ahead validation generating true OOS predictions,
  regression metrics, directional metrics, and cryptographic SHA-256 manifests.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_proccessing.model_schemas import extract_model_matrix
from src.models.evaluation.metrics import (
    compute_directional_metrics,
    compute_regression_metrics,
)
from src.models.ml.lgbm import TechnicalLGBMModel
from src.models.persistence import ArtifactManager
from src.models.validation.walk_forward import run_walk_forward_evaluation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SPAFS_V5.2.MLRunner")


def run_stream2_m4_pipeline(
    data_path: str = "data/processed/stream2_aligned_nlp_2017_2025.parquet",
    walk_forward: bool = True,
    initial_window: int = 1500,
    refit_every: int = 20,
    artifacts_dir: str = "artifacts",
) -> None:
    """Execute machine learning pipeline for M4 Technical LightGBM on Stream 2.

    Args:
        data_path: Path to Stream 2 Parquet dataset.
        walk_forward: If True, execute Branch B walk-forward out-of-sample evaluation.
        initial_window: Initial warmup observation count for expanding walk-forward.
        refit_every: Re-estimation frequency in trading days (20 = monthly refit).
        artifacts_dir: Target directory for artifacts.
    """
    logger.info("================================================================================")
    logger.info("           SPAFS V5.2: STREAM 2 MACHINE LEARNING PIPELINE (M4)                  ")
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

    # 2. Extract M4 Matrix
    mat_m4 = extract_model_matrix(df_stream2, "M4")
    logger.info("Extracted M4 matrix: %d observations, %d features: %s", len(mat_m4.y), len(mat_m4.spec.features), list(mat_m4.spec.features))

    # =========================================================================
    # BRANCH A: FULL-SAMPLE ESTIMATION & FEATURE IMPORTANCE PERSISTENCE
    # =========================================================================
    logger.info("--------------------------------------------------------------------------------")
    logger.info("[BRANCH A] Full-Sample Model Estimation & Multi-Seed Ensemble (N=%d)", len(mat_m4.y))
    logger.info("--------------------------------------------------------------------------------")

    m4 = TechnicalLGBMModel()
    m4.fit(mat_m4.X, mat_m4.y)
    artifact_mgr.save_model(m4)
    artifact_mgr.save_coefficients(m4)

    logger.info("M4 Top 5 Features (Gain Importance):")
    for feat, gain in list(m4.feature_importances_gain_.items())[:5]:
        logger.info("  - %-25s: %.4f", feat, gain)

    if not walk_forward:
        logger.info("Walk-forward evaluation skipped. Branch A complete.")
        artifact_mgr.create_manifest(
            stream_name="stream2_ml_m4",
            models_executed=["M4"],
            data_path=path,
            extra_meta={"branch_b_walk_forward": False},
        )
        return

    # =========================================================================
    # BRANCH B: EXPANDING WALK-FORWARD VALIDATION
    # =========================================================================
    logger.info("--------------------------------------------------------------------------------")
    logger.info("[BRANCH B] Expanding Walk-Forward Out-of-Sample Forecasting (Warmup=%d, Refit=%d)", initial_window, refit_every)
    logger.info("--------------------------------------------------------------------------------")

    wf_res = run_walk_forward_evaluation(
        model_factory=lambda: TechnicalLGBMModel(),
        X=mat_m4.X,
        y=mat_m4.y,
        initial_train_size=initial_window,
        refit_every=refit_every,
    )
    artifact_mgr.save_predictions(wf_res.predictions_df, model_id="M4", tag="stream2")

    pred_df = wf_res.predictions_df
    reg_metrics = compute_regression_metrics(
        y_true=pred_df["actual_return"],
        y_pred=pred_df["predicted_return"],
    )
    dir_metrics = compute_directional_metrics(
        y_true_dir=pred_df["actual_direction"],
        y_pred_dir=pred_df["predicted_direction"],
    )

    m4_metrics = {
        "model_id": "M4",
        "n_oos": len(pred_df),
        "rmse": reg_metrics["rmse"],
        "mae": reg_metrics["mae"],
        "r2_in_sample": reg_metrics["r2"],
        "directional_accuracy": dir_metrics["directional_accuracy"],
        "mcc": dir_metrics["mcc"],
        "pt_stat": dir_metrics["pt_stat"],
        "pt_p_value": dir_metrics["pt_p_value"],
    }

    artifact_mgr.save_metrics([m4_metrics], filename="stream2_m4_leaderboard.json")

    # Generate Manifest
    artifact_mgr.create_manifest(
        stream_name="stream2_ml_m4",
        models_executed=["M4"],
        data_path=path,
        extra_meta={
            "initial_window": initial_window,
            "refit_every": refit_every,
            "n_oos_evaluations": len(pred_df),
        },
    )

    print("\n" + "=" * 80)
    print("           SPAFS V5.2 - STREAM 2 ML EVALUATION (M4)")
    print("=" * 80)
    print(pd.DataFrame([m4_metrics]).to_string(index=False))
    print("=" * 80)
    logger.info("ML pipeline finished successfully in %.2f seconds.", time.time() - start_total)


def main():
    parser = argparse.ArgumentParser(description="SPAFS V5.2 ML Runner (M4 Technical LightGBM)")
    parser.add_argument(
        "--data-path",
        default="data/processed/stream2_aligned_nlp_2017_2025.parquet",
        help="Path to Stream 2 dataset",
    )
    parser.add_argument(
        "--initial-window",
        type=int,
        default=1500,
        help="Initial training warmup size for Walk-Forward",
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

    run_stream2_m4_pipeline(
        data_path=args.data_path,
        walk_forward=not args.skip_walk_forward,
        initial_window=args.initial_window,
        refit_every=args.refit_every,
        artifacts_dir=args.artifacts_dir,
    )


if __name__ == "__main__":
    main()
