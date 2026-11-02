# -*- coding: utf-8 -*-
"""Multi-Horizon Walk-Forward Forecasting Engine for Traditional Models (M0a to M5).

Executes Expanding Walk-Forward evaluation for:
- Daily: h=1 (Purge = 1 session)
- Weekly: h=5 (Purge = 5 sessions, Embargo = 2 sessions)
- Monthly: h=21 (Purge = 21 sessions, Embargo = 5 sessions)

Strictly enforces Zero-Leakage Purging:
    At forecast origin tau, training samples are strictly restricted to:
        t <= tau - h - Embargo
    ensuring no future prices or overlapping target windows leak into training.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.MultiHorizonRunner")


def compute_directional_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    valid = ~np.isnan(yt) & ~np.isnan(yp)
    yt, yp = yt[valid], yp[valid]
    n = len(yt)

    y_dir = (yt > 0.0).astype(int)
    p_dir = (yp > 0.0).astype(int)

    da = float(np.mean(y_dir == p_dir) * 100.0)

    # MCC
    tp = int(np.sum((y_dir == 1) & (p_dir == 1)))
    tn = int(np.sum((y_dir == 0) & (p_dir == 0)))
    fp = int(np.sum((y_dir == 0) & (p_dir == 1)))
    fn = int(np.sum((y_dir == 1) & (p_dir == 0)))
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = float((tp * tn - fp * fn) / denom) if denom > 0 else 0.0

    # Pesaran-Timmermann
    p_hat = float(np.mean(y_dir == p_dir))
    py = float(np.mean(y_dir))
    py_hat = float(np.mean(p_dir))
    p_star = py * py_hat + (1.0 - py) * (1.0 - py_hat)
    v_hat = (p_star * (1.0 - p_star)) / n
    v_star = (
        (2.0 * py_hat - 1.0) ** 2 * (py * (1.0 - py)) / n
        + (2.0 * py - 1.0) ** 2 * (py_hat * (1.0 - py_hat)) / n
        + 4.0 * py * py_hat * (1.0 - py) * (1.0 - py_hat) / (n**2)
    )
    denom_pt = np.sqrt(max(1e-12, v_hat - v_star))
    pt_stat = float((p_hat - p_star) / denom_pt)
    pt_pval = float(1.0 - stats.norm.cdf(pt_stat))

    return {
        "directional_accuracy_pct": da,
        "mcc": mcc,
        "pt_stat": pt_stat,
        "pt_p_value": pt_pval,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def fit_predict_lgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    seeds: list[int] = (42, 101, 202, 303, 404, 505, 606, 707, 808, 909),
    params: dict = None,
) -> float:
    if params is None:
        params = {
            "objective": "regression",
            "metric": "rmse",
            "learning_rate": 0.03,
            "num_leaves": 15,
            "min_child_samples": 20,
            "n_estimators": 100,
            "subsample": 0.8,
            "subsample_freq": 1,
            "colsample_bytree": 0.8,
            "verbose": -1,
            "n_jobs": 1,
        }

    preds = []
    for s in seeds:
        p = params.copy()
        p["random_state"] = s
        reg = lgb.LGBMRegressor(**p)
        reg.fit(X_train, y_train)
        pred = reg.predict(X_test)[0]
        preds.append(pred)
    return float(np.mean(preds))


def run_walk_forward_horizon(
    df: pd.DataFrame,
    horizon_name: str = "daily",
    h: int = 1,
    embargo: int = 0,
    warmup: int = 1500,
    refit_every: int = 20,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    target_col = f"target_return_{horizon_name}"
    valid_sub = df[df[target_col].notna()].copy().reset_index(drop=True)
    T = len(valid_sub)

    # Feature definitions
    m4_cols = [
        "mg95_return_pct", "mg95_return_lag1", "mg95_return_lag2", "mg95_return_lag3",
        "brent_return_pct_aligned", "brent_return_lag1", "brent_return_lag2", "brent_return_lag3",
        "vol_mg95_30d", "economic_shock_flag"
    ]
    m5_cols = m4_cols + [
        "spread_mg95_mg92", "spread_mg95_do005", "spread_mg95_brent", "spread_mg95_brent_lag1",
        "octane_spread_nonpositive_flag"
    ]
    m2_cols = ["mg95_return_pct", "mg95_return_lag1", "brent_return_pct_aligned", "brent_return_lag1", "spread_mg95_brent_lag1"]
    m3_cols = ["mg95_return_pct", "mg95_return_lag1", "brent_return_pos", "brent_return_neg", "brent_return_pos_lag1", "brent_return_neg_lag1", "spread_mg95_brent_lag1"]

    # Fill NaNs in features with 0.0
    for c in set(m5_cols + m3_cols):
        valid_sub[c] = valid_sub[c].fillna(0.0)

    # OOS index: warmup to T
    oos_dates = []
    actuals = []
    pred_m0a, pred_m0b, pred_m1, pred_m2, pred_m3, pred_m4, pred_m5 = [], [], [], [], [], [], []

    cached_m4_models = None
    cached_m5_models = None
    cached_m2_beta = None
    cached_m3_beta = None

    logger.info("Executing Walk-Forward for Horizon '%s' (h=%d, Purge=%d, Embargo=%d, T=%d, Warmup=%d)...",
                horizon_name, h, h, embargo, T, warmup)

    for tau in range(warmup, T):
        # Current forecast origin date
        cur_date = valid_sub.loc[tau, "market_date"]
        y_test_val = float(valid_sub.loc[tau, target_col])

        # Purging & Embargo rule:
        # We can only use training observations where label was realized on or before tau:
        # t + h <= tau <=> t <= tau - h - embargo
        train_end = tau - h - embargo
        if train_end < 50:
            # Need minimum training points
            train_end = 50

        # Refit models if needed
        is_refit = (cached_m4_models is None) or ((tau - warmup) % refit_every == 0)

        if is_refit:
            X_m4_train = valid_sub.loc[:train_end, m4_cols].values
            X_m5_train = valid_sub.loc[:train_end, m5_cols].values
            y_train = valid_sub.loc[:train_end, target_col].values

            # Fit M4 (10 seeds)
            cached_m4_models = []
            for s in [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]:
                m = lgb.LGBMRegressor(
                    objective="regression", metric="rmse", learning_rate=0.03, num_leaves=15,
                    min_child_samples=20, n_estimators=100, subsample=0.8, subsample_freq=1,
                    colsample_bytree=0.8, random_state=s, verbose=-1, n_jobs=1
                )
                m.fit(X_m4_train, y_train)
                cached_m4_models.append(m)

            # Fit M5 (10 seeds)
            cached_m5_models = []
            for s in [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]:
                m = lgb.LGBMRegressor(
                    objective="regression", metric="rmse", learning_rate=0.03, num_leaves=15,
                    min_child_samples=20, n_estimators=100, subsample=0.8, subsample_freq=1,
                    colsample_bytree=0.8, random_state=s, verbose=-1, n_jobs=1
                )
                m.fit(X_m5_train, y_train)
                cached_m5_models.append(m)

            # Fit M2 (OLS Linear Dynamic)
            X_m2_train = sm.add_constant(valid_sub.loc[:train_end, m2_cols].values, has_constant="add")
            try:
                res_m2 = sm.OLS(y_train, X_m2_train).fit()
                cached_m2_beta = res_m2.params
            except Exception:
                cached_m2_beta = np.zeros(X_m2_train.shape[1])

            # Fit M3 (OLS Asymmetric ADL)
            X_m3_train = sm.add_constant(valid_sub.loc[:train_end, m3_cols].values, has_constant="add")
            try:
                res_m3 = sm.OLS(y_train, X_m3_train).fit()
                cached_m3_beta = res_m3.params
            except Exception:
                cached_m3_beta = np.zeros(X_m3_train.shape[1])

        # Predict for origin tau
        # M0a: 0.0
        p_0a = 0.0

        # M0b: persistence return from previous realized window
        prev_idx = max(0, tau - h)
        p_0b = float(valid_sub.loc[prev_idx, target_col]) if prev_idx < len(valid_sub) else 0.0

        # M1: AR(1) on historical target returns
        p_1 = float(valid_sub.loc[:train_end, target_col].mean())

        # M2
        x_m2_test = np.hstack([[1.0], valid_sub.loc[tau, m2_cols].values])
        p_2 = float(np.dot(x_m2_test, cached_m2_beta))

        # M3
        x_m3_test = np.hstack([[1.0], valid_sub.loc[tau, m3_cols].values])
        p_3 = float(np.dot(x_m3_test, cached_m3_beta))

        # M4
        x_m4_test = valid_sub.loc[tau:tau, m4_cols].values
        p_4 = float(np.mean([m.predict(x_m4_test)[0] for m in cached_m4_models]))

        # M5
        x_m5_test = valid_sub.loc[tau:tau, m5_cols].values
        p_5 = float(np.mean([m.predict(x_m5_test)[0] for m in cached_m5_models]))

        oos_dates.append(cur_date)
        actuals.append(y_test_val)
        pred_m0a.append(p_0a)
        pred_m0b.append(p_0b)
        pred_m1.append(p_1)
        pred_m2.append(p_2)
        pred_m3.append(p_3)
        pred_m4.append(p_4)
        pred_m5.append(p_5)

    df_oos = pd.DataFrame({
        "market_date": oos_dates,
        "actual_return": actuals,
        "actual_direction": (np.array(actuals) > 0.0).astype(int),
        "pred_return_M0a": pred_m0a,
        "pred_dir_M0a": (np.array(pred_m0a) > 0.0).astype(int),
        "residual_M0a": np.array(actuals) - np.array(pred_m0a),
        "pred_return_M0b": pred_m0b,
        "pred_dir_M0b": (np.array(pred_m0b) > 0.0).astype(int),
        "residual_M0b": np.array(actuals) - np.array(pred_m0b),
        "pred_return_M1": pred_m1,
        "pred_dir_M1": (np.array(pred_m1) > 0.0).astype(int),
        "residual_M1": np.array(actuals) - np.array(pred_m1),
        "pred_return_M2": pred_m2,
        "pred_dir_M2": (np.array(pred_m2) > 0.0).astype(int),
        "residual_M2": np.array(actuals) - np.array(pred_m2),
        "pred_return_M3": pred_m3,
        "pred_dir_M3": (np.array(pred_m3) > 0.0).astype(int),
        "residual_M3": np.array(actuals) - np.array(pred_m3),
        "pred_return_M4": pred_m4,
        "pred_dir_M4": (np.array(pred_m4) > 0.0).astype(int),
        "residual_M4": np.array(actuals) - np.array(pred_m4),
        "pred_return_M5": pred_m5,
        "pred_dir_M5": (np.array(pred_m5) > 0.0).astype(int),
        "residual_M5": np.array(actuals) - np.array(pred_m5),
    })

    # Metrics Leaderboard for this horizon
    models_list = ["M0a", "M0b", "M1", "M2", "M3", "M4", "M5"]
    leaderboard = []
    yt_arr = df_oos["actual_return"].values
    mse_m0a = float(np.mean(yt_arr**2))

    for m in models_list:
        yp_arr = df_oos[f"pred_return_{m}"].values
        e = yt_arr - yp_arr
        rmse = float(np.sqrt(np.mean(e**2)))
        mae = float(np.mean(np.abs(e)))
        r2_oos = float(1.0 - (rmse**2) / mse_m0a) * 100.0 if mse_m0a > 0 else 0.0
        d_metrics = compute_directional_metrics(yt_arr, yp_arr)

        leaderboard.append({
            "horizon": horizon_name,
            "h_steps": h,
            "model_id": m,
            "sample_size": len(df_oos),
            "rmse": rmse,
            "mae": mae,
            "r2_oos_pct": r2_oos,
            "da_pct": d_metrics["directional_accuracy_pct"],
            "mcc": d_metrics["mcc"],
            "pt_stat": d_metrics["pt_stat"],
            "pt_p_value": d_metrics["pt_p_value"],
        })

    logger.info("Completed Horizon '%s': N_OOS = %d rows (from %s to %s)",
                horizon_name, len(df_oos), df_oos["market_date"].iloc[0].date(), df_oos["market_date"].iloc[-1].date())

    return df_oos, {"horizon": horizon_name, "h": h, "leaderboard": leaderboard}


def run_all_three_horizons(
    data_path: str = "data/processed/stream2_multi_horizon_2017_2025.parquet",
    output_dir: str = "artifacts/multi_horizon",
) -> None:
    p_out = Path(output_dir)
    p_out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(data_path)
    df["market_date"] = pd.to_datetime(df["market_date"])
    df = df.sort_values("market_date").reset_index(drop=True)

    # Daily: h=1, embargo=0
    df_daily, audit_daily = run_walk_forward_horizon(df, "daily", h=1, embargo=0, warmup=1500, refit_every=20)
    df_daily.to_csv(p_out / "oos_predictions_daily_h1.csv", index=False)

    # Weekly: h=5, embargo=2
    df_weekly, audit_weekly = run_walk_forward_horizon(df, "weekly", h=5, embargo=2, warmup=1500, refit_every=20)
    df_weekly.to_csv(p_out / "oos_predictions_weekly_h5.csv", index=False)

    # Monthly: h=21, embargo=5
    df_monthly, audit_monthly = run_walk_forward_horizon(df, "monthly", h=21, embargo=5, warmup=1500, refit_every=20)
    df_monthly.to_csv(p_out / "oos_predictions_monthly_h21.csv", index=False)

    # Combine Leaderboard
    all_leaderboard = audit_daily["leaderboard"] + audit_weekly["leaderboard"] + audit_monthly["leaderboard"]
    df_lead = pd.DataFrame(all_leaderboard)
    df_lead.to_csv(p_out / "multi_horizon_traditional_leaderboard.csv", index=False)
    with open(p_out / "multi_horizon_traditional_leaderboard.json", "w", encoding="utf-8") as f:
        json.dump(all_leaderboard, f, indent=2)

    logger.info("Saved all Multi-Horizon Traditional Model outputs to: %s", p_out)
    print("\n" + df_lead.to_string(index=False))


if __name__ == "__main__":
    run_all_three_horizons()
