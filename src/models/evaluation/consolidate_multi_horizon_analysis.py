# -*- coding: utf-8 -*-
"""Master Multi-Horizon Consolidation, HAC Pairwise Testing, and Error Analysis Engine for SPAFS V5.2.

Features:
1. Unifies Traditional (M0a..M5, artifacts/multi_horizon) and Deep Learning (RNN, LSTM
   5-seed ensembles, artifacts/deep_learning/oos_predictions_dl_*.csv) OOS predictions.
2. Metrics and tests come exclusively from src.models.evaluation.forecast_tests
   (RMSE, MAE, R2_OOS vs M0a, DA%, MCC, Pesaran-Timmermann; DM-HLN and Clark-West with
   h-1 HAC lags: daily 0, weekly 4, monthly 20). Clark-West is reported for nested pairs only.
4. Executes comprehensive Market Shock & Stress Regime Error Analysis:
   - Out-of-Sample Extreme Tail Shock days (|r| >= 3%)
   - Geopolitical shocks (OPEC+ cut Apr 2023, Israel-Hamas war Oct 2023, Red Sea crisis early 2024)
   - High vs Low Volatility regimes
   - Directional error asymmetry under positive vs negative shocks
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.evaluation.forecast_tests import cw_test, dm_test, forecast_metrics

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.Consolidation")

HORIZONS = [
    {"name": "daily", "h": 1, "embargo": 0},
    {"name": "weekly", "h": 5, "embargo": 2},
    {"name": "monthly", "h": 21, "embargo": 5},
]
MODELS = ["M0a", "M0b", "M1", "M2", "M3", "M4", "M5", "RNN", "LSTM"]
# (benchmark, candidate, rationale, nested?) -- Clark-West is only reported for nested pairs.
PAIRWISE_PAIRS = [
    ("M0a", "M1", "ARMA(1,1) vs Zero Forecast", True),
    ("M0a", "M2", "ADL Brent vs Zero Forecast", True),
    ("M0a", "M4", "LightGBM Core vs Zero Forecast", True),
    ("M0a", "M5", "LightGBM Full vs Zero Forecast", True),
    ("M1", "M2", "Brent Alignment Value (M2 vs M1)", False),
    ("M2", "M3", "Asymmetry Evidence (M3 vs M2)", True),
    ("M2", "M4", "Nonlinear Tree vs Linear ADL (M4 vs M2)", False),
    ("M4", "M5", "Downstream Spreads Incremental Value (M5 vs M4)", True),
    ("M2", "RNN", "RNN vs Linear ADL", False),
    ("M2", "LSTM", "LSTM vs Linear ADL", False),
    ("M4", "RNN", "RNN vs LightGBM Core", False),
    ("M4", "LSTM", "LSTM vs LightGBM Core", False),
    ("M5", "RNN", "RNN vs LightGBM Full", False),
    ("M5", "LSTM", "LSTM vs LightGBM Full", False),
]


def main():
    root = Path(".")
    artifacts_dir = root / "artifacts"
    mh_dir = artifacts_dir / "multi_horizon"
    dl_dir = artifacts_dir / "deep_learning"
    out_dir = artifacts_dir / "master_consolidation"
    out_dir.mkdir(parents=True, exist_ok=True)

    full_df = pd.read_parquet(root / "data/processed/stream2_multi_horizon_2017_2025.parquet")
    full_df["market_date"] = pd.to_datetime(full_df["market_date"])

    master_leaderboard_rows = []
    pairwise_tests_rows = []
    error_analysis_rows = []

    for h_info in HORIZONS:
        h_name, h_step = h_info["name"], h_info["h"]
        logger.info("Processing horizon '%s' (h=%d, HAC lags=%d)...", h_name, h_step, h_step - 1)
        trad_df = pd.read_csv(mh_dir / f"oos_predictions_{h_name}_h{h_step}.csv", parse_dates=["market_date"])
        dl_df = pd.read_csv(dl_dir / f"oos_predictions_dl_{h_name}.csv", parse_dates=["market_date"])

        merged_df = pd.merge(trad_df, dl_df.drop(columns=["actual_return"]), on="market_date", how="inner")
        if len(merged_df) != len(trad_df) or len(merged_df) != len(dl_df):
            raise ValueError(f"OOS windows of traditional and DL models differ for '{h_name}'.")
        chk = np.abs(trad_df.set_index("market_date")["actual_return"]
                     - dl_df.set_index("market_date")["actual_return"]).max()
        if chk > 1e-4:
            raise ValueError(f"Actual returns disagree between traditional and DL files ({chk}).")
        for m in ("RNN", "LSTM"):
            merged_df[f"pred_dir_{m}"] = (merged_df[f"pred_return_{m}"] > 0).astype(int)
            merged_df[f"residual_{m}"] = merged_df["actual_return"] - merged_df[f"pred_return_{m}"]
        merged_df.to_csv(out_dir / f"master_oos_predictions_{h_name}.csv", index=False)

        actual = merged_df["actual_return"].to_numpy()
        m0a_pred = merged_df["pred_return_M0a"].to_numpy()

        for m_id in MODELS:
            met = forecast_metrics(actual, merged_df[f"pred_return_{m_id}"].to_numpy(), benchmark=m0a_pred, horizon=h_step)
            master_leaderboard_rows.append({"horizon": h_name, "h_steps": h_step, "model_id": m_id, **met})

        for m_base, m_cand, rationale, nested in PAIRWISE_PAIRS:
            p_base = merged_df[f"pred_return_{m_base}"].to_numpy()
            p_cand = merged_df[f"pred_return_{m_cand}"].to_numpy()
            dm = dm_test(actual, p_cand, p_base, loss="squared", horizon=h_step,
                         candidate_id=m_cand, benchmark_id=m_base)
            row = {
                "horizon": h_name,
                "h_steps": h_step,
                "base_model": m_base,
                "candidate_model": m_cand,
                "comparison_rationale": rationale,
                "nested": nested,
                "hac_lags": dm.hac_lags,
                "dm_hln_stat": dm.statistic,
                "dm_p_value_one_sided": dm.p_value_one_sided,
                "dm_p_value_two_sided": dm.p_value_two_sided,
                "dm_variance_kernel": dm.details["variance_kernel"],
                "dm_candidate_better_5pct": dm.reject_at(0.05),
                "cw_stat": np.nan,
                "cw_p_value_one_sided": np.nan,
                "cw_significant_5pct": False,
            }
            if nested:
                cw = cw_test(actual, p_cand, p_base, horizon=h_step, candidate_id=m_cand, benchmark_id=m_base)
                row.update(cw_stat=cw.statistic, cw_p_value_one_sided=cw.p_value_one_sided,
                           cw_significant_5pct=cw.reject_at(0.05))
            pairwise_tests_rows.append(row)

        # --- Error analysis on shocks & regimes ---
        # Return thresholds scale with sqrt(h) so that h-step cumulative returns are
        # compared on the same volatility footing as daily ones (3% / 2% at h=1).
        # Event windows are selected by forecast-origin date.
        scale = float(np.sqrt(h_step))
        tail_thr, move_thr = 3.0 * scale, 2.0 * scale
        tail_idx = np.abs(actual) >= tail_thr
        pos_shock_idx = actual >= move_thr
        neg_shock_idx = actual <= -move_thr
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
            (f"Extreme Tail Shocks (|r| >= {tail_thr:.1f}%)", tail_idx),
            (f"Large Upward Moves (r >= +{move_thr:.1f}%)", pos_shock_idx),
            (f"Large Downward Moves (r <= -{move_thr:.1f}%)", neg_shock_idx),
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
