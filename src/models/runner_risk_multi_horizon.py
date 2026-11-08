# -*- coding: utf-8 -*-
"""Direction 4 runner: walk-forward interval / risk forecasts (Q0-Q4) for 1, 5, 21 sessions.

Datasets
    stream2     2017-2025, OOS from row 1500 (2022-12-28): same window as M0a-M5 / RNN / LSTM.
    stream1     2008-2025, OOS from 2012-01-03: robustness set containing the 2014-15,
                2020 and 2022 turbulence.

Usage
    python src/models/runner_risk_multi_horizon.py --dataset stream2
    python src/models/runner_risk_multi_horizon.py --dataset stream1

Outputs (artifacts/risk/<dataset>/)
    quantiles_<model>_<horizon>.csv   OOS quantile forecasts + actual
    leaderboard.csv / .json           all metrics per model x horizon
    dm_pinball_tests.csv              Diebold-Mariano on pinball loss
    run_manifest.json                 config, data hash, timings
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.evaluation.interval_tests import (
    build_unified_decision_card,
    compare_quantile_forecasts,
    evaluate_quantile_forecast,
)
from src.models.risk import LEVELS, MODEL_DESCRIPTIONS, RISK_MODEL_IDS, make_risk_model
from src.models.risk.quantile_models import Q4_FEATURES
from src.models.validation.walk_forward import purged_train_end, run_walk_forward_quantiles

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.RiskRunner")

HORIZONS = (("daily", 1, 0), ("weekly", 5, 2), ("monthly", 21, 5))
REFIT_EVERY = 20
# Ex-ante risk-regime seed (spec, problem 4): the walk-forward starts as early in the training
# period as MIN_SEED_TRAIN purged rows allow, so the 80% widths forecast before the OOS window
# cover the whole history (calm and crisis years), not only the year just before it.
MIN_SEED_TRAIN = 504  # ~2 trading years: enough to estimate GARCH(1,1)-t at the first seed origin


def regime_seed_start(oos_start: int, horizon: int, embargo: int) -> int:
    """Earliest walk-forward origin with >= MIN_SEED_TRAIN purged training rows.

    Kept a whole number of REFIT_EVERY steps before ``oos_start`` so the refit grid (and
    therefore every OOS forecast) is identical to a run that starts at ``oos_start``.
    """
    earliest = MIN_SEED_TRAIN - 1 + horizon + embargo
    steps = max(0, (oos_start - earliest) // REFIT_EVERY)
    return oos_start - steps * REFIT_EVERY
DATASETS = {
    "stream2": {"path": "data/processed/stream2_multi_horizon_2017_2025.parquet", "oos_start": 1500},
    "stream1": {"path": "data/processed/stream1_econometric_2008_2025.parquet", "oos_start_date": "2012-01-03"},
}
DM_PAIRS = [  # (candidate, benchmark)
    ("Q1", "Q0"), ("Q2", "Q0"), ("Q3", "Q0"), ("Q4", "Q0"),
    ("Q2", "Q1"), ("Q3", "Q2"), ("Q4", "Q2"), ("Q4", "Q3"),
]


def load_dataset(name: str) -> tuple[pd.DataFrame, dict]:
    cfg = DATASETS[name]
    df = pd.read_parquet(PROJECT_ROOT / cfg["path"])
    df["market_date"] = pd.to_datetime(df["market_date"])
    df = df.sort_values("market_date").reset_index(drop=True)
    if name == "stream1":
        # target_return_pct at row t is r_{t+1}; h-step target is r_{t+1} + ... + r_{t+h}.
        nxt = df["target_return_pct"]
        for hname, h, _ in HORIZONS:
            df[f"target_return_{hname}"] = nxt.rolling(h).sum().shift(-(h - 1))
    for c in Q4_FEATURES:
        df[c] = df[c].fillna(0.0)
    return df, cfg


def horizon_frame(df: pd.DataFrame, hname: str) -> tuple[pd.DataFrame, pd.Series]:
    valid = df[df[f"target_return_{hname}"].notna()].reset_index(drop=True)
    X = valid[list(Q4_FEATURES)].copy()
    X.index = pd.DatetimeIndex(valid["market_date"])
    y = pd.Series(valid[f"target_return_{hname}"].to_numpy(dtype=float), index=X.index)
    return X, y


def run_dataset(name: str, out_root: Path, models=RISK_MODEL_IDS) -> pd.DataFrame:
    df, cfg = load_dataset(name)
    out_dir = out_root / name
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, dm_rows, timings, best_quantiles, best_seed_widths = [], [], {}, {}, {}
    rec_models = {"daily": "Q3", "weekly": "Q3", "monthly": "Q2"}

    for hname, h, emb in HORIZONS:
        X, y = horizon_frame(df, hname)
        start = cfg.get("oos_start") or int(np.searchsorted(X.index.values, np.datetime64(cfg["oos_start_date"])))
        # Climatological probability of an increase, from data available at the first origin.
        clim_up = float((y.iloc[: purged_train_end(start, h, emb) + 1] > 0).mean())
        logger.info("[%s/%s] h=%d embargo=%d  OOS %s -> %s (N=%d)", name, hname, h, emb,
                    X.index[start].date(), X.index[-1].date(), len(y) - start)

        seed_start = regime_seed_start(start, h, emb)
        preds = {}
        for mid in models:
            t0 = time.time()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                full = run_walk_forward_quantiles(lambda m=mid: make_risk_model(m, h), X, y,
                                                  initial_train_size=seed_start, refit_every=REFIT_EVERY,
                                                  horizon=h, embargo=emb)
            timings[f"{hname}/{mid}"] = round(time.time() - t0, 1)
            seed, out = full.iloc[: start - seed_start], full.iloc[start - seed_start :]
            seed_widths = (seed[0.9] - seed[0.1]).to_numpy(dtype=float)
            preds[mid] = out[list(LEVELS)]
            out.rename(columns={lv: f"q{lv:g}" for lv in LEVELS}).to_csv(
                out_dir / f"quantiles_{mid}_{hname}.csv", index_label="market_date")
            if mid == rec_models.get(hname):
                best_quantiles[hname] = out
                best_seed_widths[hname] = seed_widths
            met = evaluate_quantile_forecast(out["actual_return"], preds[mid], horizon=h,
                                             p_up_reference=clim_up, history_width_80=seed_widths)
            rows.append({"dataset": name, "horizon": hname, "h": h, "model_id": mid,
                         "model": MODEL_DESCRIPTIONS[mid], "oos_start": str(X.index[start].date()),
                         "climatology_p_up": clim_up, **met})
            logger.info("  %s: cov80=%.3f cov95=%.3f width80=%.2f pinball=%.4f ratio=%.2f (%.0fs)",
                        mid, met["coverage_80"], met["coverage_95"], met["width_80"], met["pinball"],
                        met["risk_ratio_high_low"], timings[f"{hname}/{mid}"])

        y_oos = y.iloc[start:]
        for c, b in DM_PAIRS:
            if c in preds and b in preds:
                t = compare_quantile_forecasts(y_oos, preds[c], preds[b], horizon=h, candidate_id=c, benchmark_id=b)
                dm_rows.append({"dataset": name, "horizon": hname, "h": h, "candidate": c, "benchmark": b,
                                "pinball_candidate": t.details["candidate_loss_mean"],
                                "pinball_benchmark": t.details["benchmark_loss_mean"],
                                "improvement_pct": (1 - t.details["candidate_loss_mean"] / t.details["benchmark_loss_mean"]) * 100,
                                "dm_stat": t.statistic, "p_one_sided": t.p_value_one_sided,
                                "p_two_sided": t.p_value_two_sided, "hac_lags": t.hac_lags,
                                "candidate_better_5pct": t.reject_at(0.05)})

    lead = pd.DataFrame(rows)
    lead.to_csv(out_dir / "leaderboard.csv", index=False)
    lead.to_json(out_dir / "leaderboard.json", orient="records", indent=2)
    pd.DataFrame(dm_rows).to_csv(out_dir / "dm_pinball_tests.csv", index=False)
    if best_quantiles:
        card = build_unified_decision_card(best_quantiles, model_by_horizon=rec_models,
                                           history_width_80_by_horizon=best_seed_widths)
        card.to_csv(out_dir / "decision_card.csv", index=False)
    data_path = PROJECT_ROOT / cfg["path"]
    manifest = {
        "dataset": name, "data_path": cfg["path"],
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "levels": list(LEVELS), "refit_every": REFIT_EVERY,
        "regime_seed_min_train_rows": MIN_SEED_TRAIN,
        "horizons": [{"name": n, "h": h, "embargo": e} for n, h, e in HORIZONS],
        "models": {m: MODEL_DESCRIPTIONS[m] for m in models}, "timings_sec": timings,
        "executed_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Saved %s results to %s", name, out_dir)
    return lead


def main() -> None:
    ap = argparse.ArgumentParser(description="SPAFS V5.2 direction 4: interval / risk forecasts")
    ap.add_argument("--dataset", choices=[*DATASETS, "all"], default="all")
    ap.add_argument("--out", default="artifacts/risk")
    a = ap.parse_args()
    for name in (DATASETS if a.dataset == "all" else [a.dataset]):
        run_dataset(name, PROJECT_ROOT / a.out)


if __name__ == "__main__":
    main()
