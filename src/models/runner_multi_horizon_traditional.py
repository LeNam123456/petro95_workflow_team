# -*- coding: utf-8 -*-
"""Multi-horizon walk-forward runner for the traditional models (M0a to M5).

Horizons (purge = h, embargo = E):
- Daily:   h=1,  E=0
- Weekly:  h=5,  E=2
- Monthly: h=21, E=5

All models are the same classes used in Stream 1/2 (src.models.econometric / ml), run
through the single walk-forward engine (src.models.validation.walk_forward), which
enforces t <= tau - h - E for every training label.
"""

from __future__ import annotations

import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_proccessing.model_schemas import get_model_spec
from src.models.base import BaseForecastingModel
from src.models.econometric import (
    ArmaModel,
    AsymmetricAdlModel,
    LinearDynamicModel,
    NaiveDirectionModel,
    NaiveZeroModel,
)
from src.models.evaluation.forecast_tests import forecast_metrics
from src.models.ml.lgbm import EconomicLGBMModel, TechnicalLGBMModel
from src.models.validation.walk_forward import run_walk_forward_evaluation

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.MultiHorizonRunner")

MODEL_IDS = ("M0a", "M0b", "M1", "M2", "M3", "M4", "M5")
HORIZONS = (("daily", 1, 0), ("weekly", 5, 2), ("monthly", 21, 5))
WARMUP = 1500
REFIT_EVERY = 20


def model_factories(h: int) -> Dict[str, Callable[[], BaseForecastingModel]]:
    """Horizon-aware factories for M0a..M5."""
    return {
        "M0a": lambda: NaiveZeroModel(),
        "M0b": lambda: NaiveDirectionModel(horizon=h),
        "M1": lambda: ArmaModel(order=(1, 0, 1), trend="c", horizon=h),
        "M2": lambda: LinearDynamicModel(hac_lags=5),
        "M3": lambda: AsymmetricAdlModel(hac_lags=5),
        "M4": lambda: TechnicalLGBMModel(),
        "M5": lambda: EconomicLGBMModel(),
    }


def feature_columns() -> list[str]:
    cols: list[str] = []
    for mid in MODEL_IDS:
        for c in get_model_spec(mid).features:
            if c not in cols:
                cols.append(c)
    return cols


def run_walk_forward_horizon(
    df: pd.DataFrame,
    horizon_name: str = "daily",
    h: int = 1,
    embargo: int = 0,
    warmup: int = WARMUP,
    refit_every: int = REFIT_EVERY,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    target_col = f"target_return_{horizon_name}"
    valid = df[df[target_col].notna()].reset_index(drop=True)
    feats = feature_columns()
    X = valid[feats].fillna(0.0)
    X.index = pd.DatetimeIndex(valid["market_date"])
    y = pd.Series(valid[target_col].to_numpy(dtype=float), index=X.index, name=target_col)

    out = None
    for mid, factory in model_factories(h).items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ARIMA convergence chatter
            res = run_walk_forward_evaluation(
                factory, X, y, initial_train_size=warmup, refit_every=refit_every,
                horizon=h, embargo=embargo,
            )
        p = res.predictions_df
        if out is None:
            out = pd.DataFrame({
                "market_date": p.index,
                "actual_return": p["actual_return"].to_numpy(),
                "actual_direction": p["actual_direction"].to_numpy(),
            })
        out[f"pred_return_{mid}"] = p["predicted_return"].to_numpy()
        out[f"pred_dir_{mid}"] = p["predicted_direction"].to_numpy()
        out[f"residual_{mid}"] = p["residual"].to_numpy()
        logger.info("  %s/%s done (N_OOS=%d)", horizon_name, mid, len(p))

    leaderboard = []
    for mid in MODEL_IDS:
        met = forecast_metrics(out["actual_return"], out[f"pred_return_{mid}"], benchmark=out["pred_return_M0a"], horizon=h)
        leaderboard.append({"horizon": horizon_name, "h_steps": h, "embargo": embargo, "model_id": mid, **met})

    logger.info("Completed '%s': N_OOS=%d (%s to %s)", horizon_name, len(out),
                out["market_date"].iloc[0].date(), out["market_date"].iloc[-1].date())
    return out, {"horizon": horizon_name, "h": h, "leaderboard": leaderboard}


def run_all_three_horizons(
    data_path: str = "data/processed/stream2_multi_horizon_2017_2025.parquet",
    output_dir: str = "artifacts/multi_horizon",
) -> pd.DataFrame:
    p_out = Path(output_dir)
    p_out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(data_path)
    df["market_date"] = pd.to_datetime(df["market_date"])
    df = df.sort_values("market_date").reset_index(drop=True)

    all_rows = []
    for name, h, emb in HORIZONS:
        logger.info("Horizon '%s' (h=%d, embargo=%d)", name, h, emb)
        preds, audit = run_walk_forward_horizon(df, name, h=h, embargo=emb)
        preds.to_csv(p_out / f"oos_predictions_{name}_h{h}.csv", index=False)
        all_rows += audit["leaderboard"]

    df_lead = pd.DataFrame(all_rows)
    df_lead.to_csv(p_out / "multi_horizon_traditional_leaderboard.csv", index=False)
    with open(p_out / "multi_horizon_traditional_leaderboard.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2)
    logger.info("Saved multi-horizon outputs to %s", p_out)
    print("\n" + df_lead.to_string(index=False))
    return df_lead


if __name__ == "__main__":
    run_all_three_horizons()
