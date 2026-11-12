"""Visualization utilities for forecasting benchmark results.

Generates:
1. Actual vs. Predicted comparison plots across horizons (USD/barrel time series + residuals).
2. Directional confusion matrices (Actual Up/Down vs. Predicted Up/Down heatmaps).
3. Training and validation loss curves across recurrent neural architectures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_directional_confusion_matrix(
    actual_prices: np.ndarray | pd.Series,
    predicted_prices: np.ndarray | pd.Series,
    origin_prices: np.ndarray | pd.Series,
    binary_mode: bool = True,
) -> dict[str, Any]:
    """Compute 2x2 directional confusion matrix (Actual Up/Down vs. Predicted Up/Down).

    Direction definitions:
    - Up: price increase relative to origin (delta > 0)
    - Down: price decrease or non-increase relative to origin (delta <= 0)

    Returns:
    - Dict with counts: tp, fn, fp, tn, total
    - Rates: accuracy, sensitivity_up (recall), specificity_down, precision_up, precision_down
    - 2x2 matrix: [[tp, fn], [fp, tn]]
    """
    act = np.asarray(actual_prices, dtype=np.float64)
    pred = np.asarray(predicted_prices, dtype=np.float64)
    orig = np.asarray(origin_prices, dtype=np.float64)

    delta_act = act - orig
    delta_pred = pred - orig

    act_up = delta_act > 0
    pred_up = delta_pred > 0

    tp = int(np.sum(act_up & pred_up))
    fn = int(np.sum(act_up & (~pred_up)))
    fp = int(np.sum((~act_up) & pred_up))
    tn = int(np.sum((~act_up) & (~pred_up)))
    total = len(act)

    accuracy = float((tp + tn) / total * 100.0) if total > 0 else 0.0
    sensitivity_up = float(tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0
    specificity_down = float(tn / (tn + fp) * 100.0) if (tn + fp) > 0 else 0.0
    precision_up = float(tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
    precision_down = float(tn / (tn + fn) * 100.0) if (tn + fn) > 0 else 0.0

    matrix = np.array([[tp, fn], [fp, tn]], dtype=np.int64)

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "total": total,
        "accuracy": accuracy,
        "sensitivity_up": sensitivity_up,
        "specificity_down": specificity_down,
        "precision_up": precision_up,
        "precision_down": precision_down,
        "matrix": matrix,
        "labels": ["Up", "Down"],
    }


def plot_actual_vs_predicted(
    predictions_df: pd.DataFrame,
    horizon: int,
    output_path: str | Path,
    models_to_plot: list[str] | None = None,
) -> Path:
    """Generate publication-ready comparison plot of actual vs. predicted prices.

    Includes:
    - Upper panel: Actual Mogas 95 price and model predictions (USD/barrel).
    - Lower panel: Forecast error / residual series (USD/barrel).
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    df_h = predictions_df[predictions_df["horizon"] == horizon].copy()
    if df_h.empty:
        df_h = predictions_df.copy()

    # Parse timestamps
    time_col = "target_timestamp" if "target_timestamp" in df_h.columns else "forecast_origin"
    df_h[time_col] = pd.to_datetime(df_h[time_col])

    # Default model selections prioritizing multivariate relative change
    if models_to_plot is None:
        target_rep = "relative_change"
        # Pick representative subset
        sub = df_h[df_h["target_representation"] == target_rep]
        if sub.empty:
            sub = df_h
        avail_models = sub["model"].unique().tolist()
        preferred_order = ["Naive", "XGBoost", "LSTM", "GRU"]
        models_to_plot = [m for m in preferred_order if m in avail_models]
        if not models_to_plot:
            models_to_plot = avail_models[:4]

    # Palette
    color_map = {
        "Actual": "#111111",
        "Naive": "#7f7f7f",
        "XGBoost": "#2ca02c",
        "LSTM": "#d62728",
        "GRU": "#1f77b4",
    }
    style_map = {
        "Actual": ("-", 2.2, 10),
        "Naive": (":", 1.4, 4),
        "XGBoost": ("--", 1.6, 6),
        "LSTM": ("-", 1.6, 7),
        "GRU": ("-.", 1.6, 5),
    }

    fig, (ax_main, ax_err) = plt.subplots(
        2, 1, figsize=(14, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )

    # Plot Actual
    first_model = models_to_plot[0]
    first_subset = df_h[df_h["model"] == first_model].sort_values(time_col)
    if first_subset.empty:
        first_subset = df_h.drop_duplicates(subset=[time_col]).sort_values(time_col)

    x_dates = first_subset[time_col].dt.tz_localize(None) if first_subset[time_col].dt.tz is not None else first_subset[time_col]
    y_actual = first_subset["actual_price"].to_numpy()

    ax_main.plot(
        x_dates,
        y_actual,
        label="Actual Platts Singapore Mogas 95",
        color=color_map["Actual"],
        linestyle=style_map["Actual"][0],
        linewidth=style_map["Actual"][1],
        zorder=style_map["Actual"][2],
    )

    # Plot Model Predictions
    for model_name in models_to_plot:
        model_sub = df_h[df_h["model"] == model_name].copy()
        # Prefer multivariate if multiple scenarios
        if "multivariate" in model_sub["scenario"].values:
            model_sub = model_sub[model_sub["scenario"] == "multivariate"]
        # Prefer relative_change if multiple target reps
        if "relative_change" in model_sub["target_representation"].values:
            model_sub = model_sub[model_sub["target_representation"] == "relative_change"]

        model_sub = model_sub.sort_values(time_col)
        if model_sub.empty:
            continue

        m_x = model_sub[time_col].dt.tz_localize(None) if model_sub[time_col].dt.tz is not None else model_sub[time_col]
        m_y = model_sub["predicted_price"].to_numpy()
        m_err = model_sub["error"].to_numpy() if "error" in model_sub.columns else (m_y - model_sub["actual_price"].to_numpy())

        c = color_map.get(model_name, "#9467bd")
        ls, lw, zo = style_map.get(model_name, ("-", 1.5, 5))

        scenario_label = f" ({model_sub['scenario'].iloc[0]})" if model_name != "Naive" else ""
        ax_main.plot(
            m_x,
            m_y,
            label=f"{model_name}{scenario_label}",
            color=c,
            linestyle=ls,
            linewidth=lw,
            alpha=0.9,
            zorder=zo,
        )

        ax_err.plot(
            m_x,
            m_err,
            label=f"{model_name}",
            color=c,
            linestyle=ls,
            linewidth=1.2,
            alpha=0.85,
        )

    # Reference zero error line
    ax_err.axhline(0, color="black", linestyle="--", linewidth=1.0, alpha=0.7)

    # Format Main Axis
    ax_main.set_title(
        f"Platts Singapore Mogas 95 — Actual vs. Predicted (Horizon h = {horizon} Trading Sessions)",
        fontsize=13,
        fontweight="bold",
        pad=10,
    )
    ax_main.set_ylabel("Price (USD/barrel)", fontsize=11, fontweight="medium")
    ax_main.grid(True, linestyle="--", alpha=0.5)
    ax_main.legend(loc="upper left", framealpha=0.9, fontsize=9)

    # Format Residual Axis
    ax_err.set_ylabel("Error (USD/bbl)", fontsize=10, fontweight="medium")
    ax_err.set_xlabel("Evaluation Date", fontsize=11, fontweight="medium")
    ax_err.grid(True, linestyle="--", alpha=0.5)
    ax_err.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax_err.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

    fig.tight_layout()
    fig.savefig(out_file, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return out_file


def plot_directional_confusion_matrices(
    predictions_by_horizon: dict[int, pd.DataFrame],
    output_path: str | Path,
    models: list[str] | None = None,
) -> Path:
    """Generate multi-panel figure of directional confusion matrices across horizons.

    Layout:
    - Rows: Forecast horizons (e.g. h = 1, h = 5, h = 21)
    - Columns: Evaluated models (e.g. XGBoost, LSTM, GRU)
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    target_models = models or ["XGBoost", "LSTM", "GRU"]
    horizons = sorted(list(predictions_by_horizon.keys()))

    n_rows = len(horizons)
    n_cols = len(target_models)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(4.2 * n_cols, 3.8 * n_rows),
        squeeze=False,
    )

    cmap = plt.cm.Blues

    for r_idx, h in enumerate(horizons):
        df_h = predictions_by_horizon[h]
        for c_idx, m_name in enumerate(target_models):
            ax = axes[r_idx, c_idx]

            # Filter model data (prefer multivariate relative change)
            sub = df_h[df_h["model"].str.lower() == m_name.lower()].copy()
            if sub.empty:
                # If model name not found, display blank placeholder
                ax.text(0.5, 0.5, f"{m_name}\n(No data for h={h})", ha="center", va="center")
                ax.axis("off")
                continue

            if "multivariate" in sub["scenario"].values:
                sub = sub[sub["scenario"] == "multivariate"]
            if "relative_change" in sub["target_representation"].values:
                sub = sub[sub["target_representation"] == "relative_change"]

            cm_info = compute_directional_confusion_matrix(
                actual_prices=sub["actual_price"].to_numpy(),
                predicted_prices=sub["predicted_price"].to_numpy(),
                origin_prices=sub["origin_price"].to_numpy(),
                binary_mode=True,
            )

            mat = cm_info["matrix"]
            total = cm_info["total"]

            # Heatmap display
            im = ax.imshow(mat, cmap=cmap, interpolation="nearest", vmin=0, vmax=total * 0.7)

            # Cell annotations
            cell_descriptions = [
                ["True Up (TP)", "False Down (FN)"],
                ["False Up (FP)", "True Down (TN)"],
            ]
            thresh = mat.max() / 2.0

            for i in range(2):
                for j in range(2):
                    count = mat[i, j]
                    pct = (count / total * 100.0) if total > 0 else 0.0
                    text_color = "white" if count > thresh else "black"
                    cell_text = f"{cell_descriptions[i][j]}\n{count:,}\n({pct:.1f}%)"
                    ax.text(
                        j,
                        i,
                        cell_text,
                        ha="center",
                        va="center",
                        color=text_color,
                        fontsize=9,
                        fontweight="bold",
                    )

            # Axis formatting
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["Pred Up", "Pred Down"], fontsize=9, fontweight="medium")
            ax.set_yticklabels(["Act Up", "Act Down"], fontsize=9, fontweight="medium")

            if r_idx == n_rows - 1:
                ax.set_xlabel("Predicted Direction", fontsize=10, fontweight="bold", labelpad=6)
            if c_idx == 0:
                ax.set_ylabel(f"Horizon h = {h}\nActual Direction", fontsize=10, fontweight="bold", labelpad=6)

            metrics_subtitle = (
                f"DA: {cm_info['accuracy']:.1f}% | Prec(Up): {cm_info['precision_up']:.1f}%\n"
                f"Rec(Up): {cm_info['sensitivity_up']:.1f}% | Rec(Down): {cm_info['specificity_down']:.1f}%"
            )
            ax.set_title(f"{m_name} (h={h})\n{metrics_subtitle}", fontsize=9, fontweight="bold", pad=8)

    fig.suptitle(
        "Directional Confusion Matrices (Actual Up/Down vs. Predicted Up/Down) across Horizons",
        fontsize=14,
        fontweight="bold",
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(out_file, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return out_file


def plot_loss_curves(
    loss_histories: dict[str, dict[str, list[float]]],
    output_path: str | Path,
) -> Path:
    """Plot training and validation loss curves across recurrent model configurations.

    Parameters:
    - loss_histories: Mapping of config_label -> {"train": [losses], "val": [losses]}
    - output_path: Destination path for saved PNG figure.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if not loss_histories:
        return out_file

    n_configs = len(loss_histories)
    cols = 3
    rows = (n_configs + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(15, 3.5 * rows), squeeze=False)
    axes_flat = axes.flatten()

    for idx, (label, history) in enumerate(loss_histories.items()):
        ax = axes_flat[idx]
        train_loss = history.get("train", [])
        val_loss = history.get("val", [])
        epochs = list(range(1, max(len(train_loss), len(val_loss)) + 1))

        if train_loss:
            ax.plot(epochs[:len(train_loss)], train_loss, label="Train Loss", color="royalblue", alpha=0.85, linewidth=1.5)
        if val_loss:
            ax.plot(epochs[:len(val_loss)], val_loss, label="Val Loss", color="crimson", alpha=0.85, linewidth=1.5)

        ax.set_title(label, fontsize=9, fontweight="bold")
        ax.set_xlabel("Epoch", fontsize=8)
        ax.set_ylabel("MSE Loss", fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=8)

    # Hide any unused subplots
    for j in range(idx + 1, len(axes_flat)):
        fig.delaxes(axes_flat[j])

    fig.suptitle(
        "Deep Learning Training & Validation Loss Curves across Epochs",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )
    fig.tight_layout()
    fig.savefig(out_file, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return out_file
