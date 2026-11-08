# -*- coding: utf-8 -*-
"""Reproducible pairwise audit for SPAFS V5.2 (daily, h = 1).

Recomputes, from saved walk-forward predictions only, the model summary and the headline
pairwise tests on the common out-of-sample window of Stream 1 (M0a..M3) and Stream 2
(M4, M5). All statistics come from src.models.evaluation.forecast_tests.

Inputs (either):
* a predictions directory with pred_{M0a,M0b,M1,M2,M3}_stream1.parquet and
  pred_{M4,M5}_stream2.parquet (default: artifacts/predictions), or
* a CSV with columns market_date, actual_return, pred_return_<model>.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.evaluation.forecast_tests import cw_test, dm_test, forecast_metrics

MODELS = {
    "M0a": "Naive Zero Return Benchmark",
    "M0b": "Naive Persistence (r_hat_{t+1} = r_t)",
    "M1": "Univariate ARMA(1,1)",
    "M2": "Linear Dynamic ADL",
    "M3": "Asymmetric ADL",
    "M4": "Technical LightGBM Ensemble",
    "M5": "Economic Refining LightGBM Ensemble",
}
CW_PAIRS = [("M5", "M4"), ("M3", "M2"), ("M5", "M0a"), ("M4", "M0a")]  # (candidate, nested benchmark)
DM_PAIRS = [("M5", "M4"), ("M3", "M2")]


def _load_predictions(csv_path: Optional[str], predictions_dir: str) -> tuple[pd.DataFrame, dict]:
    if csv_path:
        p = Path(csv_path)
        df = pd.read_csv(p, parse_dates=["market_date"]).set_index("market_date")
        src = {"type": "CSV", "path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        return df, src

    p_dir = Path(predictions_dir)
    frames = {}
    for m in MODELS:
        stream = "stream2" if m in ("M4", "M5") else "stream1"
        f = p_dir / f"pred_{m}_{stream}.parquet"
        if f.exists():
            frames[m] = pd.read_parquet(f)
    if "M4" not in frames or "M5" not in frames:
        raise FileNotFoundError(f"pred_M4_stream2.parquet / pred_M5_stream2.parquet missing in {p_dir}")

    idx = frames["M5"].index
    for fr in frames.values():
        idx = idx.intersection(fr.index)
    idx = idx.sort_values()
    df = pd.DataFrame({"actual_return": frames["M5"].loc[idx, "actual_return"]}, index=idx)
    for m, fr in frames.items():
        gap = np.abs(fr.loc[idx, "actual_return"].to_numpy() - df["actual_return"].to_numpy()).max()
        if gap > 1e-6:
            raise ValueError(f"Actual returns of {m} disagree with Stream 2 on the common window ({gap}).")
        df[f"pred_return_{m}"] = fr.loc[idx, "predicted_return"]
    return df, {"type": "Parquet Directory", "path": str(p_dir)}


def _json_safe(obj):
    """Replace NaN/inf by None and numpy scalars by Python scalars (strict JSON)."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    return obj


def run_pipeline_evaluation(
    csv_path: Optional[str] = None,
    predictions_dir: str = "artifacts/predictions",
    output_json_path: str = "artifacts/metrics/reproducible_statistical_tests.json",
) -> dict:
    """Recompute summary metrics and pairwise tests and write them to JSON."""
    df, source = _load_predictions(csv_path, predictions_dir)
    y = df["actual_return"]
    available = [m for m in MODELS if f"pred_return_{m}" in df.columns]
    pred = {m: df[f"pred_return_{m}"] for m in available}

    summary = []
    for m in available:
        met = forecast_metrics(y, pred[m])  # R2_OOS vs zero forecast
        summary.append({"model_id": m, "name": MODELS[m], **met})

    cw_tests = [
        cw_test(y, pred[c], pred[b], horizon=1, candidate_id=c, benchmark_id=b).to_dict()
        for c, b in CW_PAIRS if c in pred and b in pred
    ]
    dm_tests = [
        dm_test(y, pred[c], pred[b], loss=loss, horizon=1, candidate_id=c, benchmark_id=b).to_dict()
        for c, b in DM_PAIRS if c in pred and b in pred
        for loss in ("squared", "absolute")
    ]

    payload = {
        "execution_timestamp": datetime.datetime.now().isoformat(),
        "data_source": source,
        "sample_size": int(len(df)),
        "date_range_start": str(df.index.min().date()),
        "date_range_end": str(df.index.max().date()),
        "note": "M0a..M3 are Stream 1 walk-forward forecasts restricted to the Stream 2 OOS window.",
        "models_summary": summary,
        "clark_west_tests": cw_tests,
        "diebold_mariano_tests": dm_tests,
    }
    out = Path(output_json_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_json_safe(payload), indent=2, allow_nan=False), encoding="utf-8")

    print(f"N_OOS = {len(df)} ({payload['date_range_start']} .. {payload['date_range_end']})")
    for r in summary:
        print(f"  {r['model_id']:4s} RMSE={r['rmse']:.4f} MAE={r['mae']:.4f} R2_OOS={r['r2_oos_pct']:+.2f}% "
              f"DA={r['da_pct']:.2f}% MCC={r['mcc']:.4f} PT={r['pt_stat']:.3f} (p={r['pt_p_value']:.3g})")
    for t in cw_tests:
        print(f"  CW {t['candidate_id']} vs {t['benchmark_id']}: stat={t['statistic']:+.3f} p1={t['p_value_one_sided']:.4g}")
    for t in dm_tests:
        print(f"  DM[{t['loss']}] {t['candidate_id']} vs {t['benchmark_id']}: stat={t['statistic']:+.3f} "
              f"p1={t['p_value_one_sided']:.4g} p2={t['p_value_two_sided']:.4g}")
    print(f"Written: {out}")
    return payload


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Reproducible pairwise statistical audit")
    parser.add_argument("--csv", type=str, default=None)
    parser.add_argument("--predictions_dir", type=str, default="artifacts/predictions")
    parser.add_argument("--output", type=str, default="artifacts/metrics/reproducible_statistical_tests.json")
    a = parser.parse_args()
    run_pipeline_evaluation(csv_path=a.csv, predictions_dir=a.predictions_dir, output_json_path=a.output)
