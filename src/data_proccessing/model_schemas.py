"""Formal Model Feature Schemas and Registry for SPAFS V5.2.

This module acts as the Single Source of Truth (SSOT) and declarative schema registry
for the 7 experimental models (M0 to M6) defined in Section 6 of the SPAFS V5.2
Blueprint.

Key Architectural & Econometric Principles:
1. Strict Feature Whitelisting:
   Replaces negative exclusion (c not in NON_FEATURE_COLUMNS) with explicit positive
   whitelists for each model. This strictly prevents:
   - Non-stationary raw price levels (MG95, brent_close) from distorting ML tree splits.
   - Non-numeric datetime columns (brent_observed_date) from crashing estimators.
   - Carry-forward stale series (unaligned brent_return_pct) from contaminating regressions.
2. Stationarity & Econometric Discipline:
   All whitelisted features are strictly stationary I(0) continuous returns, spreads,
   rolling standard deviations, integer article counts, or binary flags.
3. Declarative Model Specifications:
   Each model defines:
   - Mathematical formulation & model family (Baseline, Econometric, Machine Learning).
   - Target variable (Continuous return vs Binary direction).
   - Target research stream (Stream 1 Econometric 2008–2025 vs Stream 2 ML 2017–2025).
   - Benchmark model against which incremental predictive ability is tested
     (e.g., M3 vs M2 via Wald test; M6 vs M5 via Clark-West test).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import pandas as pd

from .aliases import TARGET_COLUMNS
from .exceptions import DataContractViolationError

logger = logging.getLogger("SPAFS_V5.2")


@dataclass(frozen=True)
class ModelSpec:
    """Declarative specification for an empirical model in the SPAFS V5.2 matrix.

    Args:
        model_id: Unique identifier (e.g., 'M0a', 'M1', 'M5').
        name: Formal economic / machine learning name.
        model_family: Category ('baseline', 'econometric', 'machine_learning').
        stream: Target partition ('stream1' for 2008–2025 or 'stream2' for 2017–2025).
        target: Primary target column name in the dataset.
        features: Strict immutable list of input predictor column names (whitelist).
        description: Methodological description and mathematical formulation.
        benchmark_id: Optional ID of the nested baseline model for comparative testing.
        statistical_tests: List of formal statistical hypothesis tests to execute.
    """

    model_id: str
    name: str
    model_family: Literal["baseline", "econometric", "machine_learning"]
    stream: Literal["stream1", "stream2"]
    target: str
    features: tuple[str, ...]
    description: str
    benchmark_id: Optional[str] = None
    statistical_tests: tuple[str, ...] = field(default_factory=tuple)

    @property
    def num_features(self) -> int:
        """Return the number of input predictive features."""
        return len(self.features)


# ── Canonical Model Registry (M0a to M6) ──────────────────────────

MODEL_REGISTRY: dict[str, ModelSpec] = {
    # ── M0a: Naive Zero Return ────────────────────────────────────
    "M0a": ModelSpec(
        model_id="M0a",
        name="Naive Zero Return (Random Walk / EMH)",
        model_family="baseline",
        stream="stream1",
        target="target_return_pct",
        features=(),
        description="Predicts zero return (E[r_{t+1}] = 0) under the Efficient Market Hypothesis.",
        benchmark_id=None,
        statistical_tests=("diebold_mariano",),
    ),
    # ── M0b: Naive Directional Momentum ───────────────────────────
    "M0b": ModelSpec(
        model_id="M0b",
        name="Naive Directional Momentum",
        model_family="baseline",
        stream="stream1",
        target="target_direction",
        features=("mg95_return_pct",),
        description="Predicts next-day direction based solely on today's price direction sign(r_{MG95, t}).",
        benchmark_id="M0a",
        statistical_tests=("pesaran_timmermann", "mcnemar"),
    ),
    # ── M1: ARMA(1, 1) Univariate Time Series ─────────────────────
    "M1": ModelSpec(
        model_id="M1",
        name="ARMA(1, 1) Univariate Time Series",
        model_family="econometric",
        stream="stream1",
        target="target_return_pct",
        features=("mg95_return_pct", "mg95_return_lag1"),
        description="Classic linear autoregressive moving average on endogenous Mogas 95 returns.",
        benchmark_id="M0a",
        statistical_tests=("diebold_mariano", "wald"),
    ),
    # ── M2: Linear Dynamic Symmetric Regression ───────────────────
    "M2": ModelSpec(
        model_id="M2",
        name="Linear Dynamic Regression (Symmetric Benchmark)",
        model_family="econometric",
        stream="stream1",
        target="target_return_pct",
        features=(
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "spread_mg95_brent_lag1",
        ),
        description="Linear dynamic OLS with Newey-West HAC incorporating Mogas lags, Brent lags, and equilibrium spread.",
        benchmark_id="M1",
        statistical_tests=("wald", "diebold_mariano"),
    ),
    # ── M3: Asymmetric Distributed Lag (ADL) ──────────────────────
    "M3": ModelSpec(
        model_id="M3",
        name="Asymmetric Distributed Lag (RQ1 Core Econometric Model)",
        model_family="econometric",
        stream="stream1",
        target="target_return_pct",
        features=(
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pos",
            "brent_return_neg",
            "brent_return_lag1",
            "spread_mg95_brent_lag1",
        ),
        description=(
            "Asymmetric ADL decomposing Brent shocks into positive (r+) and negative (r-) "
            "components with Newey-West HAC standard errors (5 lags) for RQ1 Wald hypothesis testing."
        ),
        benchmark_id="M2",
        statistical_tests=("wald", "diebold_mariano"),
    ),
    # ── M4: Technical Momentum & Volatility LightGBM ───────────────
    "M4": ModelSpec(
        model_id="M4",
        name="Technical LightGBM (Momentum & Volatility)",
        model_family="machine_learning",
        stream="stream2",
        target="target_return_pct",
        features=(
            "mg95_return_pct",
            "mg95_return_lag1",
            "mg95_return_lag2",
            "mg95_return_lag3",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "brent_return_lag2",
            "brent_return_lag3",
            "vol_mg95_30d",
            "economic_shock_flag",
        ),
        description="Non-linear GBDT capturing autoregressive return momentum and 30-day trailing volatility across 10 random seeds.",
        benchmark_id="M3",
        statistical_tests=("clark_west", "pesaran_timmermann"),
    ),
    # ── M5: Economic Refining Spreads LightGBM ────────────────────
    "M5": ModelSpec(
        model_id="M5",
        name="Economic LightGBM (Refining Economics Benchmark)",
        model_family="machine_learning",
        stream="stream2",
        target="target_return_pct",
        features=(
            # All M4 Technical Features
            "mg95_return_pct",
            "mg95_return_lag1",
            "mg95_return_lag2",
            "mg95_return_lag3",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "brent_return_lag2",
            "brent_return_lag3",
            "vol_mg95_30d",
            "economic_shock_flag",
            # Cross-Product Refining Economics
            "spread_mg95_mg92",
            "spread_mg95_do005",
            "spread_mg95_brent",
            "spread_mg95_brent_lag1",
            "octane_spread_nonpositive_flag",
        ),
        description="GBDT augmented with Octane premium, Diesel substitution spread, and lagged equilibrium crack margin anchor.",
        benchmark_id="M4",
        statistical_tests=("clark_west", "pesaran_timmermann", "mcnemar"),
    ),
    # ── M6: Multimodal Economic + News Sentiment LightGBM ─────────
    "M6": ModelSpec(
        model_id="M6",
        name="Economic + News LightGBM (RQ2 Multimodal Model)",
        model_family="machine_learning",
        stream="stream2",
        target="target_return_pct",
        features=(
            # All M5 Economic Features
            "mg95_return_pct",
            "mg95_return_lag1",
            "mg95_return_lag2",
            "mg95_return_lag3",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "brent_return_lag2",
            "brent_return_lag3",
            "vol_mg95_30d",
            "economic_shock_flag",
            "spread_mg95_mg92",
            "spread_mg95_do005",
            "spread_mg95_brent",
            "spread_mg95_brent_lag1",
            "octane_spread_nonpositive_flag",
            # Point-in-Time News Sentiment & Information Flow
            "news_count",
            "news_sentiment_mean",
            "news_native_tone_mean",
            "news_goldstein_mean",
        ),
        description="Multimodal GBDT combining refining economics with FinBERT polarity and GDELT sentiment for RQ2 Clark-West evaluation.",
        benchmark_id="M5",
        statistical_tests=("clark_west", "pesaran_timmermann", "mcnemar", "shap"),
    ),
}


# ── Public Access & Extraction APIs ───────────────────────────────


def get_model_spec(model_id: str) -> ModelSpec:
    """Retrieve the formal ModelSpec from the registry.

    Args:
        model_id (str): Model identifier ('M0a', 'M0b', 'M1', ..., 'M6').

    Returns:
        ModelSpec: Immutable declarative specification for the requested model.

    Raises:
        KeyError: If *model_id* is not registered in ``MODEL_REGISTRY``.
    """
    if model_id not in MODEL_REGISTRY:
        raise KeyError(
            f"Unknown model_id '{model_id}'. Registered models: {list(MODEL_REGISTRY.keys())}"
        )
    return MODEL_REGISTRY[model_id]


def list_models() -> list[ModelSpec]:
    """Return an ordered list of all registered models in the SPAFS V5.2 matrix.

    Returns:
        list[ModelSpec]: List of all 8 model specifications from M0a to M6.
    """
    return list(MODEL_REGISTRY.values())


def extract_model_matrix(
    df: pd.DataFrame,
    model_id: str,
    *,
    dropna: bool = True,
) -> tuple[pd.DataFrame, pd.Series]:
    """Extract strictly whitelisted predictor matrix (X) and target vector (y).

    Guarantees zero leakage by strictly subsetting features defined in the model's
    formal schema. Any target or metadata columns outside the whitelist are completely excluded.

    Args:
        df (pd.DataFrame): Dataset containing features and target columns.
        model_id (str): Model identifier to extract ('M0a' to 'M6').
        dropna (bool, optional): If True, drops rows with nulls in X or y. Defaults to True.

    Returns:
        tuple[pd.DataFrame, pd.Series]: A two-element tuple containing:
            - **X**: Feature DataFrame containing only the whitelisted predictor columns.
            - **y**: Target Series corresponding to the model's declared target.

    Raises:
        DataContractViolationError: If required features are missing from *df*
            or if target variables leak into *X*.
    """
    spec = get_model_spec(model_id)

    # Validate target presence
    if spec.target not in df.columns:
        raise DataContractViolationError(
            f"Target column '{spec.target}' required by model '{model_id}' not found in DataFrame."
        )

    # Validate all whitelisted features exist
    missing_features = [f for f in spec.features if f not in df.columns]
    if missing_features:
        raise DataContractViolationError(
            f"Model '{model_id}' requires features {missing_features} that are missing from DataFrame."
        )

    # Leakage check: target must NEVER be in X
    overlap = set(spec.features) & TARGET_COLUMNS
    if overlap:
        raise DataContractViolationError(
            f"CRITICAL LEAKAGE: Target variable(s) {overlap} present in feature whitelist for '{model_id}'!"
        )

    # Extract clean subsets
    X = df[list(spec.features)].copy()
    y = df[spec.target].copy()

    if dropna:
        if len(spec.features) > 0:
            valid_mask = X.notna().all(axis=1) & y.notna()
            X = X.loc[valid_mask].reset_index(drop=True)
            y = y.loc[valid_mask].reset_index(drop=True)
        else:
            valid_mask = y.notna()
            X = X.loc[valid_mask].reset_index(drop=True)
            y = y.loc[valid_mask].reset_index(drop=True)

    logger.debug(
        "Extracted matrix for %s: X=%s, y=%s (rows=%d)",
        model_id,
        list(X.columns),
        y.name,
        len(y),
    )
    return X, y
