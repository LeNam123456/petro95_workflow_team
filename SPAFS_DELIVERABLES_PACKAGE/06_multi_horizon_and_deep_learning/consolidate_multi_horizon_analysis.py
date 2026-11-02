# -*- coding: utf-8 -*-
"""Master Multi-Horizon Consolidation, HAC Pairwise Testing, and Error Analysis Engine for SPAFS V5.2.

Features:
1. Unifies Traditional (M0a..M5) and Deep Learning (RNN, LSTM 5-seed ensemble) OOS predictions.
2. Computes canonical metrics: RMSE, MAE, R2_OOS, DA%, MCC, Pesaran-Timmermann stat and p-value.
3. Implements Clark-West (CW) and Diebold-Mariano (DM) tests with Newey-West HAC bandwidth:
   - Daily: q = 1
   - Weekly: q = 4 (h - 1)
   - Monthly: q = 20 (h - 1)
4. Executes comprehensive Market Shock & Stress Regime Error Analysis:
   - Out-of-Sample Extreme Tail Shock days (|r| >= 3%)
   - Geopolitical shocks (OPEC+ cut Apr 2023, Israel-Hamas war Oct 2023, Red Sea crisis early 2024)
   - High vs Low Volatility regimes
   - Directional error asymmetry under positive vs negative shocks
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import torch
import torch.nn as nn

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.Consolidation")


# --- Model Architectures for Checkpoint Loading ---
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
    n_samples = len(X) - lookback + 1
    seq_x = []
    seq_y = []
    for i in range(n_samples):
        seq_x.append(X[i : i + lookback])
        seq_y.append(y[i + lookback - 1])
    return np.array(seq_x, dtype=np.float32), np.array(seq_y, dtype=np.float32)


# --- Statistical Tests ---
def newey_west_hac_t_test(d: np.ndarray, max_lags: int) -> Tuple[float, float]:
    """Regress d on constant with Newey-West HAC standard error."""
    n = len(d)
    if n < max_lags + 2:
        return 0.0, 1.0
    x = np.ones((n, 1))
    model = sm.OLS(d, x)
    # fit with HAC
    res = model.fit(cov_type="HAC", cov_kwds={"maxlags": max_lags})
    stat = float(res.tvalues[0])
    p_val_one_sided = float(1.0 - stats.norm.cdf(stat))
    p_val_two_sided = float(res.pvalues[0])
    return stat, p_val_one_sided, p_val_two_sided


def clark_west_test(y_true: np.ndarray, y_pred1: np.ndarray, y_pred2: np.ndarray, max_lags: int) -> dict:
    """Clark-West (2007) test for nested models.
    Model 1 is restricted (e.g. M0a, M2, or M4), Model 2 is nested larger (e.g. M2, M4, or M5).
    f_t = (e1_t)^2 - [(e2_t)^2 - (y_hat1_t - y_hat2_t)^2]
    H0: MSPE1 <= MSPE2, H1: MSPE2 < MSPE1 (One-sided).
    """
    e1 = y_true - y_pred1
    e2 = y_true - y_pred2
    f_t = (e1 ** 2) - ((e2 ** 2) - ((y_pred1 - y_pred2) ** 2))
    stat, p_one, p_two = newey_west_hac_t_test(f_t, max_lags=max_lags)
    return {
        "cw_stat": stat,
        "cw_p_value_one_sided": p_one,
        "cw_p_value_two_sided": p_two,
        "mean_adjusted_diff": float(np.mean(f_t)),
        "max_lags_used": max_lags,
    }


def diebold_mariano_test(y_true: np.ndarray, y_pred1: np.ndarray, y_pred2: np.ndarray, max_lags: int) -> dict:
    """Diebold-Mariano (1995) test with Harvey, Leybourne, Newbold (1997) small-sample adjustment.
    d_t = (e1_t)^2 - (e2_t)^2.
    H0: E[d_t] = 0 (Two-sided).
    """
    e1 = y_true - y_pred1
    e2 = y_true - y_pred2
    d = (e1 ** 2) - (e2 ** 2)
    stat, p_one, p_two = newey_west_hac_t_test(d, max_lags=max_lags)
    # HLN correction
    n = len(d)
    h = max(1, max_lags + 1)
    hln_factor = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    hln_stat = stat * hln_factor
    hln_p_two = float(2.0 * (1.0 - stats.t.cdf(abs(hln_stat), df=n - 1)))
    return {
        "dm_stat": stat,
        "dm_p_value_two_sided": p_two,
        "hln_dm_stat": float(hln_stat),
        "hln_p_value_two_sided": hln_p_two,
        "mean_loss_diff": float(np.mean(d)),
        "max_lags_used": max_lags,
    }


def pesaran_timmermann_test(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    yt = (y_true > 0.0).astype(int)
    yp = (y_pred > 0.0).astype(int)
    n = len(yt)
    p = np.mean(yt == yp)
    px = np.mean(yt)
    py = np.mean(yp)
    p_star = px * py + (1 - px) * (1 - py)
    var_p = (p_star * (1 - p_star)) / n
    var_v = (
        (2 * py - 1) ** 2 * (px * (1 - px)) / n
        + (2 * px - 1) ** 2 * (py * (1 - py)) / n
        + 4 * px * py * (1 - px) * (1 - py) / (n ** 2)
    )
    denom = np.sqrt(max(var_v, var_p, 1e-12))
    pt_stat = (p - p_star) / denom
    p_val = float(1.0 - stats.norm.cdf(pt_stat))
    return float(pt_stat), p_val


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_benchmark: np.ndarray = None) -> dict:
    valid = ~np.isnan(y_true) & ~np.isnan(y_pred)
    yt = y_true[valid]
    yp = y_pred[valid]
    n = len(yt)
    e = yt - yp
    rmse = float(np.sqrt(np.mean(e ** 2)))
    mae = float(np.mean(np.abs(e)))

    if y_benchmark is not None:
        yb = y_benchmark[valid]
        mse_m = np.mean(e ** 2)
        mse_b = np.mean((yt - yb) ** 2)
        r2_oos = float((1.0 - (mse_m / mse_b)) * 100.0) if mse_b > 0 else 0.0
    else:
        # Default against sample mean
        mse_m = np.mean(e ** 2)
        mse_b = np.mean((yt - np.mean(yt)) ** 2)
        r2_oos = float((1.0 - (mse_m / mse_b)) * 100.0) if mse_b > 0 else 0.0

    yd = (yt > 0.0).astype(int)
    pd_ = (yp > 0.0).astype(int)
    da = float(np.mean(yd == pd_) * 100.0)

    tp = int(np.sum((yd == 1) & (pd_ == 1)))
    tn = int(np.sum((yd == 0) & (pd_ == 0)))
    fp = int(np.sum((yd == 0) & (pd_ == 1)))
    fn = int(np.sum((yd == 1) & (pd_ == 0)))
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = float((tp * tn - fp * fn) / denom) if denom > 0 else 0.0

    pt_stat, pt_p = pesaran_timmermann_test(yt, yp)
    return {
        "sample_size": n,
        "rmse": rmse,
        "mae": mae,
        "r2_oos_pct": r2_oos,
        "da_pct": da,
        "mcc": mcc,
        "pt_stat": pt_stat,
        "pt_p_value": pt_p,
    }


def main():
    root = Path(".")
    artifacts_dir = root / "artifacts"
    mh_dir = artifacts_dir / "multi_horizon"
    dl_dir = artifacts_dir / "deep_learning"
    ckpts_dir = dl_dir / "checkpoints"
    out_dir = artifacts_dir / "master_consolidation"
    out_dir.mkdir(parents=True, exist_ok=True)

    data_path = root / "data/processed/stream2_multi_horizon_2017_2025.parquet"
    full_df = pd.read_parquet(data_path)
    full_df["market_date"] = pd.to_datetime(full_df["market_date"])
    full_df = full_df.sort_values("market_date").reset_index(drop=True)

    features = [
        "mg95_return_pct", "mg95_return_lag1", "mg95_return_lag2", "mg95_return_lag3",
        "brent_return_pct_aligned", "brent_return_lag1", "brent_return_lag2", "brent_return_lag3",
        "vol_mg95_30d", "economic_shock_flag",
        "spread_mg95_mg92", "spread_mg95_do005", "spread_mg95_brent", "spread_mg95_brent_lag1",
        "octane_spread_nonpositive_flag"
    ]
    for c in features:
        full_df[c] = full_df[c].fillna(0.0)

    horizons_meta = [
        {"name": "daily", "h": 1, "purge": 1, "embargo": 0, "nw_lags": 1, "pred_file": "oos_predictions_daily_h1.csv"},
        {"name": "weekly", "h": 5, "purge": 5, "embargo": 2, "nw_lags": 4, "pred_file": "oos_predictions_weekly_h5.csv"},
        {"name": "monthly", "h": 21, "purge": 21, "embargo": 5, "nw_lags": 20, "pred_file": "oos_predictions_monthly_h21.csv"},
    ]

    master_leaderboard_rows = []
    pairwise_tests_rows = []
    error_analysis_rows = []

    for h_info in horizons_meta:
        h_name = h_info["name"]
        h_step = h_info["h"]
        nw_lags = h_info["nw_lags"]
        p_file = mh_dir / h_info["pred_file"]

        logger.info("Processing Horizon '%s' (h=%d, Newey-West Lags=%d)...", h_name, h_step, nw_lags)
        trad_df = pd.read_csv(p_file)
        trad_df["market_date"] = pd.to_datetime(trad_df["market_date"])

        # Re-generate DL predictions to merge directly into the dataframe
        t_col = f"target_return_{h_name}"
        valid_df = full_df[full_df[t_col].notna()].copy().reset_index(drop=True)
        oos_start_idx = 1500
        val_size = 300
        train_end = oos_start_idx - val_size - h_step - h_info["embargo"]

        seq_X, seq_y = create_sequences(valid_df[features].values, valid_df[t_col].values, lookback=20)
        seq_dates = valid_df["market_date"].values[19:]

        train_mask = (np.arange(len(seq_X)) + 19) <= train_end
        test_mask = (np.arange(len(seq_X)) + 19) >= oos_start_idx

        X_train_seq = seq_X[train_mask]
        X_test_seq = seq_X[test_mask]
        y_test_seq = seq_y[test_mask]
        test_dates = seq_dates[test_mask]

        # Scaler
        scaler = StandardScaler()
        N_tr, L_len, F_dim = X_train_seq.shape
        scaler.fit(X_train_seq.reshape(-1, F_dim))
        N_te = len(X_test_seq)
        X_test_scaled = scaler.transform(X_test_seq.reshape(-1, F_dim)).reshape(N_te, L_len, F_dim).astype(np.float32)

        # Infer RNN & LSTM 5-seed ensembles
        seeds = [42, 101, 202, 303, 404]
        dl_preds = {"RNN": [], "LSTM": []}
        for m_type in ["RNN", "LSTM"]:
            for s in seeds:
                ckpt = ckpts_dir / f"{m_type}_{h_name}_seed_{s}.pt"
                if m_type == "RNN":
                    net = TimeSeriesRNN(in_dim=F_dim, hidden_dim=32, num_layers=1)
                else:
                    net = TimeSeriesLSTM(in_dim=F_dim, hidden_dim=32, num_layers=1)
                net.load_state_dict(torch.load(ckpt, map_location="cpu"))
                net.eval()
                with torch.no_grad():
                    p = net(torch.from_numpy(X_test_scaled)).numpy()
                dl_preds[m_type].append(p)

        rnn_ens = np.mean(dl_preds["RNN"], axis=0)
        lstm_ens = np.mean(dl_preds["LSTM"], axis=0)

        # Merge into unified dataframe
        dl_df = pd.DataFrame({
            "market_date": pd.to_datetime(test_dates),
            "pred_return_RNN": rnn_ens,
            "pred_dir_RNN": (rnn_ens > 0.0).astype(int),
            "residual_RNN": y_test_seq - rnn_ens,
            "pred_return_LSTM": lstm_ens,
            "pred_dir_LSTM": (lstm_ens > 0.0).astype(int),
            "residual_LSTM": y_test_seq - lstm_ens,
        })

        merged_df = pd.merge(trad_df, dl_df, on="market_date", how="inner")
        merged_df.to_csv(out_dir / f"master_oos_predictions_{h_name}.csv", index=False)

        # Compute Leaderboard Metrics for all models
        models = [
            ("M0a", "pred_return_M0a"),
            ("M0b", "pred_return_M0b"),
            ("M1", "pred_return_M1"),
            ("M2", "pred_return_M2"),
            ("M3", "pred_return_M3"),
            ("M4", "pred_return_M4"),
            ("M5", "pred_return_M5"),
            ("RNN", "pred_return_RNN"),
            ("LSTM", "pred_return_LSTM"),
        ]

        actual = merged_df["actual_return"].values
        m0a_pred = merged_df["pred_return_M0a"].values

        for m_id, col_name in models:
            preds = merged_df[col_name].values
            met = compute_metrics(actual, preds, y_benchmark=m0a_pred)
            master_leaderboard_rows.append({
                "horizon": h_name,
                "h_steps": h_step,
                "model_id": m_id,
                "sample_size": met["sample_size"],
                "rmse": met["rmse"],
                "mae": met["mae"],
                "r2_oos_pct": met["r2_oos_pct"] if m_id != "M0a" else 0.0,
                "da_pct": met["da_pct"],
                "mcc": met["mcc"],
                "pt_stat": met["pt_stat"],
                "pt_p_value": met["pt_p_value"],
            })

        # Pairwise Tests
        pairwise_pairs = [
            ("M0a", "M1", "AR(1) vs Constant Mean"),
            ("M0a", "M2", "ADL(1,1) Brent vs Constant Mean"),
            ("M0a", "M4", "LightGBM Core vs Constant Mean"),
            ("M0a", "M5", "LightGBM Full vs Constant Mean"),
            ("M1", "M2", "Brent Alignment Value (M2 vs M1)"),
            ("M2", "M3", "Asymmetry Evidence / Symmetry Test (M3 vs M2)"),
            ("M2", "M4", "Nonlinear Tree vs Linear ADL (M4 vs M2)"),
            ("M4", "M5", "Downstream Spreads Incremental Value (M5 vs M4)"),
            ("M2", "RNN", "RNN vs Linear ADL"),
            ("M2", "LSTM", "LSTM vs Linear ADL"),
            ("M4", "RNN", "RNN vs LightGBM Core"),
            ("M4", "LSTM", "LSTM vs LightGBM Core"),
            ("M5", "RNN", "RNN vs LightGBM Full"),
            ("M5", "LSTM", "LSTM vs LightGBM Full"),
        ]

        for m_base, m_cand, rationale in pairwise_pairs:
            p_base = merged_df[f"pred_return_{m_base}"].values
            p_cand = merged_df[f"pred_return_{m_cand}"].values

            cw = clark_west_test(actual, p_base, p_cand, max_lags=nw_lags)
            dm = diebold_mariano_test(actual, p_base, p_cand, max_lags=nw_lags)

            pairwise_tests_rows.append({
                "horizon": h_name,
                "h_steps": h_step,
                "base_model": m_base,
                "candidate_model": m_cand,
                "comparison_rationale": rationale,
                "nw_lags": nw_lags,
                "cw_stat": cw["cw_stat"],
                "cw_p_value_one_sided": cw["cw_p_value_one_sided"],
                "cw_significant_5pct": bool(cw["cw_p_value_one_sided"] < 0.05),
                "dm_stat": dm["dm_stat"],
                "dm_p_value_two_sided": dm["dm_p_value_two_sided"],
                "hln_dm_stat": dm["hln_dm_stat"],
                "hln_p_value_two_sided": dm["hln_p_value_two_sided"],
                "dm_significant_5pct": bool(dm["dm_p_value_two_sided"] < 0.05),
            })

        # --- Comprehensive Error Analysis on Shocks & Regimes ---
        # 1. Tail Shocks: Absolute return >= 3.0%
        tail_idx = np.abs(actual) >= 3.0
        # 2. Positive Shocks: Actual return >= 2.0%
        pos_shock_idx = actual >= 2.0
        # 3. Negative Shocks: Actual return <= -2.0%
        neg_shock_idx = actual <= -2.0
        # 4. Geopolitical Shock Windows:
        #    - OPEC+ Surprise Cut: 2023-04-02 to 2023-05-15
        #    - Israel-Hamas Outbreak: 2023-10-07 to 2023-11-30
        #    - Red Sea Shipping Disruption: 2023-12-15 to 2024-02-28
        dates_s = merged_df["market_date"]
        opec_idx = (dates_s >= "2023-04-01") & (dates_s <= "2023-05-15")
        gaza_idx = (dates_s >= "2023-10-07") & (dates_s <= "2023-11-30")
        redsea_idx = (dates_s >= "2023-12-15") & (dates_s <= "2024-02-28")

        # Rolling Volatility Regimes (Top 25% Vol vs Bottom 25% Vol)
        # We can extract vol_mg95_30d from full_df
        vol_s = merged_df.merge(full_df[["market_date", "vol_mg95_30d"]], on="market_date", how="left")["vol_mg95_30d"].values
        q75 = np.percentile(vol_s, 75)
        q25 = np.percentile(vol_s, 25)
        high_vol_idx = vol_s >= q75
        low_vol_idx = vol_s <= q25

        regimes = [
            ("Full OOS Sample", np.ones(len(actual), dtype=bool)),
            ("Extreme Tail Shocks (|r| >= 3%)", tail_idx),
            ("Large Upward Moves (r >= +2%)", pos_shock_idx),
            ("Large Downward Moves (r <= -2%)", neg_shock_idx),
            ("OPEC+ Surprise Cut (Apr-May 2023)", opec_idx.values),
            ("Middle East War Escalation (Oct-Nov 2023)", gaza_idx.values),
            ("Red Sea Shipping Crisis (Dec 2023 - Feb 2024)", redsea_idx.values),
            ("High Volatility Regime (Top 25% Vol)", high_vol_idx),
            ("Low Volatility Regime (Bottom 25% Vol)", low_vol_idx),
        ]

        for r_name, r_mask in regimes:
            n_sub = int(np.sum(r_mask))
            if n_sub < 5:
                continue
            sub_y = actual[r_mask]
            for m_id, col_name in [("M0a", "pred_return_M0a"), ("M2", "pred_return_M2"), ("M4", "pred_return_M4"), ("M5", "pred_return_M5"), ("RNN", "pred_return_RNN"), ("LSTM", "pred_return_LSTM")]:
                sub_p = merged_df[col_name].values[r_mask]
                sub_e = sub_y - sub_p
                sub_rmse = float(np.sqrt(np.mean(sub_e ** 2)))
                sub_mae = float(np.mean(np.abs(sub_e)))
                sub_da = float(np.mean((sub_y > 0) == (sub_p > 0)) * 100.0)
                max_err = float(np.max(np.abs(sub_e)))
                error_analysis_rows.append({
                    "horizon": h_name,
                    "h_steps": h_step,
                    "regime": r_name,
                    "subsample_size": n_sub,
                    "model_id": m_id,
                    "rmse": sub_rmse,
                    "mae": sub_mae,
                    "da_pct": sub_da,
                    "max_abs_error": max_err,
                })

    # Save Master Leaderboard
    df_master = pd.DataFrame(master_leaderboard_rows)
    df_master.to_csv(out_dir / "master_multi_horizon_leaderboard.csv", index=False)

    # Save Pairwise Tests
    df_pairs = pd.DataFrame(pairwise_tests_rows)
    df_pairs.to_csv(out_dir / "master_pairwise_hac_tests.csv", index=False)

    # Save Error Analysis
    df_err = pd.DataFrame(error_analysis_rows)
    df_err.to_csv(out_dir / "master_shock_error_analysis.csv", index=False)

    logger.info("Master Multi-Horizon Analysis completed successfully! Files written to %s", out_dir)


if __name__ == "__main__":
    main()
