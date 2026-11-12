"""Benchmark orchestrator for Mogas 95 forecasting pipeline (Seam A).

Executes:
1. Split integrity verification and PIT audit governance.
2. Naive persistence baseline across horizons h in {1, 5, 21}.
3. Direct multi-horizon XGBoost regressions (Univariate & Multivariate).
4. Price reconstruction to USD/barrel and evaluation across 6 standard metrics + 3-state DA.
5. Export of per-horizon predictions, feature importance rankings, benchmark leaderboard, and audit manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pandas as pd
import yaml

from src.data.dataset import SupervisedBatch, build_supervised_samples
from src.data.validation import audit_point_in_time, verify_splits_integrity
from src.evaluation.metrics import compute_metrics
from src.models.baseline import NaivePersistenceModel
from src.models.xgboost_model import XGBoostConfig, XGBoostForecaster


def load_model_configs(config_path: str | Path | None) -> dict[str, Any]:
    """Load model hyperparameters from YAML configuration file."""
    if config_path is None:
        return {}
    c_path = Path(config_path)
    if not c_path.exists():
        return {}
    try:
        content = c_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _build_predictions_df(
    batch: SupervisedBatch,
    model_name: str,
    scenario: str,
    pred_prices: Any,
) -> pd.DataFrame:
    """Construct standardized per-sample prediction records DataFrame."""
    return pd.DataFrame({
        "forecast_origin": batch.forecast_origins,
        "feature_available_at": batch.feature_available_ats,
        "target_timestamp": batch.target_timestamps,
        "horizon": batch.horizon,
        "model": model_name,
        "scenario": scenario,
        "target_representation": batch.target_representation,
        "origin_price": batch.origin_prices,
        "actual_price": batch.actual_prices,
        "predicted_price": pred_prices,
        "error": pred_prices - batch.actual_prices,
    })


def run_benchmark(
    models: list[str] | tuple[str, ...] = ("naive", "xgboost"),
    manifest_path: str | Path = "data/splits/splits_manifest.json",
    splits_dir: str | Path = "data/splits",
    output_dir: str | Path = "outputs",
    config_path: str | Path | None = "configs/models.yaml",
    horizons: tuple[int, ...] = (1, 5, 21),
    scenarios: tuple[str, ...] = ("univariate", "multivariate"),
    target_representation: str = "relative_change",
    lookback: int = 30,
    seed: int = 42,
    xgb_n_estimators: int | None = None,
    xgb_early_stopping_rounds: int | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """Execute multi-model forecasting benchmark pipeline."""
    m_path = Path(manifest_path)
    s_dir = Path(splits_dir)
    out_dir = Path(output_dir)
    preds_dir = out_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify split integrity
    integrity_report = verify_splits_integrity(m_path, raise_on_error=True)

    # 2. Load splits in strictly read-only mode
    train_df = pd.read_parquet(s_dir / "train_2008_2020.parquet")
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

    # 4. Load hyperparameters
    yaml_configs = load_model_configs(config_path)
    xgb_yaml = yaml_configs.get("xgboost", {})

    n_estimators = xgb_n_estimators or xgb_yaml.get("n_estimators", 500)
    max_depth = xgb_yaml.get("max_depth", 4)
    learning_rate = xgb_yaml.get("learning_rate", 0.05)
    subsample = xgb_yaml.get("subsample", 0.8)
    colsample_bytree = xgb_yaml.get("colsample_bytree", 0.8)
    early_stopping_rounds = (
        xgb_early_stopping_rounds
        if xgb_early_stopping_rounds is not None
        else xgb_yaml.get("early_stopping_rounds", 15)
    )
    xgb_seed = seed or xgb_yaml.get("random_state", 42)

    leaderboard_rows: list[dict[str, Any]] = []
    horizon_predictions: dict[int, list[pd.DataFrame]] = {h: [] for h in horizons}
    feature_importance_dfs: list[pd.DataFrame] = []

    normalized_models = [m.lower() for m in models]

    # 5. Run Naive Baseline
    if "naive" in normalized_models:
        for h in horizons:
            batch = build_supervised_samples(
                partition_df=test_df,
                prior_df=val_df,
                lookback=lookback,
                horizon=h,
                scenario="univariate",
                target_representation=target_representation,
            )

            model = NaivePersistenceModel()
            pred_prices = model.predict_prices(batch)

            metrics = compute_metrics(
                actual_prices=batch.actual_prices,
                predicted_prices=pred_prices,
                origin_prices=batch.origin_prices,
            )

            pred_df = _build_predictions_df(
                batch=batch,
                model_name="Naive",
                scenario="univariate",
                pred_prices=pred_prices,
            )
            horizon_predictions[h].append(pred_df)

            leaderboard_rows.append({
                "model": "Naive",
                "scenario": "univariate",
                "target_representation": target_representation,
                "horizon": h,
                **metrics,
            })

    # 6. Run XGBoost Models
    if "xgboost" in normalized_models:
        for scenario in scenarios:
            for h in horizons:
                # Build Train, Val, and Test batches
                train_batch = build_supervised_samples(
                    partition_df=train_df,
                    prior_df=None,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=target_representation,
                )
                val_batch = build_supervised_samples(
                    partition_df=val_df,
                    prior_df=train_df,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=target_representation,
                )
                test_batch = build_supervised_samples(
                    partition_df=test_df,
                    prior_df=val_df,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=target_representation,
                )

                xgb_config = XGBoostConfig(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    learning_rate=learning_rate,
                    subsample=subsample,
                    colsample_bytree=colsample_bytree,
                    early_stopping_rounds=early_stopping_rounds,
                    random_state=xgb_seed,
                    eval_metric="rmse",
                )
                xgb_forecaster = XGBoostForecaster(config=xgb_config)
                xgb_forecaster.fit(train_batch, val_batch=val_batch, verbose=verbose)

                pred_prices = xgb_forecaster.predict_prices(test_batch)

                metrics = compute_metrics(
                    actual_prices=test_batch.actual_prices,
                    predicted_prices=pred_prices,
                    origin_prices=test_batch.origin_prices,
                )

                pred_df = _build_predictions_df(
                    batch=test_batch,
                    model_name="XGBoost",
                    scenario=scenario,
                    pred_prices=pred_prices,
                )
                horizon_predictions[h].append(pred_df)

                fi_df = xgb_forecaster.get_feature_importance_df(horizon=h, scenario=scenario)
                feature_importance_dfs.append(fi_df)

                leaderboard_rows.append({
                    "model": "XGBoost",
                    "scenario": scenario,
                    "target_representation": target_representation,
                    "horizon": h,
                    **metrics,
                })

    # 7. Write predictions per horizon
    for h, df_list in horizon_predictions.items():
        if df_list:
            combined_h_df = pd.concat(df_list, ignore_index=True)
            pred_csv_path = preds_dir / f"predictions_h{h}.csv"
            combined_h_df.to_csv(pred_csv_path, index=False)

    # 8. Export feature importance
    if feature_importance_dfs:
        all_fi_df = pd.concat(feature_importance_dfs, ignore_index=True)
        fi_csv_path = out_dir / "feature_importance.csv"
        all_fi_df.to_csv(fi_csv_path, index=False)

    # 9. Write benchmark leaderboard
    leaderboard_df = pd.DataFrame(leaderboard_rows)
    leaderboard_path = out_dir / "benchmark_leaderboard.csv"
    leaderboard_df.to_csv(leaderboard_path, index=False)

    # 10. Save audit manifest
    audit_manifest = {
        "pipeline": "Pipeline Du bao Diem & Chieu huong Xang Platts Singapore Mogas 95",
        "benchmark_stage": "Stage 4 - XGBoost Relative Change Benchmark",
        "seed": seed,
        "models_evaluated": list(models),
        "splits_integrity": integrity_report,
        "pit_audit": pit_report.to_dict(),
        "horizons_evaluated": list(horizons),
        "test_sample_counts": {
            f"h{h}": int(leaderboard_df.loc[leaderboard_df["horizon"] == h, "n_samples"].iloc[0])
            for h in horizons
            if len(leaderboard_df.loc[leaderboard_df["horizon"] == h]) > 0
        },
        "hyperparameters": {
            "xgboost": {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "learning_rate": learning_rate,
                "subsample": subsample,
                "colsample_bytree": colsample_bytree,
                "early_stopping_rounds": early_stopping_rounds,
                "random_state": xgb_seed,
            }
        },
    }
    manifest_out_path = out_dir / "audit_manifest.json"
    manifest_out_path.write_text(json.dumps(audit_manifest, indent=2, default=str), encoding="utf-8")

    return leaderboard_df


def run_naive_benchmark(
    manifest_path: str | Path = "data/splits/splits_manifest.json",
    splits_dir: str | Path = "data/splits",
    output_dir: str | Path = "outputs",
    horizons: tuple[int, ...] = (1, 5, 21),
    lookback: int = 30,
    scenario: str = "univariate",
    target_representation: str = "relative_change",
) -> pd.DataFrame:
    """Execute Naive baseline benchmark pipeline across horizons (backwards compatibility)."""
    return run_benchmark(
        models=["naive"],
        manifest_path=manifest_path,
        splits_dir=splits_dir,
        output_dir=output_dir,
        horizons=horizons,
        lookback=lookback,
        scenarios=(scenario,),
        target_representation=target_representation,
    )
