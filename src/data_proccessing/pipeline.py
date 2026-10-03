"""End-to-End Point-in-Time Data Engineering Pipeline for SPAFS V5.2.

This orchestrator executes the complete multi-layer data preparation pipeline,
progressing from raw ingestion to model-ready partitioned feature datasets:

Pipeline Execution Flow:
1. Gate 1.1 (Platts Data Contract):
   Ingests, cleans, validates schema, and filters structural holidays.
2. Gate 1.2 (Brent Continuous Futures Contract):
   Ingests continuous Brent futures, validates chronology/positivity, computes
   log returns, and audits fat-tail shock events.
3. Gate 1.3 (Temporal As-Of Alignment & Canonical Panel):
   Synchronizes Platts and Brent across timezones under the 08:30 SGT Cutoff,
   enforcing the Point-in-Time (PIT) hard gate.
4. Step 04 (Returns & Target Formulation):
   Derives continuous return predictors and formulates forward-looking targets (r_{t+1}, y_{t+1}).
5. Step 05 (Analytical Market Features & Refining Economics):
   Computes Octane spread, Diesel spread, Crack margin, Lagged equilibrium anchor,
   asymmetric shocks (r+, r-), trailing 30-day volatility, and 3-regime dynamic targets.
6. Step 06 (Point-in-Time News Sentiment Aggregator):
   Integrates GDELT/FinBERT features within the causal session cutoff window.
7. Step 07 (Two-Sample Partitioning):
   Splits into Stream 1 (Full 2008–2025 econometric panel) and Stream 2 (Aligned 2017–2025
   Train/OOS ML subsample).
8. Step 08 (Weekly Temporal Aggregation Robustness):
   Produces the aggregated weekly dataset (N ≈ 900) for cross-frequency robustness testing.

Artifacts Generated:
- Full interim and processed datasets in data/interim/ and data/processed/.
- Complete quality audit reports in reports/data_quality/.
- Master pipeline manifest in reports/data_quality/pipeline_manifest.json.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import pandas as pd

from .config import Config, ensure_directories
from .data_handling.alignment import build_canonical_panel
from .data_handling.market_features import build_market_features
from .data_handling.news_pit import aggregate_news_pit
from .data_handling.patrition import partition_streams
from .data_handling.target import add_returns_and_targets
from .data_handling.validate_brent import validate_brent
from .data_handling.validate_plats import validate_platts
from .data_handling.weekly import build_weekly_price_robustness
from .helpers import save_json
from .io import write_csv, write_parquet

logger = logging.getLogger("SPAFS_V5.2")


def run_pipeline(cfg: Config) -> dict[str, Any]:
    """Execute the complete end-to-end SPAFS V5.2 data preparation pipeline.

    Orchestrates all 8 sequential stages, enforces data contracts and Point-in-Time
    governance, generates analytical feature sets, and outputs research datasets
    and comprehensive audit trails.

    Args:
        cfg (Config): Pipeline configuration containing file paths, research windows,
            and audit rules.

    Returns:
        dict[str, Any]: Comprehensive execution manifest detailing dataset row counts,
            audit metrics for every stage, and overall completion status.

    Raises:
        DataContractViolationError: If any data contract gate or Point-in-Time constraint fails.
        FileNotFoundError: If required raw data sources cannot be located.
    """
    logger.info("==================================================================")
    logger.info("STARTING SPAFS V5.2 END-TO-END POINT-IN-TIME DATA PIPELINE")
    logger.info("==================================================================")
    ensure_directories(cfg)

    # ── Step 01: Platts Data Contract Validation ──────────────────
    platts, platts_audit = validate_platts(cfg)

    # ── Step 02: Brent Validation & Continuity ────────────────────
    brent, brent_audit = validate_brent(cfg)

    # ── Step 03: Canonical Synchronized Market Panel & PIT Gate ───
    canonical, canonical_audit = build_canonical_panel(
        platts,
        brent,
        cfg,
        alignment_mode="asof",
    )

    # ── Step 04: Returns & Next-Trading-Day Targets ───────────────
    daily = add_returns_and_targets(canonical, cfg)

    # ── Step 05: Analytical Market Features & Refining Economics ──
    daily = build_market_features(daily, cfg)

    # ── Step 06: Point-in-Time News Sentiment Aggregation ─────────
    daily = aggregate_news_pit(daily, cfg)

    # Persist the fully-featured daily master panel
    write_parquet(
        daily,
        cfg.processed_dir / "spafs_full_features_daily.parquet",
    )

    # ── Step 07: Two-Sample Research Stream Partitioning ──────────
    stream1, stream2, partition_audit = partition_streams(
        daily,
        cfg,
    )

    # ── Step 08: Weekly Price Robustness Aggregation ──────────────
    weekly, weekly_audit = build_weekly_price_robustness(daily, cfg)

    # ── Master Pipeline Manifest ──────────────────────────────────
    manifest: dict[str, Any] = {
        "pipeline": "SPAFS_V5.2",
        "status": "PASSED",
        "config": {
            k: str(v) if hasattr(v, "__fspath__") else v
            for k, v in asdict(cfg).items()
        },
        "row_counts": {
            "canonical_panel": len(canonical),
            "daily_full_features": len(daily),
            "stream1_econometric": len(stream1),
            "stream2_aligned_nlp": len(stream2),
            "weekly_robustness": len(weekly),
        },
        "audits": {
            "gate_1_1_platts": platts_audit,
            "gate_1_2_brent": brent_audit,
            "gate_1_3_canonical": canonical_audit,
            "step_07_partition": partition_audit,
            "step_08_weekly": weekly_audit,
        },
    }

    save_json(
        manifest,
        cfg.report_dir / "pipeline_manifest.json",
    )
    write_csv(
        pd.DataFrame([
            {
                "pipeline": "SPAFS_V5.2",
                "status": "PASSED",
                "canonical_rows": len(canonical),
                "stream1_rows": len(stream1),
                "stream2_rows": len(stream2),
                "weekly_rows": len(weekly),
            }
        ]),
        cfg.report_dir / "pipeline_manifest.csv",
    )

    logger.info("==================================================================")
    logger.info("SPAFS V5.2 PIPELINE EXECUTION COMPLETED SUCCESSFULLY (ALL GATES PASSED)")
    logger.info("==================================================================")
    return manifest
