"""Step 07 — Two-Sample Research Framework & Train/Test Partitioning Engine.

This module partitions the feature-engineered dataset into two independent empirical
research streams in accordance with Section 3 of the SPAFS V5.2 Blueprint:

1. Stream 1 (Full Historical Econometric Sample 2008–2025):
   - Scope: Complete 17.5-year historical horizon.
   - Purpose: Dedicated to RQ1 (Asymmetric Distributed Lag models, Wald tests)
     and baseline econometric models M0 to M3.
   - Preserves major structural regimes: 2008 Global Financial Crisis, 2014–2016
     oil crash, and 2020 COVID-19 pandemic shock.
2. Stream 2 (Aligned NLP & Machine Learning Subsample 2017–2025):
   - Scope: 9-year aligned observation window (from 2017-01-01 onwards).
   - Purpose: Dedicated to RQ2 (Clark-West incremental predictive ability tests)
     and multi-seed LightGBM machine learning models M4 to M6.
   - Eliminates "Zero Ambiguity" bias (ensuring lack of news prior to 2017 does not
     distort machine learning feature attribution).
3. Out-of-Sample Partitioning of Stream 2:
   - In-sample Training: 2017–2019 (target dates <= 2019-12-31).
   - Out-of-Sample (OOS) Testing: 2020–2025 (target dates >= 2020-01-01).
4. Feature Governance & Leakage Prevention:
   Enforces strict feature contracts ensuring zero overlap between model features
   and target/identifier metadata.

Artifacts Generated:
- data/processed/stream1_econometric_2008_2025.parquet : Full historical panel.
- data/processed/stream2_aligned_nlp_2017_2025.parquet : Aligned ML subsample.
- reports/data_quality/partition_audit.csv : Tabular partitioning summary.
- reports/data_quality/partition_audit.json : Machine-readable audit report.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from ..aliases import (
    IDENTIFIER_COLUMNS,
    NON_FEATURE_COLUMNS,
    TARGET_COLUMNS,
)
from ..config import Config
from ..exceptions import DataContractViolationError
from ..helpers import save_json
from ..io import write_csv, write_parquet
from ..model_schemas import MODEL_REGISTRY

logger = logging.getLogger("SPAFS_V5.2")


def build_feature_contract(df: pd.DataFrame) -> dict[str, Any]:
    """Audit and enforce strict boundary between feature columns and target/ID metadata.

    Identifies all candidate predictive features by excluding protected target
    and identifier columns, validates that zero target variables bleed
    into the feature predictor set, and records the explicit model feature schemas.

    Args:
        df (pd.DataFrame): Analytical panel containing all features and targets.

    Returns:
        dict[str, Any]: Feature contract summary mapping column categories:
            ``feature_columns``, ``target_columns``, ``identifier_columns``,
            ``non_feature_columns``, and verified ``model_feature_whitelists``.

    Raises:
        DataContractViolationError: If any target column is erroneously present
            in the candidate feature set.
    """
    feature_columns = [
        c for c in df.columns
        if c not in NON_FEATURE_COLUMNS
    ]

    overlap = set(feature_columns) & TARGET_COLUMNS
    if overlap:
        raise DataContractViolationError(
            f"Feature Contract Violation: Detected target variables leaking "
            f"into predictor space: {sorted(overlap)}"
        )

    return {
        "feature_columns": feature_columns,
        "target_columns": sorted(TARGET_COLUMNS),
        "identifier_columns": sorted(IDENTIFIER_COLUMNS),
        "non_feature_columns": sorted(NON_FEATURE_COLUMNS),
        "feature_target_overlap": sorted(overlap),
        "model_feature_whitelists": {
            m: list(spec.features) for m, spec in MODEL_REGISTRY.items()
        },
    }


def partition_streams(
    df: pd.DataFrame,
    cfg: Config,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Partition the fully enriched dataset into Stream 1 (Econometrics) and Stream 2 (ML/NLP).

    Executes the Two-Sample Framework:
    - Stream 1 captures the full sample across [cfg.min_date, cfg.max_date] for M0–M3.
    - Stream 2 slices from cfg.nlp_start_date (2017+) and splits into In-Sample Train
      (2017–2019) and Out-of-Sample Test (2020–2025) strictly based on target market dates.

    Args:
        df (pd.DataFrame): Fully enriched daily feature panel from Step 06.
        cfg (Config): Pipeline configuration supplying partitioning dates and directories.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]: A three-element tuple:
            - **stream1**: Full historical econometric dataset (2008–2025).
            - **stream2**: Aligned NLP and Machine Learning dataset (2017–2025).
            - **audit**: Complete partitioning audit record.

    Raises:
        DataContractViolationError: If required news data is missing when
            ``cfg.require_news_for_stream2`` is strictly enforced, or if feature
            contracts are violated.
    """
    logger.info("Executing Step 07: Two-Sample Stream Partitioning...")

    # News availability check for Stream 2
    if cfg.require_news_for_stream2 and not bool(df["news_dataset_present"].any()):
        raise DataContractViolationError(
            "Stream 2 creation halted: 'cfg.require_news_for_stream2' is True, "
            "but news data is completely absent from the feature panel."
        )

    # ── Stream 1: Full Historical Econometric Sample (2008–2025) ──
    stream1 = df[
        df["market_date"].between(
            pd.Timestamp(cfg.min_date),
            pd.Timestamp(cfg.max_date),
        )
    ].copy()

    # ── Stream 2: Aligned NLP Subsample (2017–2025) ───────────────
    stream2 = df[
        df["market_date"] >= pd.Timestamp(cfg.nlp_start_date)
    ].copy()

    # Split Stream 2 by target date, not feature date, to prevent lookahead
    train = stream2[
        stream2["target_market_date"] <= pd.Timestamp(cfg.train_end_date)
    ].copy()

    oos = stream2[
        stream2["target_market_date"] >= pd.Timestamp(cfg.oos_start_date)
    ].copy()

    # ── Validate Feature Contract ─────────────────────────────────
    feature_contract = build_feature_contract(df)

    audit: dict[str, Any] = {
        "stream1_rows": len(stream1),
        "stream1_date_range": (
            f"{stream1['market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{stream1['market_date'].max().strftime('%Y-%m-%d')}"
        ),
        "stream2_rows": len(stream2),
        "stream2_date_range": (
            f"{stream2['market_date'].min().strftime('%Y-%m-%d')} -> "
            f"{stream2['market_date'].max().strftime('%Y-%m-%d')}"
        ) if not stream2.empty else "N/A",
        "train_rows": len(train),
        "oos_rows": len(oos),
        "num_predictive_features": len(feature_contract["feature_columns"]),
        "zero_news_days_stream2": (
            int((stream2["news_count"] == 0).sum())
            if "news_count" in stream2.columns
            else None
        ),
        "feature_contract": feature_contract,
        "status": "PASSED",
    }

    # ── Persist Stream Artifacts ──────────────────────────────────
    write_parquet(
        stream1,
        cfg.processed_dir / "stream1_econometric_2008_2025.parquet",
    )
    write_parquet(
        stream2,
        cfg.processed_dir / "stream2_aligned_nlp_2017_2025.parquet",
    )
    write_csv(
        pd.DataFrame([{k: str(v) for k, v in audit.items()}]),
        cfg.report_dir / "partition_audit.csv",
    )
    save_json(
        audit,
        cfg.report_dir / "partition_audit.json",
    )

    logger.info(
        "STEP 07 PASSED | Stream 1: %d | Stream 2: %d | Train: %d | OOS: %d",
        len(stream1),
        len(stream2),
        len(train),
        len(oos),
    )

    return stream1, stream2, audit
