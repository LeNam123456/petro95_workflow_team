"""Immutable project configuration for the SPAFS V5.2 data pipeline.

Defines a frozen dataclass ``Config`` that captures every tuneable
parameter — file paths, research windows, PIT time assumptions,
feature hyper-parameters, and audit thresholds — in one place.
All downstream modules receive a ``Config`` instance; no magic
constants should appear outside this file.

A factory function ``build_config`` provides the conventional directory
layout so that callers only need to supply the project root path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Config:
    """Immutable container for every pipeline-wide setting.

    Args:
        root: Project root directory.
        platts_csv: Path to the raw Platts FOB Singapore CSV.
        brent_csv: Path to the raw Brent crude daily CSV.
        news_csv: Path to the raw GDELT news headlines CSV.
        interim_dir: Output directory for intermediate Parquet artifacts.
        processed_dir: Output directory for model-ready datasets.
        report_dir: Output directory for audit JSON / CSV reports.
        min_date: Earliest date in the research window (YYYY-MM-DD).
        max_date: Latest date in the research window (YYYY-MM-DD).
        nlp_start_date: Start date for the NLP-aligned subsample.
        train_end_date: Last date of the training partition.
        oos_start_date: First date of the out-of-sample test partition.
        platts_moc_time_sgt: Platts Market-on-Close time (HH:MM SGT).
        forecast_cutoff_time_sgt: Forecast origin cutoff (HH:MM SGT).
        brent_settlement_available_time_sgt: Brent settlement availability
            time (HH:MM SGT).
        volatility_window: Rolling window size (trading days) for
            trailing volatility.
        tri_regime_multiplier: Multiplier applied to trailing volatility
            to compute the three-regime direction threshold.
        max_return_lag: Maximum number of lagged return features.
        outlier_abs_return_pct: Absolute return threshold (%) for
            flagging potential outliers.
        require_positive_prices: If True, non-positive prices trigger
            a DataContractViolationError.
        require_unique_market_date: If True, duplicate market dates
            trigger a DataContractViolationError.
        require_news_for_stream2: If True, Stream 2 requires non-null
            news features.
        expected_raw_platts_rows: Optional exact row count for the raw
            Platts CSV (sanity check).
        expected_trading_rows: Optional exact trading-day count after
            removing structural holidays.
        expected_synchronized_rows: Optional exact count after Brent
            synchronisation.
        expected_nlp_rows: Optional exact count for the NLP subsample.
    """

    root: Path

    # ── Raw sources ──────────────────────────────────────────────
    platts_csv: Path
    brent_csv: Path
    news_csv: Path

    # ── Output layers ────────────────────────────────────────────
    interim_dir: Path
    processed_dir: Path
    report_dir: Path

    # ── Research windows ─────────────────────────────────────────
    min_date: str = "2008-01-01"
    max_date: str = "2025-12-31"
    nlp_start_date: str = "2017-01-01"
    train_end_date: str = "2019-12-31"
    oos_start_date: str = "2020-01-01"

    # ── PIT assumptions ─────────────────────────────────────────
    platts_moc_time_sgt: str = "16:30"
    forecast_cutoff_time_sgt: str = "08:30"
    brent_settlement_available_time_sgt: str = "03:30"

    # ── Feature parameters ───────────────────────────────────────
    volatility_window: int = 30
    tri_regime_multiplier: float = 0.5
    max_return_lag: int = 3

    # ── Audit rules ──────────────────────────────────────────────
    outlier_abs_return_pct: float = 20.0
    require_positive_prices: bool = True
    require_unique_market_date: bool = True
    require_news_for_stream2: bool = False

    # ── Expected counts (optional sanity-check) ──────────────────
    expected_raw_platts_rows: Optional[int] = None
    expected_trading_rows: Optional[int] = None
    expected_synchronized_rows: Optional[int] = None
    expected_nlp_rows: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate date formats, chronological ordering, and time formats
        at construction time so that invalid configurations fail fast.

        Raises:
            ValueError: If any date string is not valid YYYY-MM-DD, if
                date ordering constraints are violated, or if time strings
                are not valid HH:MM format.
        """
        date_fields = [
            "min_date", "max_date", "nlp_start_date",
            "train_end_date", "oos_start_date",
        ]
        parsed: dict[str, datetime] = {}
        for name in date_fields:
            val = getattr(self, name)
            try:
                parsed[name] = datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Config.{name}='{val}' is not a valid YYYY-MM-DD date."
                )

        if parsed["min_date"] >= parsed["max_date"]:
            raise ValueError("min_date must be strictly before max_date.")
        if parsed["train_end_date"] >= parsed["oos_start_date"]:
            raise ValueError("train_end_date must be before oos_start_date.")

        for time_field in [
            "platts_moc_time_sgt",
            "forecast_cutoff_time_sgt",
            "brent_settlement_available_time_sgt",
        ]:
            val = getattr(self, time_field)
            parts = val.split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                raise ValueError(
                    f"Config.{time_field}='{val}' must be HH:MM format."
                )


def build_config(root: str | Path) -> Config:
    """Create a Config instance with the conventional SPAFS directory layout.

    Args:
        root: Project root directory (str or Path).

    Returns:
        Config: A fully initialised Config with default sub-paths for
            raw data, interim artifacts, processed outputs, and reports.
    """
    root_path = Path(root)
    return Config(
        root=root_path,
        platts_csv=root_path / "data/raw/price_petroleum_platts.csv",
        brent_csv=root_path / "data/raw/brent_crude_daily.csv",
        news_csv=root_path / "data/raw/gdelt_news_headlines.csv",
        interim_dir=root_path / "data/interim",
        processed_dir=root_path / "data/processed",
        report_dir=root_path / "reports/data_quality",
    )


def ensure_directories(config: Config) -> None:
    """Create output directories if they do not already exist.

    Args:
        config: The pipeline configuration whose directory paths
            will be created on disk.

    Returns:
        None
    """
    for path in [config.interim_dir, config.processed_dir, config.report_dir]:
        path.mkdir(parents=True, exist_ok=True)