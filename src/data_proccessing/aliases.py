"""Canonical column-name aliases and semantic column sets for SPAFS V5.2.

Centralises every raw-source naming convention into a single registry.
Processing modules must import aliases from here instead of scattering
hard-coded column names across the codebase. This guarantees that a
column rename in the upstream CSV only requires a one-line edit.

Column sets (TARGET_COLUMNS, IDENTIFIER_COLUMNS, NON_FEATURE_COLUMNS)
enforce a strict boundary between model features and metadata so that
no identifier or label can accidentally leak into the feature matrix.
"""

from __future__ import annotations

# ── Alias registry ──────────────────────────────────────────────
# Key   = canonical (logical) name used throughout the pipeline.
# Value = list of known raw-file variants, ordered by likelihood.

ALIASES: dict[str, list[str]] = {
    "market_date": [
        "market_date", "Market_Date", "date", "Date", "DATE",
        "trading_date", "TradeDate", "Ngày", "ngày",
    ],
    "MG95": [
        "MG95", "MG95_USD_BBL", "MOGAS95", "MOGAS_95",
        "Mogas95", "Platts_MG95", "FOB_SINGAPORE_MOGAS_95",
    ],
    "MG92": [
        "MG92", "MG92_USD_BBL", "MOGAS92", "MOGAS_92",
        "Mogas92", "Platts_MG92", "FOB_SINGAPORE_MOGAS_92",
    ],
    "DO_001": [
        "DO_001", "DO001", "DO_0.001", "DIESEL_001", "DO 0.001", "DO 0.001%",
        "DO_0.001%", "GASOIL_001", "Platts_DO_001", "Platts_Gasoil_0.001",
    ],
    "DO_005": [
        "DO_005", "DO005", "DO_0.05", "DIESEL_005", "DO 0.005", "DO 0.005%",
        "DO_0.05%", "GASOIL_005", "Platts_DO_005", "Platts_Gasoil_0.05",
    ],
    "brent_close": [
        "Close", "close", "Adj Close", "adj_close",
        "BZ=F", "Brent", "brent_close", "brent_price",
    ],
    "publication_datetime": [
        "publication_datetime", "published_datetime", "published_at",
        "publication_time", "timestamp", "datetime", "DateTime",
    ],
    "availability_datetime": [
        "availability_datetime", "available_datetime", "ingested_at",
        "loaded_at", "availability_time",
    ],
    "sentiment": [
        "FINBERT_SENTIMENT", "finbert_sentiment", "sentiment",
        "SENTIMENT", "sentiment_score",
    ],
    "native_tone": [
        "GDELT_TONE", "gdelt_tone", "tone", "Tone",
    ],
    "goldstein_scale": [
        "GoldsteinScale", "goldstein_scale", "goldstein",
    ],
}

# ── Platts price series required for validation ─────────────────

PLATTS_PRICE_COLUMNS: list[str] = ["MG95", "MG92", "DO_001", "DO_005"]

# ── Semantic column sets ────────────────────────────────────────

TARGET_COLUMNS: set[str] = {
    "target_market_date",
    "target_return_pct",
    "target_direction",
    "target_direction_tri",
    "target_outlier_flag",
}

IDENTIFIER_COLUMNS: set[str] = {
    "market_date",
    "forecast_origin_datetime",
    "observation_datetime",
    "publication_datetime",
    "availability_datetime",
    "target_market_date",
    "availability_datetime_is_proxy",
    "publication_datetime_is_proxy",
    "brent_availability_datetime",
    "brent_availability_datetime_is_proxy",
    "news_dataset_present",
}

NON_FEATURE_COLUMNS: set[str] = TARGET_COLUMNS | IDENTIFIER_COLUMNS
