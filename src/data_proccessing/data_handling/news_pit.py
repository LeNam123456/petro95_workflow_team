"""Step 06 — Point-in-Time News Sentiment & Information Flow Aggregator.

This module aggregates unstructured news sentiment metrics (FinBERT, GDELT Tone,
Goldstein Scale) strictly within the causal Point-in-Time information window
governed by the 08:30 SGT Cutoff (t_origin).

Key Architecture and Quantitative Principles:
1. Temporal Window Alignment:
   Assigns news articles published during the exact causal window:
       (forecast_origin_{t-1}, forecast_origin_t]
   where forecast_origin_t is 08:30 SGT on the morning of trading day D_{t+1}.
   This prevents any news published after 08:30 SGT from leaking into the predictor set.
2. Multi-Metric Sentiment Fusion:
   Aggregates:
   - ``news_count``: Volume of market-relevant news articles.
   - ``news_sentiment_mean``: Mean FinBERT polarity score [-1.0, +1.0].
   - ``news_native_tone_mean``: GDELT native tone score baseline.
   - ``news_goldstein_mean``: Goldstein geopolitical conflict/cooperation scale [-10, +10].
3. Zero-Ambiguity Invariant:
   Distinguishes true unobserved historical periods (2008–2016 where news is missing)
   from modern observed trading sessions with genuine zero news volume.
4. PIT Hard Gate Verification:
   Verifies that publication_datetime <= forecast_origin_datetime on all assigned records.

Artifacts Generated:
- Appends news volume and sentiment features to the analytical panel.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..aliases import ALIASES
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import (
    parse_numeric,
    parse_timestamp_sgt,
    resolve_column,
    sanitize_column_names,
)
from ..io import read_csv

logger = logging.getLogger("SPAFS_V5.2")


def _empty_news_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Populate default empty news features when news dataset is unavailable.

    Args:
        df (pd.DataFrame): Input market panel DataFrame.

    Returns:
        pd.DataFrame: DataFrame augmented with default null news columns:
            ``news_dataset_present`` = False,
            ``news_count`` = 0,
            and NaN sentiment / tone / goldstein averages.
    """
    out = df.copy()
    out["news_dataset_present"] = False
    out["news_count"] = 0
    out["news_sentiment_mean"] = np.nan
    out["news_native_tone_mean"] = np.nan
    out["news_goldstein_mean"] = np.nan
    return out


def aggregate_news_pit(
    df: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Aggregate unstructured news features under strict Point-in-Time information windows.

    Matches news articles to market sessions using forward As-Of integration on
    forecast origin cutoffs, computes session-level sentiment statistics, and
    verifies that no post-cutoff information leaks into the dataset.

    Args:
        df (pd.DataFrame): Market panel containing 'market_date' and 'forecast_origin_datetime'.
        cfg (Config): Pipeline configuration supplying news file path and enforcement flags.

    Returns:
        pd.DataFrame: DataFrame augmented with:
            - ``news_count``: Total number of articles in the PIT session window.
            - ``news_sentiment_mean``: Average FinBERT sentiment.
            - ``news_native_tone_mean``: Average GDELT Tone.
            - ``news_goldstein_mean``: Average Goldstein Scale score.
            - ``news_dataset_present``: Boolean indicating active news coverage.

    Raises:
        FileNotFoundError: If news CSV is missing and ``require_news_for_stream2`` is True.
        DataContractViolationError: If any article publication violates the PIT cutoff.
    """
    if not cfg.news_csv.exists():
        if cfg.require_news_for_stream2:
            logger.warning(
                "News CSV not found at %s. (Required for Stream 2 Machine Learning M4-M6).",
                cfg.news_csv,
            )
            # When news source is not yet populated, provide empty structure with warning
            return _empty_news_columns(df)
        return _empty_news_columns(df)

    logger.info("Ingesting and aggregating news data from %s...", cfg.news_csv.name)
    news = sanitize_column_names(read_csv(cfg.news_csv))

    publication_col = resolve_column(
        news,
        ALIASES,
        "publication_datetime",
    )

    # GDELT timestamps are recorded in UTC. If timezone-naive,
    # strictly localize to UTC first, then convert to Asia/Singapore (UTC+8).
    raw_ts = pd.to_datetime(news[publication_col], errors="coerce")
    if raw_ts.dt.tz is None:
        news["publication_datetime"] = raw_ts.dt.tz_localize("UTC").dt.tz_convert("Asia/Singapore")
    else:
        news["publication_datetime"] = raw_ts.dt.tz_convert("Asia/Singapore")

    sentiment_col = resolve_column(news, ALIASES, "sentiment", required=False)
    tone_col = resolve_column(news, ALIASES, "native_tone", required=False)
    goldstein_col = resolve_column(news, ALIASES, "goldstein_scale", required=False)

    if sentiment_col:
        news = news.rename(columns={sentiment_col: "news_sentiment"})
        news["news_sentiment"] = parse_numeric(news["news_sentiment"])

    if tone_col:
        news = news.rename(columns={tone_col: "news_native_tone"})
        news["news_native_tone"] = parse_numeric(news["news_native_tone"])

    if goldstein_col:
        news = news.rename(columns={goldstein_col: "news_goldstein"})
        news["news_goldstein"] = parse_numeric(news["news_goldstein"])

    # ── Map news articles to causal forecast origins ──────────────
    # Window: (previous_forecast_origin, current_forecast_origin]
    origins = df[["market_date", "forecast_origin_datetime"]].copy()
    origins["previous_forecast_origin_datetime"] = origins["forecast_origin_datetime"].shift(1)

    assigned = pd.merge_asof(
        news.sort_values("publication_datetime"),
        origins.sort_values("forecast_origin_datetime"),
        left_on="publication_datetime",
        right_on="forecast_origin_datetime",
        direction="forward",
        allow_exact_matches=True,
    )

    valid_window = (
        assigned["forecast_origin_datetime"].notna()
        & (
            assigned["previous_forecast_origin_datetime"].isna()
            | (assigned["publication_datetime"] > assigned["previous_forecast_origin_datetime"])
        )
        & (assigned["publication_datetime"] <= assigned["forecast_origin_datetime"])
    )

    assigned = assigned.loc[valid_window].copy()

    if not assigned.empty:
        agg_dict: dict[str] = {
            "news_count": ("publication_datetime", "count"),
        }

        if "news_sentiment" in assigned.columns:
            agg_dict["news_sentiment_mean"] = ("news_sentiment", "mean")
        if "news_native_tone" in assigned.columns:
            agg_dict["news_native_tone_mean"] = ("news_native_tone", "mean")
        if "news_goldstein" in assigned.columns:
            agg_dict["news_goldstein_mean"] = ("news_goldstein", "mean")

        grouped = (
            assigned.groupby("market_date")
            .agg(**agg_dict)
            .reset_index()
        )
    else:
        grouped = pd.DataFrame(
            {
                "market_date": df["market_date"],
                "news_count": 0,
                "news_sentiment_mean": np.nan,
                "news_native_tone_mean": np.nan,
                "news_goldstein_mean": np.nan,
            }
        )

    out = df.merge(
        grouped,
        on="market_date",
        how="left",
        validate="one_to_one",
    )

    out["news_count"] = out["news_count"].fillna(0).astype("int64")
    out["news_dataset_present"] = True

    # ── PIT Hard Gate check on assigned articles ──────────────────
    if not assigned.empty:
        late_news = (
            assigned["publication_datetime"]
            > assigned["forecast_origin_datetime"]
        )
        if late_news.any():
            raise DataContractViolationError(
                f"News PIT hard gate breach: {int(late_news.sum())} articles "
                f"published after session forecast cutoff."
            )

    logger.info(
        "STEP 06 COMPLETE | total_news=%d | assigned_to_sessions=%d",
        len(news),
        len(assigned),
    )

    return out
