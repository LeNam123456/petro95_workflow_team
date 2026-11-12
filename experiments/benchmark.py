"""Benchmark orchestrator for Mogas 95 forecasting pipeline (Seam A).

Executes:
1. Split integrity verification and PIT audit governance.
2. Naive persistence baseline across horizons h in {1, 5, 21}.
3. Direct multi-horizon XGBoost regressions (Univariate & Multivariate).
4. Direct multi-horizon sequence Deep Learning (LSTM & GRU, Univariate & Multivariate).
5. Price reconstruction to USD/barrel and evaluation across 6 standard metrics + 3-state DA.
6. Export of per-horizon predictions, feature importance rankings, neural checkpoints, publication figures, and full reproducible experiment manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any
import numpy as np
import pandas as pd
import yaml

from src.data.dataset import SupervisedBatch, build_supervised_samples
from src.data.manifest import build_experiment_manifest, save_experiment_manifest
from src.data.validation import audit_point_in_time, verify_splits_integrity
from src.evaluation.metrics import compute_metrics
from src.evaluation.visualization import (
    plot_actual_vs_predicted,
    plot_directional_confusion_matrices,
    plot_loss_curves,
)
from src.models.base import Forecaster
from src.models.baseline import NaivePersistenceModel
from src.models.gru import GRUForecaster
from src.models.lstm import LSTMForecaster
from src.models.xgboost_model import XGBoostConfig, XGBoostForecaster
from src.training.trainer import RecurrentTrainingConfig, set_seed


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
    pred_prices: np.ndarray,
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


def _evaluate_and_record(
    model: Forecaster,
    batch: SupervisedBatch,
    scenario: str,
    horizon: int,
    runtime_seconds: float | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Evaluate model on batch, calculate standard metrics, and assemble outputs."""
    pred_prices = model.predict_prices(batch)
    metrics = compute_metrics(
        actual_prices=batch.actual_prices,
        predicted_prices=pred_prices,
        origin_prices=batch.origin_prices,
    )
    pred_df = _build_predictions_df(
        batch=batch,
        model_name=model.name,
        scenario=scenario,
        pred_prices=pred_prices,
    )
    leaderboard_entry: dict[str, Any] = {
        "model": model.name,
        "scenario": scenario,
        "target_representation": batch.target_representation,
        "horizon": horizon,
        **metrics,
    }
    if runtime_seconds is not None:
        leaderboard_entry["runtime_seconds"] = round(runtime_seconds, 4)

    return pred_df, leaderboard_entry


def run_benchmark(
    models: list[str] | tuple[str, ...] = ("naive", "xgboost", "lstm", "gru"),
    manifest_path: str | Path = "data/splits/splits_manifest.json",
    splits_dir: str | Path = "data/splits",
    output_dir: str | Path = "outputs",
    config_path: str | Path | None = "configs/models.yaml",
    horizons: tuple[int, ...] = (1, 5, 21),
    scenarios: tuple[str, ...] = ("univariate", "multivariate"),
    target_representation: str = "relative_change",
    include_price_level_ablation: bool = False,
    lookback: int = 30,
    seed: int = 42,
    xgb_n_estimators: int | None = None,
    xgb_early_stopping_rounds: int | None = None,
    nn_epochs: int | None = None,
    nn_batch_size: int | None = None,
    nn_hidden_dim: int | None = None,
    nn_num_layers: int | None = None,
    nn_patience: int | None = None,
    nn_learning_rate: float | None = None,
    generate_plots: bool = True,
    verbose: bool = False,
) -> pd.DataFrame:
    """Execute multi-model forecasting benchmark pipeline."""
    total_start_time = time.perf_counter()

    # Ensure canonical determinism
    set_seed(seed)

    m_path = Path(manifest_path)
    s_dir = Path(splits_dir)
    out_dir = Path(output_dir)
    preds_dir = out_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = out_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify split integrity
    integrity_report = verify_splits_integrity(m_path, raise_on_error=True)

    # 2. Read manifest to resolve partition files
    manifest_data = json.loads(m_path.read_text(encoding="utf-8"))
    partition_keys = list(manifest_data.get("partitions", {}).keys())

    train_file = f"{partition_keys[0]}.parquet" if len(partition_keys) > 0 else "train_2008_2020.parquet"
    val_file = f"{partition_keys[1]}.parquet" if len(partition_keys) > 1 else "val_2021_2023.parquet"
    test_file = f"{partition_keys[2]}.parquet" if len(partition_keys) > 2 else "test_2024_2025.parquet"

    # Load splits in strictly read-only mode
    train_df = pd.read_parquet(s_dir / train_file)
    val_df = pd.read_parquet(s_dir / val_file)
    test_df = pd.read_parquet(s_dir / test_file)

    # 3. Audit PIT governance
    canonical_source = manifest_data.get("dataset_source", "data/interim/canonical_market_panel.parquet")
    canonical_path = Path(canonical_source)
    if not canonical_path.is_absolute():
        canonical_path = m_path.parent.parent.parent / canonical_source
    canonical_df = pd.read_parquet(canonical_path)
    pit_report = audit_point_in_time(canonical_df, horizons=horizons, raise_on_error=True)

    # 4. Load hyperparameters from config
    yaml_configs = load_model_configs(config_path)
    xgb_yaml = yaml_configs.get("xgboost", {})
    lstm_yaml = yaml_configs.get("lstm", {})
    gru_yaml = yaml_configs.get("gru", {})

    # XGBoost hyperparams
    n_estimators = xgb_n_estimators or xgb_yaml.get("n_estimators", 500)
    max_depth = xgb_yaml.get("max_depth", 4)
    learning_rate = xgb_yaml.get("learning_rate", 0.05)
    subsample = xgb_yaml.get("subsample", 0.8)
    colsample_bytree = xgb_yaml.get("colsample_bytree", 0.8)
    xgb_early_stopping = (
        xgb_early_stopping_rounds
        if xgb_early_stopping_rounds is not None
        else xgb_yaml.get("early_stopping_rounds", 15)
    )
    xgb_seed = seed or xgb_yaml.get("random_state", 42)

    # Recurrent hyperparams
    def build_recurrent_config(model_yaml: dict[str, Any]) -> RecurrentTrainingConfig:
        return RecurrentTrainingConfig(
            hidden_dim=nn_hidden_dim or model_yaml.get("hidden_dim", 64),
            num_layers=nn_num_layers or model_yaml.get("num_layers", 2),
            dropout=model_yaml.get("dropout", 0.2),
            learning_rate=nn_learning_rate or model_yaml.get("learning_rate", 0.001),
            batch_size=nn_batch_size or model_yaml.get("batch_size", 32),
            epochs=nn_epochs if nn_epochs is not None else model_yaml.get("epochs", 100),
            early_stopping_patience=nn_patience or model_yaml.get("early_stopping_patience", 15),
            random_state=seed or model_yaml.get("random_state", 42),
            weight_decay=model_yaml.get("weight_decay", 0.0),
        )

    lstm_cfg = build_recurrent_config(lstm_yaml)
    gru_cfg = build_recurrent_config(gru_yaml)

    leaderboard_rows: list[dict[str, Any]] = []
    horizon_predictions: dict[int, list[pd.DataFrame]] = {h: [] for h in horizons}
    feature_importance_dfs: list[pd.DataFrame] = []
    loss_histories: dict[str, dict[str, list[float]]] = {}
    saved_checkpoints: list[str] = []

    normalized_models = [m.lower() for m in models]
    run_relative = target_representation in ("relative_change", "all", "both")
    run_price_level = (
        include_price_level_ablation or target_representation in ("price_level", "all", "both")
    )

    target_reps: list[str] = []
    if run_relative:
        target_reps.append("relative_change")
    if run_price_level:
        target_reps.append("price_level")

    # Pre-build SupervisedBatches for each (target_rep, scenario, horizon)
    # Cache batches to avoid redundant computation across models
    batches: dict[tuple[str, str, int], dict[str, SupervisedBatch]] = {}
    for rep in target_reps:
        for scenario in scenarios:
            for h in horizons:
                t_batch = build_supervised_samples(
                    partition_df=train_df,
                    prior_df=None,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=rep,
                )
                v_batch = build_supervised_samples(
                    partition_df=val_df,
                    prior_df=train_df,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=rep,
                )
                te_batch = build_supervised_samples(
                    partition_df=test_df,
                    prior_df=val_df,
                    lookback=lookback,
                    horizon=h,
                    scenario=scenario,
                    target_representation=rep,
                )
                batches[(rep, scenario, h)] = {
                    "train": t_batch,
                    "val": v_batch,
                    "test": te_batch,
                }

    # 5. Run Relative Change Models
    if run_relative:
        # 5.1 Naive Baseline (3 horizons)
        if "naive" in normalized_models:
            for h in horizons:
                t0 = time.perf_counter()
                batch = batches[("relative_change", "univariate", h)]["test"]
                model = NaivePersistenceModel()
                duration = time.perf_counter() - t0

                pred_df, entry = _evaluate_and_record(
                    model=model,
                    batch=batch,
                    scenario="univariate",
                    horizon=h,
                    runtime_seconds=duration,
                )
                horizon_predictions[h].append(pred_df)
                leaderboard_rows.append(entry)

        # 5.2 XGBoost Models (2 scenarios x 3 horizons = 6 configurations)
        if "xgboost" in normalized_models:
            for scenario in scenarios:
                for h in horizons:
                    train_batch = batches[("relative_change", scenario, h)]["train"]
                    val_batch = batches[("relative_change", scenario, h)]["val"]
                    test_batch = batches[("relative_change", scenario, h)]["test"]

                    t0 = time.perf_counter()
                    xgb_config = XGBoostConfig(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        learning_rate=learning_rate,
                        subsample=subsample,
                        colsample_bytree=colsample_bytree,
                        early_stopping_rounds=xgb_early_stopping,
                        random_state=xgb_seed,
                        eval_metric="rmse",
                    )
                    xgb_forecaster = XGBoostForecaster(config=xgb_config)
                    xgb_forecaster.fit(train_batch, val_batch=val_batch, verbose=verbose)
                    duration = time.perf_counter() - t0

                    pred_df, entry = _evaluate_and_record(
                        model=xgb_forecaster,
                        batch=test_batch,
                        scenario=scenario,
                        horizon=h,
                        runtime_seconds=duration,
                    )
                    horizon_predictions[h].append(pred_df)
                    leaderboard_rows.append(entry)

                    fi_df = xgb_forecaster.get_feature_importance_df(horizon=h, scenario=scenario)
                    feature_importance_dfs.append(fi_df)

        # 5.3 LSTM Models (2 scenarios x 3 horizons = 6 configurations)
        if "lstm" in normalized_models:
            for scenario in scenarios:
                for h in horizons:
                    train_batch = batches[("relative_change", scenario, h)]["train"]
                    val_batch = batches[("relative_change", scenario, h)]["val"]
                    test_batch = batches[("relative_change", scenario, h)]["test"]

                    t0 = time.perf_counter()
                    lstm_model = LSTMForecaster(
                        config=lstm_cfg,
                        checkpoint_dir=checkpoints_dir,
                    )
                    lstm_model.fit(train_batch, val_batch=val_batch)
                    duration = time.perf_counter() - t0

                    pred_df, entry = _evaluate_and_record(
                        model=lstm_model,
                        batch=test_batch,
                        scenario=scenario,
                        horizon=h,
                        runtime_seconds=duration,
                    )
                    horizon_predictions[h].append(pred_df)
                    leaderboard_rows.append(entry)

                    if lstm_model.history:
                        label = f"LSTM_{scenario}_h{h}"
                        loss_histories[label] = {
                            "train": lstm_model.history.train_losses,
                            "val": lstm_model.history.val_losses,
                        }

                    cp_file = checkpoints_dir / f"lstm_{scenario}_relative_change_h{h}.pt"
                    if cp_file.exists():
                        saved_checkpoints.append(str(cp_file.name))

        # 5.4 GRU Models (2 scenarios x 3 horizons = 6 configurations)
        if "gru" in normalized_models:
            for scenario in scenarios:
                for h in horizons:
                    train_batch = batches[("relative_change", scenario, h)]["train"]
                    val_batch = batches[("relative_change", scenario, h)]["val"]
                    test_batch = batches[("relative_change", scenario, h)]["test"]

                    t0 = time.perf_counter()
                    gru_model = GRUForecaster(
                        config=gru_cfg,
                        checkpoint_dir=checkpoints_dir,
                    )
                    gru_model.fit(train_batch, val_batch=val_batch)
                    duration = time.perf_counter() - t0

                    pred_df, entry = _evaluate_and_record(
                        model=gru_model,
                        batch=test_batch,
                        scenario=scenario,
                        horizon=h,
                        runtime_seconds=duration,
                    )
                    horizon_predictions[h].append(pred_df)
                    leaderboard_rows.append(entry)

                    if gru_model.history:
                        label = f"GRU_{scenario}_h{h}"
                        loss_histories[label] = {
                            "train": gru_model.history.train_losses,
                            "val": gru_model.history.val_losses,
                        }

                    cp_file = checkpoints_dir / f"gru_{scenario}_relative_change_h{h}.pt"
                    if cp_file.exists():
                        saved_checkpoints.append(str(cp_file.name))

    # 6. Run Price Level Ablation Models ({XGBoost, LSTM} x 2 scenarios x 3 horizons = 12 configurations)
    if run_price_level:
        # 6.1 XGBoost Price Level Ablation
        if "xgboost" in normalized_models or include_price_level_ablation:
            for scenario in scenarios:
                for h in horizons:
                    train_batch = batches[("price_level", scenario, h)]["train"]
                    val_batch = batches[("price_level", scenario, h)]["val"]
                    test_batch = batches[("price_level", scenario, h)]["test"]

                    t0 = time.perf_counter()
                    xgb_config = XGBoostConfig(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        learning_rate=learning_rate,
                        subsample=subsample,
                        colsample_bytree=colsample_bytree,
                        early_stopping_rounds=xgb_early_stopping,
                        random_state=xgb_seed,
                        eval_metric="rmse",
                    )
                    xgb_forecaster = XGBoostForecaster(config=xgb_config)
                    xgb_forecaster.fit(train_batch, val_batch=val_batch, verbose=verbose)
                    duration = time.perf_counter() - t0

                    pred_df, entry = _evaluate_and_record(
                        model=xgb_forecaster,
                        batch=test_batch,
                        scenario=scenario,
                        horizon=h,
                        runtime_seconds=duration,
                    )
                    horizon_predictions[h].append(pred_df)
                    leaderboard_rows.append(entry)

                    fi_df = xgb_forecaster.get_feature_importance_df(horizon=h, scenario=scenario)
                    feature_importance_dfs.append(fi_df)

        # 6.2 LSTM Price Level Ablation
        if "lstm" in normalized_models or include_price_level_ablation:
            for scenario in scenarios:
                for h in horizons:
                    train_batch = batches[("price_level", scenario, h)]["train"]
                    val_batch = batches[("price_level", scenario, h)]["val"]
                    test_batch = batches[("price_level", scenario, h)]["test"]

                    t0 = time.perf_counter()
                    lstm_model = LSTMForecaster(
                        config=lstm_cfg,
                        checkpoint_dir=checkpoints_dir,
                    )
                    lstm_model.fit(train_batch, val_batch=val_batch)
                    duration = time.perf_counter() - t0

                    pred_df, entry = _evaluate_and_record(
                        model=lstm_model,
                        batch=test_batch,
                        scenario=scenario,
                        horizon=h,
                        runtime_seconds=duration,
                    )
                    horizon_predictions[h].append(pred_df)
                    leaderboard_rows.append(entry)

                    if lstm_model.history:
                        label = f"LSTM_price_level_{scenario}_h{h}"
                        loss_histories[label] = {
                            "train": lstm_model.history.train_losses,
                            "val": lstm_model.history.val_losses,
                        }

                    cp_file = checkpoints_dir / f"lstm_{scenario}_price_level_h{h}.pt"
                    if cp_file.exists():
                        saved_checkpoints.append(str(cp_file.name))

    # 9. Write predictions per horizon
    for h, df_list in horizon_predictions.items():
        if df_list:
            combined_h_df = pd.concat(df_list, ignore_index=True)
            pred_csv_path = preds_dir / f"predictions_h{h}.csv"
            combined_h_df.to_csv(pred_csv_path, index=False)

    # 10. Export feature importance (if XGBoost was executed)
    if feature_importance_dfs:
        all_fi_df = pd.concat(feature_importance_dfs, ignore_index=True)
        fi_csv_path = out_dir / "feature_importance.csv"
        all_fi_df.to_csv(fi_csv_path, index=False)

    # 11. Plot and save loss curves (if recurrent models were executed)
    if loss_histories and generate_plots:
        plot_loss_curves(loss_histories, figures_dir / "loss_curves.png")
        loss_hist_file = out_dir / "loss_history.json"
        loss_hist_file.write_text(json.dumps(loss_histories, indent=2), encoding="utf-8")

    # 12. Plot actual vs predicted & directional confusion matrices
    if generate_plots:
        for h, df_list in horizon_predictions.items():
            if df_list:
                combined_h_df = pd.concat(df_list, ignore_index=True)
                plot_actual_vs_predicted(
                    predictions_df=combined_h_df,
                    horizon=h,
                    output_path=figures_dir / f"actual_vs_predicted_h{h}.png",
                )

        if any(horizon_predictions.values()):
            preds_by_h_dict = {
                h: pd.concat(df_list, ignore_index=True)
                for h, df_list in horizon_predictions.items()
                if df_list
            }
            plot_directional_confusion_matrices(
                predictions_by_horizon=preds_by_h_dict,
                output_path=figures_dir / "directional_confusion_matrix.png",
            )

    # 13. Write benchmark leaderboard
    leaderboard_df = pd.DataFrame(leaderboard_rows)
    leaderboard_path = out_dir / "benchmark_leaderboard.csv"
    leaderboard_df.to_csv(leaderboard_path, index=False)

    total_duration = time.perf_counter() - total_start_time

    # 14. Save full experiment manifest & audit manifest
    if run_price_level and run_relative:
        stage_str = "Stage 6 - Price Level Ablation Benchmark & Full 33-Configuration Evaluation"
    elif run_price_level:
        stage_str = "Stage 6 - Price Level Ablation Benchmark (XGBoost & LSTM)"
    elif {"lstm", "gru"}.intersection(normalized_models):
        stage_str = "Stage 5 - Sequence Deep Learning Benchmark (LSTM & GRU)"
    else:
        stage_str = "Stage 4 - XGBoost Relative Change Benchmark"

    hyperparams = {
        "xgboost": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "early_stopping_rounds": xgb_early_stopping,
            "random_state": xgb_seed,
        },
        "lstm": {
            "hidden_dim": lstm_cfg.hidden_dim,
            "num_layers": lstm_cfg.num_layers,
            "dropout": lstm_cfg.dropout,
            "learning_rate": lstm_cfg.learning_rate,
            "batch_size": lstm_cfg.batch_size,
            "epochs": lstm_cfg.epochs,
            "early_stopping_patience": lstm_cfg.early_stopping_patience,
            "random_state": lstm_cfg.random_state,
        },
        "gru": {
            "hidden_dim": gru_cfg.hidden_dim,
            "num_layers": gru_cfg.num_layers,
            "dropout": gru_cfg.dropout,
            "learning_rate": gru_cfg.learning_rate,
            "batch_size": gru_cfg.batch_size,
            "epochs": gru_cfg.epochs,
            "early_stopping_patience": gru_cfg.early_stopping_patience,
            "random_state": gru_cfg.random_state,
        },
    }

    generated_artifacts = {
        "leaderboard": str(leaderboard_path.relative_to(out_dir)),
        "predictions": [f"predictions/predictions_h{h}.csv" for h in horizons if horizon_predictions[h]],
        "figures": [
            f"figures/actual_vs_predicted_h{h}.png" for h in horizons if horizon_predictions[h]
        ] + (["figures/directional_confusion_matrix.png"] if any(horizon_predictions.values()) else []) + (["figures/loss_curves.png"] if loss_histories else []),
        "checkpoints": sorted(list(set(saved_checkpoints))),
    }

    full_manifest = build_experiment_manifest(
        benchmark_stage=stage_str,
        seed=seed,
        models_evaluated=list(models),
        target_representations_evaluated=target_reps,
        horizons_evaluated=list(horizons),
        splits_manifest_path=m_path,
        canonical_df=canonical_df,
        pit_audit_report=pit_report,
        splits_integrity=integrity_report,
        hyperparameters=hyperparams,
        leaderboard_df=leaderboard_df,
        saved_checkpoints=saved_checkpoints,
        partitions={"train": train_df, "val": val_df, "test": test_df},
        total_runtime_seconds=round(total_duration, 3),
        artifacts=generated_artifacts,
    )

    manifest_out_path = out_dir / "audit_manifest.json"
    save_experiment_manifest(full_manifest, manifest_out_path)
    experiment_manifest_path = out_dir / "experiment_manifest.json"
    save_experiment_manifest(full_manifest, experiment_manifest_path)

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
