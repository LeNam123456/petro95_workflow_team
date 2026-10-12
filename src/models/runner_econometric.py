"""CLI Runner for Econometric Models (M0a, M0b, M1, M2, M3) in SPAFS V5.2.

Executes:
- Branch A: Full-sample parameter estimation, multicollinearity diagnostics,
  residual diagnostics, and RQ1 Wald hypothesis testing with artifact persistence.
- Branch B: Expanding Walk-Forward 1-step-ahead validation generating true OOS predictions,
  pairwise statistical tests (Diebold-Mariano HLN 1997, Clark-West 2007),
  leaderboard CSV, and cryptographic SHA-256 manifests.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_proccessing.model_schemas import (
    PAIRWISE_COMPARISONS,
    extract_common_sample_matrices,
    extract_model_matrix,
)
from src.models.diagnostics import diagnose_multicollinearity, diagnose_residuals
from src.models.econometric.arma import ArmaModel
from src.models.econometric.dynamic_adl import AsymmetricAdlModel, LinearDynamicModel
from src.models.econometric.naive import NaiveDirectionModel, NaiveZeroModel
from src.models.evaluation.hypothesis import run_rq1_wald_tests
from src.models.evaluation.metrics import (
    compute_directional_metrics,
    compute_regression_metrics,
)
from src.models.evaluation.pairwise import clark_west_test, diebold_mariano_test
from src.models.persistence import ArtifactManager
from src.models.validation.walk_forward import run_walk_forward_evaluation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SPAFS_V5.2.EconometricRunner")


def run_stream1_econometric_pipeline(
    data_path: str = "data/processed/stream1_econometric_2008_2025.parquet",
    walk_forward: bool = True,
    initial_window: int = 3500,
    artifacts_dir: str = "artifacts",
) -> None:
    """Execute complete end-to-end econometric pipeline for Stream 1 (M0a through M3).

    Args:
        data_path: Path to Stream 1 Parquet dataset.
        walk_forward: If True, execute Branch B walk-forward out-of-sample evaluation.
        initial_window: Initial warmup observation count for expanding walk-forward.
        artifacts_dir: Base directory for storing artifacts.
    """
    logger.info("================================================================================")
    logger.info("       SPAFS V5.2: STREAM 1 ECONOMETRIC PIPELINE (M0a, M0b, M1, M2, M3)         ")
    logger.info("================================================================================")
    start_total = time.time()
    artifact_mgr = ArtifactManager(base_dir=artifacts_dir)

    # 1. Load validated Stream 1 dataset
    path = Path(data_path)
    if not path.exists():
        logger.error("Dataset not found at %s. Please run data preparation pipeline first.", path)
        sys.exit(1)

    df_stream1 = pd.read_parquet(path)
    df_stream1["market_date"] = pd.to_datetime(df_stream1["market_date"])
    df_stream1 = df_stream1.sort_values("market_date").reset_index(drop=True)
    n_raw = len(df_stream1)
    logger.info(
        "Loaded Stream 1 dataset: %d rows (%s to %s)",
        n_raw,
        df_stream1["market_date"].min().date(),
        df_stream1["market_date"].max().date(),
    )

    # 2. Extract Common-Sample Matrices (N = 4,425) for fair statistical power
    model_ids = ["M0a", "M0b", "M1", "M2", "M3"]
    matrices = extract_common_sample_matrices(df_stream1, model_ids=model_ids)
    n_common = len(matrices["M3"].y)
    logger.info("Extracted aligned common sample across %s: N = %d rows", model_ids, n_common)

    # =========================================================================
    # BRANCH A: FULL-SAMPLE ESTIMATION, DIAGNOSTICS & HYPOTHESIS TESTING
    # =========================================================================
    logger.info("--------------------------------------------------------------------------------")
    logger.info("[BRANCH A] Full-Sample Model Estimation & RQ1 Econometric Inference (N=%d)", n_common)
    logger.info("--------------------------------------------------------------------------------")

    # Fit M0a (Naive Zero)
    m0a = NaiveZeroModel()
    m0a.fit(matrices["M0a"].X, matrices["M0a"].y)
    artifact_mgr.save_model(m0a)
    artifact_mgr.save_coefficients(m0a)
    logger.info("M0a fitted & saved.")

    # Fit M0b (Naive Direction)
    m0b = NaiveDirectionModel()
    m0b.fit(matrices["M0b"].X, matrices["M0b"].y)
    artifact_mgr.save_model(m0b)
    artifact_mgr.save_coefficients(m0b)
    logger.info("M0b fitted & saved.")

    # Fit M1 (ARMA(1,1) MLE / Kalman Filter)
    m1 = ArmaModel(order=(1, 0, 1), trend="c")
    m1.fit(matrices["M1"].X, matrices["M1"].y)
    artifact_mgr.save_model(m1)
    artifact_mgr.save_coefficients(m1)
    logger.info("M1 fitted & saved. AIC=%.2f, BIC=%.2f", m1.results_.aic, m1.results_.bic)

    # Fit M2 (Linear Dynamic HAC)
    m2 = LinearDynamicModel(hac_lags=5)
    m2.fit(matrices["M2"].X, matrices["M2"].y)
    artifact_mgr.save_model(m2)
    artifact_mgr.save_coefficients(m2)
    logger.info("M2 fitted & saved. R²=%.4f, Adj R²=%.4f", m2.results_.rsquared, m2.results_.rsquared_adj)

    # Fit M3 (Asymmetric ADL HAC) - RQ1 Core Model
    m3 = AsymmetricAdlModel(hac_lags=5)
    m3.fit(matrices["M3"].X, matrices["M3"].y)
    artifact_mgr.save_model(m3)
    artifact_mgr.save_coefficients(m3)
    logger.info("M3 fitted & saved. R²=%.4f, Adj R²=%.4f", m3.results_.rsquared, m3.results_.rsquared_adj)

    # 3. Multicollinearity Diagnostics for M2 and M3
    m2_vif = diagnose_multicollinearity(matrices["M2"].X, model_id="M2")
    m3_vif = diagnose_multicollinearity(matrices["M3"].X, model_id="M3")
    artifact_mgr.save_metrics(
        {
            "M2": {
                "condition_number": m2_vif.condition_number,
                "vif_scores": m2_vif.vif_scores,
                "max_vif_feature": m2_vif.max_vif_feature,
                "max_vif_value": m2_vif.max_vif_value,
                "has_severe_multicollinearity": m2_vif.has_severe_multicollinearity,
            },
            "M3": {
                "condition_number": m3_vif.condition_number,
                "vif_scores": m3_vif.vif_scores,
                "max_vif_feature": m3_vif.max_vif_feature,
                "max_vif_value": m3_vif.max_vif_value,
                "has_severe_multicollinearity": m3_vif.has_severe_multicollinearity,
            },
        },
        filename="multicollinearity_diagnostics.json",
    )
    logger.info(
        "Multicollinearity check: M2 CondNum=%.2f (Max VIF=%.2f), M3 CondNum=%.2f (Max VIF=%.2f)",
        m2_vif.condition_number,
        m2_vif.max_vif_value,
        m3_vif.condition_number,
        m3_vif.max_vif_value,
    )

    # 4. Residual Diagnostics for M1, M2, M3
    res_m1 = diagnose_residuals(m1.results_.resid, lags=(5, 10, 20))
    res_m2 = diagnose_residuals(m2.results_.resid, lags=(5, 10, 20))
    res_m3 = diagnose_residuals(m3.results_.resid, lags=(5, 10, 20))
    artifact_mgr.save_metrics(
        {"M1": res_m1, "M2": res_m2, "M3": res_m3},
        filename="residual_diagnostics.json",
    )
    logger.info("Saved residual diagnostics for M1, M2, M3.")

    # 5. RQ1 Formal Wald Hypothesis Tests for M3
    rq1_results = run_rq1_wald_tests(m3)
    artifact_mgr.save_metrics(rq1_results, filename="rq1_wald_tests.json")
    logger.info("=== RQ1 WALD TEST RESULTS ===")
    logger.info(
        "H0(1) Contemporaneous: W_F=%.4f (p=%.4e), Reject@5%%=%s",
        rq1_results["h0_contemporaneous"]["wald_f_stat"],
        rq1_results["h0_contemporaneous"]["p_value"],
        rq1_results["h0_contemporaneous"]["reject_h0_at_005"],
    )
    logger.info(
        "H0(2) Cumulative 2-Day: W_F=%.4f (p=%.4e), Reject@5%%=%s",
        rq1_results["h0_cumulative"]["wald_f_stat"],
        rq1_results["h0_cumulative"]["p_value"],
        rq1_results["h0_cumulative"]["reject_h0_at_005"],
    )
    logger.info(
        "H0(joint) Nested (M3 nests M2): W_F=%.4f (df=%d, p=%.4e), Reject@5%%=%s",
        rq1_results["h0_joint_nested"]["wald_f_stat"],
        rq1_results["h0_joint_nested"]["df"],
        rq1_results["h0_joint_nested"]["p_value"],
        rq1_results["h0_joint_nested"]["reject_h0_at_005"],
    )

    if not walk_forward:
        logger.info("Walk-forward evaluation skipped. Branch A complete.")
        artifact_mgr.create_manifest(
            stream_name="stream1_econometric",
            models_executed=model_ids,
            data_path=path,
            extra_meta={"branch_b_walk_forward": False},
        )
        return

    # =========================================================================
    # BRANCH B: EXPANDING WALK-FORWARD 1-STEP-AHEAD OUT-OF-SAMPLE VALIDATION
    # =========================================================================
    logger.info("--------------------------------------------------------------------------------")
    logger.info("[BRANCH B] Expanding Walk-Forward Out-of-Sample Forecasting (Warmup=%d)", initial_window)
    logger.info("--------------------------------------------------------------------------------")

    factories = {
        "M0a": lambda: NaiveZeroModel(),
        "M0b": lambda: NaiveDirectionModel(),
        "M1": lambda: ArmaModel(order=(1, 0, 1), trend="c"),
        "M2": lambda: LinearDynamicModel(hac_lags=5),
        "M3": lambda: AsymmetricAdlModel(hac_lags=5),
    }

    oos_results: dict[str, Any] = {}
    for mid in model_ids:
        logger.info("Running Walk-Forward for %s...", mid)
        wf_res = run_walk_forward_evaluation(
            model_factory=factories[mid],
            X=matrices[mid].X,
            y=matrices[mid].y,
            initial_train_size=initial_window,
            refit_every=1,
        )
        oos_results[mid] = wf_res
        artifact_mgr.save_predictions(wf_res.predictions_df, model_id=mid, tag="stream1")

    # Benchmark predictions for Campbell-Thompson OOS-R² (M0a zero return)
    y_true = oos_results["M0a"].predictions_df["actual_return"]
    y_m0a = oos_results["M0a"].predictions_df["predicted_return"]

    # Compute Leaderboard
    leaderboard_rows = []
    for mid in model_ids:
        pred_df = oos_results[mid].predictions_df
        reg_metrics = compute_regression_metrics(
            y_true=pred_df["actual_return"],
            y_pred=pred_df["predicted_return"],
            y_benchmark=y_m0a,
        )
        dir_metrics = compute_directional_metrics(
            y_true_dir=pred_df["actual_direction"],
            y_pred_dir=pred_df["predicted_direction"],
        )
        leaderboard_rows.append({
            "model_id": mid,
            "n_oos": len(pred_df),
            "rmse": reg_metrics["rmse"],
            "mae": reg_metrics["mae"],
            "oos_r2": reg_metrics.get("oos_r2", 0.0),
            "r2_in_sample": reg_metrics["r2"],
            "directional_accuracy": dir_metrics["directional_accuracy"],
            "mcc": dir_metrics["mcc"],
            "pt_stat": dir_metrics["pt_stat"],
            "pt_p_value": dir_metrics["pt_p_value"],
        })

    df_leaderboard = pd.DataFrame(leaderboard_rows)
    artifact_mgr.save_leaderboard(df_leaderboard, filename="stream1_econometric_leaderboard.csv")
    artifact_mgr.save_metrics(leaderboard_rows, filename="stream1_econometric_leaderboard.json")

    # Compute Pairwise Statistical Tests across Stream 1 comparisons
    pairwise_reports = []
    stream1_comps = [c for c in PAIRWISE_COMPARISONS if c.eval_stream == "stream1"]
    for comp in stream1_comps:
        cand_df = oos_results[comp.candidate_id].predictions_df
        bench_df = oos_results[comp.benchmark_id].predictions_df

        e_cand = cand_df["actual_return"].values - cand_df["predicted_return"].values
        e_bench = bench_df["actual_return"].values - bench_df["predicted_return"].values

        # Diebold-Mariano Test (HLN 1997)
        dm_res = diebold_mariano_test(
            e_candidate=e_cand,
            e_benchmark=e_bench,
            loss="squared",
            h=1,
            candidate_id=comp.candidate_id,
            benchmark_id=comp.benchmark_id,
        )

        # Clark-West Test for Nested Models
        cw_res = clark_west_test(
            y_true=cand_df["actual_return"].values,
            y_pred_small=bench_df["predicted_return"].values,
            y_pred_large=cand_df["predicted_return"].values,
            candidate_id=comp.candidate_id,
            benchmark_id=comp.benchmark_id,
        )

        pairwise_reports.append({
            "candidate_id": comp.candidate_id,
            "benchmark_id": comp.benchmark_id,
            "hypothesis": comp.hypothesis,
            "dm_hln_stat": dm_res.test_statistic,
            "dm_p_value": dm_res.p_value,
            "dm_reject_005": dm_res.reject_h0_at_005,
            "dm_mean_loss_diff": dm_res.loss_differential_mean,
            "cw_stat": cw_res.test_statistic,
            "cw_p_value": cw_res.p_value,
            "cw_reject_005": cw_res.reject_h0_at_005,
            "cw_adjusted_loss_diff": cw_res.loss_differential_mean,
        })

    artifact_mgr.save_metrics(pairwise_reports, filename="stream1_pairwise_tests.json")

    # Generate Manifest
    artifact_mgr.create_manifest(
        stream_name="stream1_econometric",
        models_executed=model_ids,
        data_path=path,
        extra_meta={
            "initial_window": initial_window,
            "n_oos_evaluations": len(y_true),
            "refit_every": 1,
        },
    )

    # Print Formatted Leaderboard
    print("\n" + "=" * 90)
    print("           SPAFS V5.2 - STREAM 1 ECONOMETRIC LEADERBOARD (M0a to M3)")
    print("=" * 90)
    print(df_leaderboard.to_string(index=False))
    print("=" * 90)
    logger.info("Econometric pipeline finished successfully in %.2f seconds.", time.time() - start_total)


def main():
    parser = argparse.ArgumentParser(description="SPAFS V5.2 Econometric Runner (M0a through M3)")
    parser.add_argument(
        "--data-path",
        default="data/processed/stream1_econometric_2008_2025.parquet",
        help="Path to Stream 1 dataset",
    )
    parser.add_argument(
        "--initial-window",
        type=int,
        default=3500,
        help="Initial training warmup size (tau_0) for Walk-Forward",
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

    run_stream1_econometric_pipeline(
        data_path=args.data_path,
        walk_forward=not args.skip_walk_forward,
        initial_window=args.initial_window,
        artifacts_dir=args.artifacts_dir,
    )


if __name__ == "__main__":
    main()
