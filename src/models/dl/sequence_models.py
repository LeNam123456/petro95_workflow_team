# -*- coding: utf-8 -*-
"""Deep Learning Sequence Benchmark Models (RNN & LSTM) for Multi-Horizon SPAFS V5.2.

Key Quantitative Features:
1. Recurrent Neural Network (Elman RNN) & Long Short-Term Memory (LSTM).
2. Lookback sequence window of L = 20 trading days.
3. Strict Temporal Split with Purging & Embargo:
   - In-Sample: 2017 to 2022 (tau < 1500)
     * Train: 2017-01-03 to 2021-10-31 (approx 1200 days)
     * Purge & Embargo: Drop h + Embargo observations
     * Validation: 2021-11-01 to 2022-12-27 (approx 300 days)
   - Out-of-Sample (OOS): 2022-12-28 onwards (matches M0a..M5 exactly)
4. Scaler Governance:
   - StandardScaler fit strictly on Training sequences ONLY.
   - Zero lookahead leakage into Validation or Test sets.
5. Multi-Seed Ensemble & Stability:
   - 5 independent random seeds: [42, 101, 202, 303, 404].
   - Early stopping on validation loss (MSE) with patience = 5 epochs.
   - Saves best checkpoint per seed.
   - Reports Mean +- Standard Deviation across seeds for RMSE, MAE, DA, and MCC.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_proccessing.model_schemas import get_model_spec
from src.models.evaluation.forecast_tests import forecast_metrics

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.DeepLearning")

# Same information set as M5 (single source: the model registry).
FEATURES: list[str] = list(get_model_spec("M5").features)


class TimeSeriesRNN(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 32, num_layers: int = 1, dropout: float = 0.1):
        super().__init__()
        self.rnn = nn.RNN(in_dim, hidden_dim, num_layers=num_layers, batch_first=True, nonlinearity="tanh")
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out).squeeze(-1)


class TimeSeriesLSTM(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 32, num_layers: int = 1, dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(in_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out).squeeze(-1)


def create_sequences(X: np.ndarray, y: np.ndarray, lookback: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """Create sliding window sequences of length L."""
    n_samples = len(X) - lookback + 1
    if n_samples <= 0:
        raise ValueError(f"Length of X ({len(X)}) is less than lookback ({lookback})")
    seq_x = []
    seq_y = []
    for i in range(n_samples):
        seq_x.append(X[i : i + lookback])
        seq_y.append(y[i + lookback - 1])
    return np.array(seq_x, dtype=np.float32), np.array(seq_y, dtype=np.float32)


def evaluate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """RMSE/MAE/DA/MCC via the shared evaluation module."""
    m = forecast_metrics(y_true, y_pred)
    return {"rmse": m["rmse"], "mae": m["mae"], "da_pct": m["da_pct"], "mcc": m["mcc"]}


def train_single_deep_model(
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    seed: int = 42,
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 0.005,
    checkpoint_path: str = None,
) -> Tuple[np.ndarray, dict]:
    torch.manual_seed(seed)
    np.random.seed(seed)

    in_dim = X_train.shape[2]
    if model_type == "RNN":
        net = TimeSeriesRNN(in_dim=in_dim, hidden_dim=32, num_layers=1)
    elif model_type == "LSTM":
        net = TimeSeriesLSTM(in_dim=in_dim, hidden_dim=32, num_layers=1)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=lr, weight_decay=1e-4)

    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    best_val_loss = float("inf")
    best_weights = None
    best_epoch = -1
    patience = 6
    patience_counter = 0

    train_losses = []
    val_losses = []

    for ep in range(1, epochs + 1):
        net.train()
        ep_loss = 0.0
        n_batches = 0
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = net(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            ep_loss += float(loss.item())
            n_batches += 1
        avg_train = ep_loss / max(1, n_batches)
        train_losses.append(avg_train)

        # Validation
        net.eval()
        v_loss = 0.0
        v_batches = 0
        with torch.no_grad():
            for bx, by in val_loader:
                out = net(bx)
                loss = criterion(out, by)
                v_loss += float(loss.item())
                v_batches += 1
        avg_val = v_loss / max(1, v_batches)
        val_losses.append(avg_val)

        if avg_val < best_val_loss:
            best_val_loss = avg_val
            best_epoch = ep
            best_weights = {k: v.cpu().clone() for k, v in net.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    # Load best model
    if best_weights is not None:
        net.load_state_dict(best_weights)
        if checkpoint_path:
            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(best_weights, checkpoint_path)

    # Predict on test
    net.eval()
    with torch.no_grad():
        test_pred = net(torch.from_numpy(X_test)).numpy()

    return test_pred, {
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "final_train_loss": train_losses[-1],
        "epochs_trained": len(train_losses),
    }


def run_deep_learning_pipeline(
    data_path: str = "data/processed/stream2_multi_horizon_2017_2025.parquet",
    output_dir: str = "artifacts/deep_learning",
    seeds: list[int] = (42, 101, 202, 303, 404),
    lookback: int = 20,
) -> dict:
    p_out = Path(output_dir)
    p_out.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = p_out / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(data_path)
    df["market_date"] = pd.to_datetime(df["market_date"])
    df = df.sort_values("market_date").reset_index(drop=True)

    features = FEATURES
    for c in features:
        df[c] = df[c].fillna(0.0)

    # Common OOS boundary
    oos_start_idx = 1500  # corresponds to 2022-12-28
    val_size = 300  # 300 sessions for validation

    horizons = [("daily", 1, 0), ("weekly", 5, 2), ("monthly", 21, 5)]
    all_summary = []
    predictions_dump = {}

    for h_name, h_step, embargo in horizons:
        t_col = f"target_return_{h_name}"
        valid_df = df[df[t_col].notna()].copy().reset_index(drop=True)
        N_tot = len(valid_df)

        X_raw = valid_df[features].values
        y_raw = valid_df[t_col].values
        dates = valid_df["market_date"].values

        # Split boundaries:
        # In-Sample is 0 to oos_start_idx - 1
        # Validation is [oos_start_idx - val_size : oos_start_idx]
        # Train is [0 : oos_start_idx - val_size - h_step - embargo]  <-- PURGED & EMBARGOED!
        train_end = oos_start_idx - val_size - h_step - embargo
        val_start = oos_start_idx - val_size
        val_end = oos_start_idx - h_step - embargo  # Purge before OOS test
        test_start = oos_start_idx

        # Create raw sequences
        seq_X, seq_y = create_sequences(X_raw, y_raw, lookback=lookback)
        seq_dates = dates[lookback - 1 :]

        # Indices in sequence array
        # Sample i in sequence corresponds to raw index i + lookback - 1
        train_mask = (np.arange(len(seq_X)) + lookback - 1) <= train_end
        val_mask = ((np.arange(len(seq_X)) + lookback - 1) >= val_start) & ((np.arange(len(seq_X)) + lookback - 1) <= val_end)
        test_mask = (np.arange(len(seq_X)) + lookback - 1) >= test_start

        X_train_seq = seq_X[train_mask]
        y_train_seq = seq_y[train_mask]

        X_val_seq = seq_X[val_mask]
        y_val_seq = seq_y[val_mask]

        X_test_seq = seq_X[test_mask]
        y_test_seq = seq_y[test_mask]
        test_dates = seq_dates[test_mask]

        # Scaler fit STRICTLY on Training sequences ONLY
        scaler = StandardScaler()
        # Flatten for scaling: (N, L, F) -> (N*L, F)
        N_tr, L_len, F_dim = X_train_seq.shape
        X_train_flat = scaler.fit_transform(X_train_seq.reshape(-1, F_dim))
        X_train_seq = X_train_flat.reshape(N_tr, L_len, F_dim).astype(np.float32)

        N_va = len(X_val_seq)
        X_val_flat = scaler.transform(X_val_seq.reshape(-1, F_dim))
        X_val_seq = X_val_flat.reshape(N_va, L_len, F_dim).astype(np.float32)

        N_te = len(X_test_seq)
        X_test_flat = scaler.transform(X_test_seq.reshape(-1, F_dim))
        X_test_seq = X_test_flat.reshape(N_te, L_len, F_dim).astype(np.float32)

        logger.info(
            "Horizon '%s' (h=%d): Train=%d, Purged Val=%d, OOS Test=%d sequences (Dates: %s to %s)",
            h_name, h_step, len(X_train_seq), len(X_val_seq), len(X_test_seq),
            pd.to_datetime(test_dates[0]).date(), pd.to_datetime(test_dates[-1]).date()
        )

        horizon_preds: dict[str, np.ndarray] = {}
        for m_type in ["RNN", "LSTM"]:
            seed_metrics = []
            seed_preds = []

            for s in seeds:
                ckpt = str(checkpoints_dir / f"{m_type}_{h_name}_seed_{s}.pt")
                pred, audit_t = train_single_deep_model(
                    model_type=m_type,
                    X_train=X_train_seq,
                    y_train=y_train_seq,
                    X_val=X_val_seq,
                    y_val=y_val_seq,
                    X_test=X_test_seq,
                    seed=s,
                    epochs=25,
                    batch_size=32,
                    lr=0.005,
                    checkpoint_path=ckpt,
                )
                m = evaluate_metrics(y_test_seq, pred)
                seed_metrics.append(m)
                seed_preds.append(pred)

            # Ensemble prediction across seeds
            ensemble_pred = np.mean(seed_preds, axis=0)
            ens_metrics = evaluate_metrics(y_test_seq, ensemble_pred)

            # Mean and std across seeds
            rmse_vals = [m["rmse"] for m in seed_metrics]
            mae_vals = [m["mae"] for m in seed_metrics]
            da_vals = [m["da_pct"] for m in seed_metrics]
            mcc_vals = [m["mcc"] for m in seed_metrics]

            summary_item = {
                "horizon": h_name,
                "h_steps": h_step,
                "model_id": m_type,
                "test_sample_size": len(y_test_seq),
                "ensemble_rmse": ens_metrics["rmse"],
                "ensemble_mae": ens_metrics["mae"],
                "ensemble_da_pct": ens_metrics["da_pct"],
                "ensemble_mcc": ens_metrics["mcc"],
                "seed_mean_rmse": float(np.mean(rmse_vals)),
                "seed_std_rmse": float(np.std(rmse_vals)),
                "seed_mean_mae": float(np.mean(mae_vals)),
                "seed_std_mae": float(np.std(mae_vals)),
                "seed_mean_da_pct": float(np.mean(da_vals)),
                "seed_std_da_pct": float(np.std(da_vals)),
                "seed_mean_mcc": float(np.mean(mcc_vals)),
                "seed_std_mcc": float(np.std(mcc_vals)),
            }
            all_summary.append(summary_item)

            horizon_preds[m_type] = ensemble_pred
            # Store predictions for CSV
            key = f"{m_type}_{h_name}"
            predictions_dump[key] = {
                "dates": test_dates,
                "actual": y_test_seq,
                "predicted": ensemble_pred,
            }

            logger.info(
                "%s on %-7s: Ensemble RMSE=%.4f%%, MAE=%.4f%%, DA=%.2f%%, MCC=%.4f (Mean RMSE: %.4f +- %.4f)",
                m_type, h_name, ens_metrics["rmse"], ens_metrics["mae"], ens_metrics["da_pct"], ens_metrics["mcc"],
                np.mean(rmse_vals), np.std(rmse_vals)
            )

        pd.DataFrame({
            "market_date": pd.to_datetime(test_dates),
            "actual_return": y_test_seq.astype(float),
            "pred_return_RNN": horizon_preds["RNN"].astype(float),
            "pred_return_LSTM": horizon_preds["LSTM"].astype(float),
        }).to_csv(p_out / f"oos_predictions_dl_{h_name}.csv", index=False)

    # Save summary
    df_sum = pd.DataFrame(all_summary)
    df_sum.to_csv(p_out / "deep_learning_benchmark_summary.csv", index=False)
    with open(p_out / "deep_learning_benchmark_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_summary, f, indent=2)

    logger.info("Saved Deep Learning Benchmarks to: %s", p_out)
    return {"summary": all_summary, "predictions": predictions_dump}


if __name__ == "__main__":
    run_deep_learning_pipeline()
