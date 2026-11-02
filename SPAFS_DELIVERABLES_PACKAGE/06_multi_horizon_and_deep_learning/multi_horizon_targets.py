# -*- coding: utf-8 -*-
"""Step 04B — Multi-Horizon Target Engineering & Overlapping Label Governance.

Formulates targets for:
- Daily: h=1 trading day
    r_{t, 1} = ln(P_{t+1} / P_t) * 100%
- Weekly: h=5 trading days
    r_{t, 5} = ln(P_{t+5} / P_t) * 100%
- Monthly: h=21 trading days
    r_{t, 21} = ln(P_{t+21} / P_t) * 100%

Along with binary directional indicators:
    y_{t, h} = 1 if r_{t, h} > 0 else 0
"""

from __future__ import annotations

import logging
from pathlib import Path
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SPAFS_V5.2.MultiHorizon")


def generate_multi_horizon_dataset(
    input_path: str = "data/processed/stream2_aligned_nlp_2017_2025.parquet",
    output_path: str = "data/processed/stream2_multi_horizon_2017_2025.parquet",
) -> pd.DataFrame:
    p_in = Path(input_path)
    if not p_in.exists():
        raise FileNotFoundError(f"Input file not found: {p_in}")

    df = pd.read_parquet(p_in)
    df["market_date"] = pd.to_datetime(df["market_date"])
    df = df.sort_values("market_date").reset_index(drop=True)

    price_col = "MG95"
    if price_col not in df.columns:
        raise KeyError(f"Price column '{price_col}' not found in {df.columns}")

    prices = df[price_col].values
    dates = df["market_date"].values
    n = len(df)

    # 1. Daily (h=1)
    ret_daily = np.full(n, np.nan, dtype=float)
    ret_daily[:-1] = np.log(prices[1:] / prices[:-1]) * 100.0
    dir_daily = np.where(np.isnan(ret_daily), np.nan, (ret_daily > 0.0).astype(float))

    # 2. Weekly (h=5 trading days)
    ret_weekly = np.full(n, np.nan, dtype=float)
    ret_weekly[:-5] = np.log(prices[5:] / prices[:-5]) * 100.0
    dir_weekly = np.where(np.isnan(ret_weekly), np.nan, (ret_weekly > 0.0).astype(float))

    # 3. Monthly (h=21 trading days)
    ret_monthly = np.full(n, np.nan, dtype=float)
    ret_monthly[:-21] = np.log(prices[21:] / prices[:-21]) * 100.0
    dir_monthly = np.where(np.isnan(ret_monthly), np.nan, (ret_monthly > 0.0).astype(float))

    # Append targets
    df["target_return_daily"] = ret_daily
    df["target_dir_daily"] = dir_daily

    df["target_return_weekly"] = ret_weekly
    df["target_dir_weekly"] = dir_weekly

    df["target_return_monthly"] = ret_monthly
    df["target_dir_monthly"] = dir_monthly

    # Forward realization dates
    date_real_daily = pd.Series(dates).shift(-1)
    date_real_weekly = pd.Series(dates).shift(-5)
    date_real_monthly = pd.Series(dates).shift(-21)

    df["realization_date_daily"] = date_real_daily
    df["realization_date_weekly"] = date_real_weekly
    df["realization_date_monthly"] = date_real_monthly

    p_out = Path(output_path)
    p_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p_out, index=False)

    logger.info("Generated Multi-Horizon Dataset: %s", p_out)
    logger.info("Total rows: %d", n)
    logger.info("Valid Daily targets  : %d rows", int(np.sum(~np.isnan(ret_daily))))
    logger.info("Valid Weekly targets : %d rows", int(np.sum(~np.isnan(ret_weekly))))
    logger.info("Valid Monthly targets: %d rows", int(np.sum(~np.isnan(ret_monthly))))

    return df


if __name__ == "__main__":
    generate_multi_horizon_dataset()
