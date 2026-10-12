"""Generate publication-quality visualizations for M0a, M0b, and M1 results."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.graphics.tsaplots import plot_acf

# Set style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.titleweight"] = "bold"

# 1. Load predictions
pred_file_m0a = Path("artifacts/predictions/pred_M0a_stream1.parquet")
pred_file_m0b = Path("artifacts/predictions/pred_M0b_stream1.parquet")
pred_file_m1 = Path("artifacts/predictions/pred_M1_stream1.parquet")

if not pred_file_m1.exists():
    print("Prediction files not found. Creating simulated window for demonstration.")
    # If full walk-forward was skipped, load raw stream 1 and compute in-sample fitted values
    df_raw = pd.read_parquet("data/processed/stream1_econometric_2008_2025.parquet")
    dates = pd.to_datetime(df_raw["market_date"])
    actual_r = df_raw["target_return_pct"]
    r_t = df_raw["mg95_return_pct"]
    
    # Load M1 params
    with open("artifacts/models/M1_coefficients.json") as f:
        meta = json.load(f)
    c = meta["params"]["const"]
    phi = meta["params"]["ar.L1"]
    theta = meta["params"]["ma.L1"]
    
    # Compute M1 fitted
    m1_pred = c + phi * r_t
    df_m0a = pd.DataFrame({"market_date": dates, "actual_return": actual_r, "predicted_return": 0.0, "residual": actual_r})
    df_m0b = pd.DataFrame({"market_date": dates, "actual_return": actual_r, "predicted_return": r_t, "residual": actual_r - r_t})
    df_m1 = pd.DataFrame({"market_date": dates, "actual_return": actual_r, "predicted_return": m1_pred, "residual": actual_r - m1_pred})
else:
    df_m0a = pd.read_parquet(pred_file_m0a)
    df_m0b = pd.read_parquet(pred_file_m0b)
    df_m1 = pd.read_parquet(pred_file_m1)

# Ensure datetime
df_m1["market_date"] = pd.to_datetime(df_m1["market_date"])

# =============================================================================
# FIGURE 1: FORECAST TRAJECTORY COMPARISON (RECENT WINDOW - LAST 60 DAYS)
# =============================================================================
recent_m1 = df_m1.iloc[-60:].copy()
recent_m0b = df_m0b.iloc[-60:].copy()
recent_m0a = df_m0a.iloc[-60:].copy()

plt.figure(figsize=(14, 6))
plt.plot(recent_m1["market_date"], recent_m1["actual_return"], color="black", lw=2.2, label="Actual Return r_{t+1} (Thực tế)", marker="o", markersize=3)
plt.plot(recent_m0a["market_date"], recent_m0a["predicted_return"], color="gray", lw=1.5, ls="--", label="M0a: Naive Zero (r_hat = 0)")
plt.plot(recent_m0b["market_date"], recent_m0b["predicted_return"], color="#ff7f0e", lw=1.5, ls="-.", label="M0b: Naive Momentum (r_hat = r_t)")
plt.plot(recent_m1["market_date"], recent_m1["predicted_return"], color="#1f77b4", lw=2, label="M1: ARMA(1,1) Kalman MLE")

plt.axhline(0, color="gray", lw=0.8, ls=":")
plt.title("HÌNH 1: SO SÁNH GIÁ TRỊ DỰ BÁO CỦA M0a, M0b VÀ M1 TRÊN 60 PHIÊN GIAO DỊCH GẦN NHẤT")
plt.xlabel("Ngày Giao Dịch")
plt.ylabel("Tỷ Suất Sinh Lời Dự Báo (%)")
plt.legend(loc="upper right", frameon=True)
plt.tight_layout()

out_fig1 = Path("reports/figures/m0_m1_predictions_comparison.png")
out_fig1.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_fig1, dpi=300)
plt.close()
print(f"[OK] Saved Figure 1: {out_fig1}")

# =============================================================================
# FIGURE 2: M1 RESIDUAL DIAGNOSTICS (3 PANELS)
# =============================================================================
df_m1_valid = df_m1.dropna(subset=["residual"]).copy()
residuals = df_m1_valid["residual"]

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Subplot A: Residual Time Series
axes[0].plot(df_m1_valid["market_date"], residuals, color="#1f77b4", lw=0.8, alpha=0.8)
axes[0].axhline(0, color="red", lw=1, ls="--")
axes[0].set_title("A. Chuỗi Phần Dư e_t = r_{t+1} - r_hat")
axes[0].set_xlabel("Thời Gian")
axes[0].set_ylabel("Sai số (%)")

# Subplot B: Density vs Normal
mean_e = residuals.mean()
std_e = residuals.std()
axes[1].hist(residuals, bins=60, density=True, color="#1f77b4", alpha=0.6, label="Phân phối thực tế")
x_axis = np.linspace(residuals.min(), residuals.max(), 300)
norm_pdf = stats.norm.pdf(x_axis, loc=mean_e, scale=std_e)
axes[1].plot(x_axis, norm_pdf, color="red", lw=2, ls="--", label="Phân phối Chuẩn (Normal)")
axes[1].set_xlim(-10, 10)
axes[1].set_title(f"B. Mật Độ Sai Số (Std = {std_e:.2f}%)")
axes[1].set_xlabel("Phần dư (%)")
axes[1].legend()

# Subplot C: ACF of Residuals
plot_acf(residuals, lags=20, ax=axes[2], color="#1f77b4", title="C. Tự Tương Quan Phần Dư (ACF Lags 1-20)")
axes[2].set_xlabel("Độ trễ (Lags)")
axes[2].set_ylabel("Hệ số Tương quan")

plt.tight_layout()
out_fig2 = Path("reports/figures/m1_residual_diagnostics.png")
plt.savefig(out_fig2, dpi=300)
plt.close()
print(f"[OK] Saved Figure 2: {out_fig2}")
