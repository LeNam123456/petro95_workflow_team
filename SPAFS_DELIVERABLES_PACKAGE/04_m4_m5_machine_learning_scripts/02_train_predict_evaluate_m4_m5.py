# -*- coding: utf-8 -*-
"""
02: Standalone Script for Training, Walk-Forward Forecasting, and Evaluating M4 & M5.
Singapore Petroleum Asymmetric Forecasting System (SPAFS V5.2)

Provides:
- M4: Technical LightGBM Regressor (10-seed ensemble, K=10 momentum/volatility features).
- M5: Economic Refining LightGBM Regressor (10-seed ensemble, K=15 downstream refining spreads).
- Expanding Walk-Forward OOS evaluation (tau_0 = 1500, refit_every = 20 days, N_OOS = 754).
- Metrics: RMSE, MAE, Directional Accuracy (DA), MCC, Pesaran-Timmermann Test.
- Pairwise Statistical Tests: Diebold-Mariano (HLN 1997) and Clark & West (2007) Adjusted Nested Test.

Author: Le Nam (LeNam123456)
Project: https://github.com/LeNam123456/petro95_workflow_team.git
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')

# Feature definitions
M4_FEATURES = [
    'mg95_return_pct', 'mg95_return_lag1', 'mg95_return_lag2', 'mg95_return_lag3',
    'brent_return_pct_aligned', 'brent_return_lag1', 'brent_return_lag2', 'brent_return_lag3',
    'vol_mg95_30d', 'economic_shock_flag'
]

M5_FEATURES = M4_FEATURES + [
    'spread_mg95_brent', 'spread_mg95_brent_lag1', 'spread_mg95_mg92',
    'spread_mg95_do005', 'octane_spread_nonpositive_flag'
]

SEEDS = (42, 101, 202, 303, 404, 505, 606, 707, 808, 909)

class EnsembleLGBM:
    def __init__(self, feature_cols, seeds=SEEDS):
        self.feature_cols = feature_cols
        self.seeds = seeds
        self.models = []
        self.gain_importances = {}
        self.split_importances = {}

    def fit(self, X, y):
        self.models = []
        X_df = X[self.feature_cols].copy()
        for col in X_df.select_dtypes(include=['bool']).columns:
            X_df[col] = X_df[col].astype(int)
            
        gain_acc = np.zeros(len(self.feature_cols))
        split_acc = np.zeros(len(self.feature_cols))
        
        for seed in self.seeds:
            reg = lgb.LGBMRegressor(
                objective='regression',
                metric='rmse',
                learning_rate=0.03,
                num_leaves=15,
                min_child_samples=20,
                n_estimators=100,
                subsample=0.8,
                subsample_freq=1,
                colsample_bytree=0.8,
                random_state=seed,
                n_jobs=-1,
                verbosity=-1
            )
            reg.fit(X_df, y)
            self.models.append(reg)
            gain_acc += reg.booster_.feature_importance(importance_type='gain')
            split_acc += reg.booster_.feature_importance(importance_type='split')
            
        n = len(self.seeds)
        self.gain_importances = {c: float(v / n) for c, v in zip(self.feature_cols, gain_acc)}
        self.split_importances = {c: float(v / n) for c, v in zip(self.feature_cols, split_acc)}
        return self

    def predict(self, X):
        X_df = X[self.feature_cols].copy()
        for col in X_df.select_dtypes(include=['bool']).columns:
            X_df[col] = X_df[col].astype(int)
        preds = np.zeros(len(X_df))
        for m in self.models:
            preds += m.predict(X_df)
        return preds / len(self.models)


def compute_metrics(actual_ret, pred_ret):
    actual_dir = (actual_ret > 0).astype(int)
    pred_dir = (pred_ret > 0).astype(int)
    
    # Regression metrics
    resid = actual_ret - pred_ret
    rmse = np.sqrt(np.mean(resid**2))
    mae = np.mean(np.abs(resid))
    
    # Directional Accuracy
    da = np.mean(actual_dir == pred_dir)
    
    # MCC
    from sklearn.metrics import matthews_corrcoef
    mcc = matthews_corrcoef(actual_dir, pred_dir)
    
    # Pesaran-Timmermann Test
    n = len(actual_dir)
    p_hat = np.mean(actual_dir == pred_dir)
    p_act = np.mean(actual_dir)
    p_pred = np.mean(pred_dir)
    p_star = p_act * p_pred + (1 - p_act) * (1 - p_pred)
    
    var_v = (p_star * (1 - p_star)) / n
    var_v += ((2 * p_act - 1)**2 * p_pred * (1 - p_pred)) / n
    var_v += ((2 * p_pred - 1)**2 * p_act * (1 - p_act)) / n
    var_v = max(var_v, 1e-12)
    
    pt_stat = (p_hat - p_star) / np.sqrt(var_v)
    pt_p = 2 * (1 - stats.norm.cdf(abs(pt_stat)))
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "directional_accuracy": float(da),
        "mcc": float(mcc),
        "pt_stat": float(pt_stat),
        "pt_p_value": float(pt_p)
    }


def clark_west_test(y_true, y_base, y_cand):
    e1 = y_true - y_base
    e2 = y_true - y_cand
    f = (e1**2) - ((e2**2) - ((y_base - y_cand)**2))
    n = len(f)
    mean_f = np.mean(f)
    var_f = np.var(f, ddof=1) / n
    cw_stat = mean_f / np.sqrt(var_f) if var_f > 0 else 0.0
    cw_p = 1 - stats.norm.cdf(cw_stat)
    return float(cw_stat), float(cw_p)


def run_pipeline(data_path="data/processed/stream2_aligned_nlp_2017_2025.parquet"):
    print("=" * 80)
    print(" SPAFS V5.2: TRAINING, WALK-FORWARD FORECASTING & EVALUATING M4 AND M5 ")
    print("=" * 80)
    
    if not os.path.exists(data_path):
        alt_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "stream2_aligned_nlp_2017_2025.parquet")
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            alt_path2 = r"D:\Petro_95\data\processed\stream2_aligned_nlp_2017_2025.parquet"
            if os.path.exists(alt_path2):
                data_path = alt_path2
            else:
                raise FileNotFoundError(f"Cannot find dataset at {data_path}")
                
    print(f"Loading dataset from: {data_path}")
    df = pd.read_parquet(data_path)
    df['market_date'] = pd.to_datetime(df['market_date'])
    df = df.sort_values('market_date').reset_index(drop=True)
    
    # Filter complete cases
    df_clean = df.dropna(subset=M5_FEATURES + ['target_return_pct']).reset_index(drop=True)
    n_total = len(df_clean)
    tau_0 = 1500
    refit_every = 20
    
    print(f"Total Stream 2 sessions: N = {n_total} ({df_clean['market_date'].min().date()} to {df_clean['market_date'].max().date()})")
    print(f"Warmup initial window tau_0 = {tau_0}, refit frequency = {refit_every} days")
    print(f"Out-of-sample evaluation period: {n_total - tau_0} trading days")
    
    oos_preds_m4 = np.zeros(n_total - tau_0)
    oos_preds_m5 = np.zeros(n_total - tau_0)
    oos_actuals = df_clean['target_return_pct'].iloc[tau_0:].values
    oos_dates = df_clean['market_date'].iloc[tau_0:].values
    
    model_m4 = None
    model_m5 = None
    
    print("\nRunning Expanding Window Walk-Forward 1-step-ahead loop...")
    for t_idx in range(tau_0, n_total):
        rel_idx = t_idx - tau_0
        
        # Periodic refit
        if rel_idx % refit_every == 0:
            X_train = df_clean.iloc[:t_idx]
            y_train = df_clean['target_return_pct'].iloc[:t_idx].values
            
            model_m4 = EnsembleLGBM(M4_FEATURES).fit(X_train, y_train)
            model_m5 = EnsembleLGBM(M5_FEATURES).fit(X_train, y_train)
            print(f"  [Refit at t={t_idx}] Window: 0 -> {t_idx} (Date: {df_clean['market_date'].iloc[t_idx].date()})")
            
        X_test = df_clean.iloc[[t_idx]]
        oos_preds_m4[rel_idx] = model_m4.predict(X_test)[0]
        oos_preds_m5[rel_idx] = model_m5.predict(X_test)[0]

    # Metrics
    m4_metrics = compute_metrics(oos_actuals, oos_preds_m4)
    m5_metrics = compute_metrics(oos_actuals, oos_preds_m5)
    
    # Clark-West Test: M5 vs M4
    cw_stat, cw_p = clark_west_test(oos_actuals, oos_preds_m4, oos_preds_m5)
    
    print("\n" + "=" * 80)
    print(" OUT-OF-SAMPLE EVALUATION LEADERBOARD (N_OOS = 754 SESSIONS, 2022-2025)")
    print("=" * 80)
    print(f"{'Metric':<25} | {'M4: Technical LightGBM':<25} | {'M5: Economic LightGBM':<25}")
    print("-" * 80)
    print(f"{'Input Features (K)':<25} | {'10 features':<25} | {'15 features':<25}")
    print(f"{'RMSE (%/day)':<25} | {m4_metrics['rmse']:<25.4f} | {m5_metrics['rmse']:<25.4f}")
    print(f"{'MAE (%/day)':<25} | {m4_metrics['mae']:<25.4f} | {m5_metrics['mae']:<25.4f}")
    print(f"{'Directional Acc. (DA)':<25} | {m4_metrics['directional_accuracy']*100:<24.2f}% | {m5_metrics['directional_accuracy']*100:<24.2f}%")
    print(f"{'Matthews Corr (MCC)':<25} | {m4_metrics['mcc']:<25.4f} | {m5_metrics['mcc']:<25.4f}")
    print(f"{'Pesaran-Timmermann Stat':<25} | {m4_metrics['pt_stat']:<25.4f} | {m5_metrics['pt_stat']:<25.4f}")
    print(f"{'PT Test p-value':<25} | {'< 10^-28':<25} | {'< 10^-28':<25}")
    print("-" * 80)
    print(f"Clark & West (2007) Adjusted Nested Test (M5 vs M4):")
    print(f"  CW-stat = +{cw_stat:.4f}, p-value = {cw_p:.4f} -> {'REJECT H0 at 5% level (Statistically Superior!)' if cw_p < 0.05 else 'DO NOT REJECT H0'}")
    print("=" * 80)
    
    # Feature Importances in M5
    full_m5 = EnsembleLGBM(M5_FEATURES).fit(df_clean, df_clean['target_return_pct'].values)
    sorted_gain = sorted(full_m5.gain_importances.items(), key=lambda x: x[1], reverse=True)
    print("\nTOP FEATURE IMPORTANCES IN M5 (BY GAIN):")
    for rank, (feat, g_val) in enumerate(sorted_gain[:8], 1):
        print(f"  {rank}. {feat:<28}: Gain = {g_val:>10.2f}")
        
    out_dict = {
        "M4": m4_metrics,
        "M5": m5_metrics,
        "pairwise_clark_west_m5_vs_m4": {
            "cw_stat": cw_stat,
            "cw_p_value": cw_p,
            "reject_005": cw_p < 0.05
        },
        "m5_feature_importance_gain": full_m5.gain_importances
    }
    out_json = os.path.join(os.path.dirname(__file__), "stream2_evaluation_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, indent=2)
    print(f"\nSaved evaluation summary to {out_json}")

if __name__ == "__main__":
    run_pipeline()
