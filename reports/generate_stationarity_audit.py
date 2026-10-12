"""Generate formal Stationarity & Unit Root Audit Report for SPAFS V5.2."""

import json
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

warnings.filterwarnings("ignore")

# Load full processed panel
df = pd.read_parquet("data/processed/spafs_full_features_daily.parquet")

features_to_audit = [
    "target_return_pct",
    "target_direction",
    "mg95_return_pct",
    "mg95_return_lag1",
    "mg95_return_lag2",
    "mg95_return_lag3",
    "brent_return_pct_aligned",
    "brent_return_lag1",
    "brent_return_lag2",
    "brent_return_lag3",
    "brent_return_pos",
    "brent_return_neg",
    "brent_return_pos_lag1",
    "brent_return_neg_lag1",
    "spread_mg95_brent_lag1",
    "vol_mg95_30d",
    "economic_shock_flag",
    "spread_mg95_mg92",
    "spread_mg95_do005",
    "spread_mg95_brent",
    "octane_spread_nonpositive_flag",
]

audit_rows = []

for feat in features_to_audit:
    if feat not in df.columns:
        continue
    series = df[feat].dropna()
    if len(series) < 50:
        continue

    # Binary flags: stationarity is trivially bounded, but we can compute ADF
    is_binary = set(series.unique()).issubset({0, 1, 0.0, 1.0})

    try:
        adf_res = adfuller(series, autolag="AIC")
        adf_stat = float(adf_res[0])
        adf_p = float(adf_res[1])
        adf_crit_5pct = float(adf_res[4]["5%"])
    except Exception:
        adf_stat, adf_p, adf_crit_5pct = np.nan, np.nan, np.nan

    try:
        kpss_res = kpss(series, regression="c", nlags="auto")
        kpss_stat = float(kpss_res[0])
        kpss_p = float(kpss_res[1])
        kpss_crit_5pct = float(kpss_res[3]["5%"])
    except Exception:
        kpss_stat, kpss_p, kpss_crit_5pct = np.nan, np.nan, np.nan

    # Conclusion categorization
    # ADF H0: Has unit root (non-stationary). Rejecting (p < 0.05) -> Stationary
    # KPSS H0: Is stationary. Rejecting (p < 0.05) -> Non-stationary / Structural shift
    if adf_p < 0.05 and kpss_p >= 0.05:
        verdict = "I(0) Strongly Stationary"
    elif adf_p < 0.05 and kpss_p < 0.05:
        verdict = "Mean-Reverting (Structural Shift in Mean)"
    elif adf_p >= 0.05 and kpss_p >= 0.05:
        verdict = "Inconclusive"
    else:
        verdict = "I(1) Non-Stationary (Unit Root)"

    audit_rows.append({
        "feature_name": feat,
        "sample_size": len(series),
        "is_binary_flag": is_binary,
        "adf_stat": round(adf_stat, 4),
        "adf_pvalue": round(adf_p, 6),
        "adf_reject_unit_root_alpha05": bool(adf_p < 0.05),
        "kpss_stat": round(kpss_stat, 4) if not np.isnan(kpss_stat) else None,
        "kpss_pvalue": round(kpss_p, 4) if not np.isnan(kpss_p) else None,
        "kpss_stationary_alpha05": bool(kpss_p >= 0.05) if not np.isnan(kpss_p) else None,
        "econometric_verdict": verdict,
        "action_taken": "Safe for linear regression" if "Stationary" in verdict else "Requires z-score or cointegration residual"
    })

audit_df = pd.DataFrame(audit_rows)
csv_out = "reports/data_quality/stationarity_audit.csv"
json_out = "reports/data_quality/stationarity_audit.json"

audit_df.to_csv(csv_out, index=False)
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(audit_rows, f, indent=2)

print(f"[OK] Generated Stationarity Audit Report: {csv_out} ({len(audit_df)} features audited)")
print(audit_df[["feature_name", "adf_stat", "adf_pvalue", "econometric_verdict"]].to_string())
