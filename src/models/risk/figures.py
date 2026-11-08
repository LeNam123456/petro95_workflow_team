# -*- coding: utf-8 -*-
"""Static figures for the direction-4 report (PNG, light surface).

    python src/models/risk/figures.py   -> artifacts/risk/figures/*.png

Colors follow the validated reference palette (categorical slots 1-3 in fixed order:
blue, orange, aqua); bands use one sequential blue ramp. Text uses ink tokens only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RISK = ROOT / "artifacts" / "risk"
OUT = RISK / "figures"

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]          # categorical slots 1-3
BAND95, BAND80, MEDIAN = "#cde2fb", "#86b6ef", "#1c5cab"  # sequential blue 100 / 250 / 550
HORIZON_VI = {"daily": "1 ngày", "weekly": "1 tuần", "monthly": "1 tháng"}
MODELS = ["Q0", "Q1", "Q2", "Q3", "Q4"]


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _fig(nrows, ncols, w, h):
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), facecolor=SURFACE, squeeze=False)
    plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]
    return fig, axes


def fan_chart(dataset: str = "stream2") -> Path:
    lead = pd.read_csv(RISK / dataset / "leaderboard.csv")
    fig, axes = _fig(3, 1, 11, 9.5)
    for ax, hz in zip(axes[:, 0], ["daily", "weekly", "monthly"]):
        best = lead[lead.horizon == hz].sort_values("pinball").iloc[0]["model_id"]
        q = pd.read_csv(RISK / dataset / f"quantiles_{best}_{hz}.csv", parse_dates=["market_date"])
        x = q["market_date"]
        ax.fill_between(x, q["q0.025"], q["q0.975"], color=BAND95, linewidth=0, label="Khoảng 95%")
        ax.fill_between(x, q["q0.1"], q["q0.9"], color=BAND80, linewidth=0, label="Khoảng 80%")
        ax.plot(x, q["q0.5"], color=MEDIAN, linewidth=1.2, label="Trung vị dự báo")
        out = (q["actual_return"] < q["q0.1"]) | (q["actual_return"] > q["q0.9"])
        ax.scatter(x[~out], q["actual_return"][~out], s=6, color=INK2, linewidths=0, label="Thực tế (trong khoảng 80%)")
        ax.scatter(x[out], q["actual_return"][out], s=9, color=SERIES[1], linewidths=0, label="Thực tế (ngoài khoảng 80%)")
        _style(ax)
        ax.axhline(0, color=AXIS, linewidth=0.8)
        ax.set_title(f"{HORIZON_VI[hz]} — mô hình {best}  ·  tỷ lệ bao phủ 80% = {1 - out.mean():.1%}",
                     loc="left", fontsize=11, color=INK)
        ax.set_ylabel("Thay đổi giá MG95 (%)", color=INK2, fontsize=9)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.suptitle("Khoảng dự báo walk-forward, giai đoạn kiểm tra 28/12/2022 – 2025 (Luồng 2)",
                 x=0.01, y=0.995, ha="left", fontsize=13, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.01, 0.965), ncol=5, fontsize=8.5,
               frameon=False, labelcolor=INK2, markerscale=2)
    p = OUT / f"fan_chart_{dataset}.png"
    fig.savefig(p, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return p


def coverage_chart() -> Path:
    fig, axes = _fig(1, 2, 11, 4.2)
    for ax, ds, title in zip(axes[0], ["stream2", "stream1"], ["Luồng 2 · 2023–2025", "Luồng 1 · 2012–2025"]):
        lead = pd.read_csv(RISK / ds / "leaderboard.csv")
        for i, hz in enumerate(["daily", "weekly", "monthly"]):
            sub = lead[lead.horizon == hz].set_index("model_id").loc[MODELS]
            xs = [m + (i - 1) * 0.18 for m in range(len(MODELS))]
            ax.scatter(xs, sub["coverage_80"] * 100, s=46, color=SERIES[i], edgecolors=SURFACE,
                       linewidths=1.5, label=HORIZON_VI[hz], zorder=3)
        ax.axhline(80, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
        ax.text(-0.45, 79.4, "mục tiêu 80%", color=INK2, fontsize=8, ha="left", va="top")
        _style(ax)
        ax.set_xticks(range(len(MODELS)), MODELS)
        ax.set_ylim(70, 100)
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        ax.set_ylabel("Tỷ lệ giá thực rơi vào khoảng 80% (%)", color=INK2, fontsize=9)
    axes[0, 0].legend(loc="upper right", fontsize=8, frameon=False, labelcolor=INK2)
    fig.suptitle("Độ hiệu chỉnh: nói 80% thì thực tế bao nhiêu %?", x=0.01, ha="left", fontsize=13, color=INK)
    fig.tight_layout()
    p = OUT / "coverage_80.png"
    fig.savefig(p, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return p


def risk_ratio_chart(model: str = "Q2") -> Path:
    fig, axes = _fig(1, 1, 8, 4.2)
    ax = axes[0, 0]
    labels = [("stream1", "Luồng 1 · 2012–2025"), ("stream2", "Luồng 2 · 2023–2025")]
    hzs = ["daily", "weekly", "monthly"]
    w = 0.36
    for i, (ds, lab) in enumerate(labels):
        lead = pd.read_csv(RISK / ds / "leaderboard.csv").set_index(["horizon", "model_id"])
        vals = [lead.loc[(hz, model), "risk_ratio_high_low"] for hz in hzs]
        xs = [k + (i - 0.5) * (w + 0.02) for k in range(len(hzs))]
        ax.bar(xs, vals, width=w, color=SERIES[i], label=lab, zorder=3)
        for x, v in zip(xs, vals):
            ax.text(x, max(v, 1.0) + 0.04, f"{v:.2f}×", ha="center", va="bottom", fontsize=9, color=INK)
    ax.axhline(1, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    _style(ax)
    ax.set_xlim(-0.65, 2.55)
    ax.set_xticks(range(len(hzs)), [HORIZON_VI[h] for h in hzs])
    ax.set_ylabel("Độ lệch chuẩn thực tế:\nnhóm rủi ro CAO / THẤP", color=INK2, fontsize=9)
    ax.legend(loc="upper right", fontsize=8, frameon=False, labelcolor=INK2)
    ax.set_title(f"Mô hình {model} có báo trước được giai đoạn biến động mạnh không?\n"
                 "Đường nét đứt 1× = không phân biệt được rủi ro cao/thấp",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    p = OUT / f"risk_ratio_{model}.png"
    fig.savefig(p, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return p


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for p in (fan_chart("stream2"), coverage_chart(), risk_ratio_chart("Q2")):
        print("written", p)


if __name__ == "__main__":
    sys.exit(main())
