"""Formal Model Feature Schemas and Registry for SPAFS V5.2.

This module acts as the Single Source of Truth (SSOT) and declarative schema registry
for the 7 experimental models (M0 to M6) defined in Section 6 of the SPAFS V5.2
Blueprint.

Key Architectural & Econometric Principles:
1. Strict Feature Whitelisting & Zero Target Leakage:
   Replaces negative exclusion (c not in NON_FEATURE_COLUMNS) with explicit positive
   whitelists for each model. Target variables ('target_return_pct', 'target_direction')
   are strictly separated from predictor matrices X with hard programmatic assert guards.
2. Distinct Ingestion Paradigms (input_mode):
   Explicitly differentiates between:
   - 'null_baseline': Zero features / constant / directional sign heuristic (M0a, M0b).
   - 'univariate_series': 1D endogenous return series fitted via Gaussian MLE / Kalman filter (M1 ARMA).
   - 'feature_matrix': 2D design matrix of stationary predictors for OLS or GBDT (M2 to M6).
3. Task Separation & Pairwise Comparison Governance:
   Differentiates continuous regression from binary directional classification.
   Enforces valid pairwise model comparison (no cross-task McNemar testing).
4. Stationarity & Econometric Discipline:
   All whitelisted features are strictly stationary I(0) continuous returns, crack spreads,
   rolling standard deviations, or binary shock flags.
5. Point-in-Time Audit Metadata:
   ModelDataMatrix encapsulates X, y, dates, and full row-level audit metadata (row_meta)
   verifying chronological monotonicity and numeric finiteness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import numpy as np
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
        task: Supervised learning task ('regression' or 'classification').
        input_mode: Data ingestion paradigm:
            - 'null_baseline': Zero features / constant / simple directional rule.
            - 'univariate_series': Endogenous 1D time-series fitted via MLE / Kalman filter (e.g., ARIMA).
            - 'feature_matrix': Standard 2D design matrix of exogenous/lagged predictors (OLS/GBDT).
        stream: Target partition ('stream1' for 2008–2025 or 'stream2' for 2017–2025).
        target: Primary target column name in the dataset.
        features: Strict immutable list of input predictor column names (whitelist).
        description: Methodological description and mathematical formulation.
        benchmark_id: Optional ID of the benchmark model for comparative testing (must share same task).
        statistical_tests: List of formal statistical hypothesis tests to execute.
    """

    model_id: str
    name: str
    model_family: Literal["baseline", "econometric", "machine_learning"]
    task: Literal["regression", "classification"]
    input_mode: Literal["null_baseline", "univariate_series", "feature_matrix"]
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
        task="regression",
        input_mode="null_baseline",
        stream="stream1",
        target="target_return_pct",
        features=(),
        description="Predicts zero return (E[r_{t+1}] = 0) under the Efficient Market Hypothesis. Global regression baseline.",
        benchmark_id=None,
        statistical_tests=(),
    ),
    # ── M0b: Naive Directional Momentum ───────────────────────────
    "M0b": ModelSpec(
        model_id="M0b",
        name="Naive Directional Momentum",
        model_family="baseline",
        task="classification",
        input_mode="null_baseline",
        stream="stream1",
        target="target_direction",
        features=("mg95_return_pct",),
        description="Predicts next-day direction based solely on today's observed return direction sign(r_{MG95, t}). Independent classification baseline.",
        benchmark_id=None,
        statistical_tests=("pesaran_timmermann",),
    ),
    # ── M1: ARMA(1, 1) Univariate Time Series ─────────────────────
    "M1": ModelSpec(
        model_id="M1",
        name="ARMA(1, 1) Univariate Time Series (MLE / Kalman Filter)",
        model_family="econometric",
        task="regression",
        input_mode="univariate_series",
        stream="stream1",
        target="target_return_pct",
        features=("mg95_return_pct",),
        description=(
            "Classic univariate linear autoregressive moving average on endogenous Mogas 95 returns. "
            "Estimated via Gaussian Maximum Likelihood (MLE) using Kalman Filter state-space recursion, "
            "NOT via static OLS regression. Evaluated against M0a via Diebold-Mariano test."
        ),
        benchmark_id="M0a",
        statistical_tests=("diebold_mariano", "ljung_box"),
    ),
    # ── M2: Linear Dynamic Symmetric Regression ───────────────────
    "M2": ModelSpec(
        model_id="M2",
        name="Linear Dynamic Regression (Symmetric Benchmark)",
        model_family="econometric",
        task="regression",
        input_mode="feature_matrix",
        stream="stream1",
        target="target_return_pct",
        features=(
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "spread_mg95_brent_lag1",
        ),
        description=(
            "Linear dynamic OLS with Newey-West HAC standard errors (5 lags) incorporating Mogas lags, "
            "symmetric Brent lags, and lagged gasoline-crude crack spread as mean-reversion anchor."
        ),
        benchmark_id="M1",
        statistical_tests=("diebold_mariano", "wald"),
    ),
    # ── M3: Asymmetric Distributed Lag (ADL) ──────────────────────
    "M3": ModelSpec(
        model_id="M3",
        name="Asymmetric Distributed Lag (RQ1 Core Econometric Model)",
        model_family="econometric",
        task="regression",
        input_mode="feature_matrix",
        stream="stream1",
        target="target_return_pct",
        features=(
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pos",
            "brent_return_neg",
            "brent_return_pos_lag1",
            "brent_return_neg_lag1",
            "spread_mg95_brent_lag1",
        ),
        description=(
            "Asymmetric ADL decomposing contemporaneous (t) and lagged (t-1) Brent shocks "
            "into positive (r+) and negative (r-) branches with Newey-West HAC standard errors (5 lags). "
            "Enables rigorous Wald testing of contemporaneous asymmetry (H0: beta_0+ = beta_0-), "
            "cumulative long-run asymmetry (H0: beta_0+ + beta_1+ = beta_0- + beta_1-), "
            "and joint nested restriction against M2 (H0: beta_0+=beta_0- and beta_1+=beta_1-)."
        ),
        benchmark_id="M2",
        statistical_tests=(
            "wald_contemporaneous",
            "wald_cumulative",
            "wald_joint_nested",
            "diebold_mariano",
        ),
    ),
    # ── M4: Technical Momentum & Volatility LightGBM ───────────────
    "M4": ModelSpec(
        model_id="M4",
        name="Technical LightGBM (Momentum & Volatility)",
        model_family="machine_learning",
        task="regression",
        input_mode="feature_matrix",
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
        description=(
            "Non-linear GBDT capturing autoregressive return momentum and 30-day trailing volatility. "
            "Compared against linear ADL M3 out-of-sample via Diebold-Mariano (HLN 1997)."
        ),
        benchmark_id="M3",
        statistical_tests=("diebold_mariano_hln", "pesaran_timmermann"),
    ),
    # ── M5: Economic Refining Spreads LightGBM ────────────────────
    "M5": ModelSpec(
        model_id="M5",
        name="Economic LightGBM (Refining Economics Benchmark)",
        model_family="machine_learning",
        task="regression",
        input_mode="feature_matrix",
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
        description=(
            "GBDT augmented with Octane premium, Diesel substitution spread, and refining crack margins. "
            "Evaluated against M4 via Diebold-Mariano (HLN 1997) and Pesaran-Timmermann direction test."
        ),
        benchmark_id="M4",
        statistical_tests=("diebold_mariano_hln", "pesaran_timmermann"),
    ),
    # ── M6: Multimodal Economic + News Sentiment LightGBM ─────────
    "M6": ModelSpec(
        model_id="M6",
        name="Economic + News LightGBM (RQ2 Multimodal Model)",
        model_family="machine_learning",
        task="regression",
        input_mode="feature_matrix",
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
        description=(
            "Multimodal GBDT combining refining economics with FinBERT polarity and GDELT sentiment. "
            "Primary comparative evaluation against M5 via Diebold-Mariano (HLN 1997) with HAC variance, "
            "Pesaran-Timmermann directional test, and SHAP feature attributions."
        ),
        benchmark_id="M5",
        statistical_tests=("diebold_mariano_hln", "pesaran_timmermann", "shap"),
    ),
}


# ── Formal Pairwise Comparison Registry ───────────────────────────


@dataclass(frozen=True)
class ComparisonSpec:
    """Formal pairwise comparative hypothesis test specification.

    Enforces methodological validity by ensuring candidate and benchmark models
    belong to the exact same learning task (regression vs regression, classification vs classification)
    and target variable. Prevents invalid cross-task statistical comparisons.
    """

    candidate_id: str
    benchmark_id: str
    task: Literal["regression", "classification"]
    eval_stream: Literal["stream1", "stream2"]
    primary_test: Literal["diebold_mariano_hln", "wald_nested", "pesaran_timmermann"]
    loss_metric: Literal["squared_error", "absolute_error", "directional_accuracy"]
    hypothesis: str
    requires_cross_stream_alignment: bool = False


PAIRWISE_COMPARISONS: tuple[ComparisonSpec, ...] = (
    ComparisonSpec(
        candidate_id="M1",
        benchmark_id="M0a",
        task="regression",
        eval_stream="stream1",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0: ARMA(1,1) M1 does not outperform Naive Zero Return M0a in OOS loss differential.",
    ),
    ComparisonSpec(
        candidate_id="M2",
        benchmark_id="M1",
        task="regression",
        eval_stream="stream1",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0: Symmetric Dynamic M2 does not outperform Univariate ARMA M1 in OOS loss differential.",
    ),
    ComparisonSpec(
        candidate_id="M3",
        benchmark_id="M2",
        task="regression",
        eval_stream="stream1",
        primary_test="wald_nested",
        loss_metric="squared_error",
        hypothesis="H0 (RQ1 Joint): M3 collapses to M2 (beta_0+ = beta_0- and beta_1+ = beta_1-).",
    ),
    ComparisonSpec(
        candidate_id="M3",
        benchmark_id="M2",
        task="regression",
        eval_stream="stream1",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0: Asymmetric ADL M3 does not improve OOS forecast accuracy over Symmetric M2.",
    ),
    ComparisonSpec(
        candidate_id="M4",
        benchmark_id="M3",
        task="regression",
        eval_stream="stream2",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0: Non-linear GBDT M4 does not outperform linear ADL M3 out-of-sample on Stream 2 test window (2020-2025).",
        requires_cross_stream_alignment=True,
    ),
    ComparisonSpec(
        candidate_id="M5",
        benchmark_id="M4",
        task="regression",
        eval_stream="stream2",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0: Refining spreads (M5) do not reduce OOS forecast error over technical momentum (M4).",
    ),
    ComparisonSpec(
        candidate_id="M6",
        benchmark_id="M5",
        task="regression",
        eval_stream="stream2",
        primary_test="diebold_mariano_hln",
        loss_metric="squared_error",
        hypothesis="H0 (RQ2): Multimodal news features (M6) do not reduce OOS forecast error over refining spreads (M5) on common news-available sample.",
    ),
)


# ── Model Data Matrix Container ───────────────────────────────────


@dataclass(frozen=True)
class ModelDataMatrix:
    """Immutable container holding extracted model features, target, dates, and audit metadata.

    Provides dual interface:
    1. Unpacking compatibility: ``X, y = matrix`` works seamlessly.
    2. Attribute access: ``matrix.X``, ``matrix.y``, ``matrix.dates``, ``matrix.row_meta``, ``matrix.spec``.

    Both ``X`` and ``y`` have their index set to ``market_date`` DatetimeIndex,
    enabling natural date slicing (e.g. ``X.loc['2020-01-01':'2025-12-31']``).
    """

    X: pd.DataFrame
    y: pd.Series
    dates: pd.Series
    spec: ModelSpec
    row_meta: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())

    def __iter__(self):
        """Allow tuple unpacking: X, y = extract_model_matrix(...)."""
        return iter((self.X, self.y))

    def __getitem__(self, idx: int) -> Any:
        """Allow indexing: matrix[0] -> X, matrix[1] -> y."""
        return (self.X, self.y)[idx]

    def __len__(self) -> int:
        """Return the number of observations (rows) in the matrix."""
        return len(self.y)

    @property
    def num_observations(self) -> int:
        """Return the number of observations (rows)."""
        return len(self.y)

    @property
    def num_features(self) -> int:
        """Return the number of whitelisted predictor columns."""
        return len(self.X.columns)

    @property
    def start_date(self) -> str:
        """Return the ISO start date of the sample."""
        return str(pd.to_datetime(self.dates.iloc[0]).date()) if len(self.dates) > 0 else ""

    @property
    def end_date(self) -> str:
        """Return the ISO end date of the sample."""
        return str(pd.to_datetime(self.dates.iloc[-1]).date()) if len(self.dates) > 0 else ""


@dataclass(frozen=True)
class MulticollinearityReport:
    """Diagnostic report assessing collinearity among predictor features.

    Evaluates Belsley-Kuh-Welsch (1980) Condition Number and Variance Inflation Factors (VIF).
    Provides automated risk classification:
    - Condition Number >= 30.0 or any VIF >= 10.0: Severe multicollinearity.
    - Condition Number >= 15.0 or any VIF >= 5.0: Moderate multicollinearity.
    - Otherwise: Low / benign collinearity.
    """

    model_id: str
    num_features: int
    condition_number: float
    vif_scores: dict[str, float]
    max_vif_feature: str
    max_vif_value: float
    has_severe_multicollinearity: bool
    warning_message: Optional[str] = None


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
    common_mask: Optional[pd.Series] = None,
) -> ModelDataMatrix:
    """Extract strictly whitelisted predictor matrix (X) and target vector (y).

    Guarantees zero leakage by strictly subsetting features defined in the model's
    formal schema. Any target or metadata columns outside the whitelist are completely excluded.
    Preserves market_date as the DatetimeIndex of both X and y.

    Enforces automated assert guards:
    - Target variables are strictly absent from X.
    - Dates are strictly monotonically increasing.
    - No infinite (Inf, -Inf) values in X or y.

    Args:
        df (pd.DataFrame): Dataset containing features, target, and 'market_date'.
        model_id (str): Model identifier to extract ('M0a' to 'M6').
        dropna (bool, optional): If True, drops rows with nulls in X or y. Defaults to True.
        common_mask (pd.Series, optional): Optional boolean mask to enforce an exact
            common estimation sample across multiple models.

    Returns:
        ModelDataMatrix: Container with (X, y, dates, spec, row_meta), unpackable as ``X, y = ...``.

    Raises:
        DataContractViolationError: If required features/target are missing, if targets leak into X,
            if temporal order is violated, or if M6 is requested on a dataset without ingested news.
    """
    spec = get_model_spec(model_id)

    # 1. Hard Assertion: Feature whitelist must NEVER contain target variables
    for target_col in TARGET_COLUMNS:
        if target_col in spec.features:
            raise DataContractViolationError(
                f"CRITICAL LEAKAGE: Target variable '{target_col}' declared in feature whitelist of '{model_id}'!"
            )

    # 2. Validate target presence in dataset
    if spec.target not in df.columns:
        raise DataContractViolationError(
            f"Target column '{spec.target}' required by model '{model_id}' not found in DataFrame."
        )

    # 3. Validate all whitelisted features exist in dataset
    missing_features = [f for f in spec.features if f not in df.columns]
    if missing_features:
        raise DataContractViolationError(
            f"Model '{model_id}' requires features {missing_features} that are missing from DataFrame."
        )

    # 4. Multimodal availability check for M6 (fail-fast instead of returning 0 rows)
    if any("news_" in f for f in spec.features):
        if "news_dataset_present" in df.columns and not bool(df["news_dataset_present"].any()):
            raise DataContractViolationError(
                f"Model '{model_id}' requires multimodal news features {list(spec.features)}, "
                "but the dataset has 'news_dataset_present' == False (Market-Only Baseline mode). "
                "Cannot extract M6 matrix without ingested GDELT/FinBERT data. "
                "To resolve: Run Step 06 with GDELT news data or use economic models M0a through M5."
            )

    # 5. Extract raw subsets
    X = df[list(spec.features)].copy()
    y = df[spec.target].copy()

    # 6. Hard Contract Enforcement: Target columns must NEVER be in X DataFrame
    if "target_return_pct" in X.columns or "target_direction" in X.columns:
        raise DataContractViolationError(
            f"CRITICAL LEAKAGE: Target column found in predictor matrix X for '{model_id}'!"
        )

    # 7. Extract dates and metadata
    if "market_date" in df.columns:
        dates_raw = pd.to_datetime(df["market_date"])
    else:
        dates_raw = pd.Series(pd.to_datetime(df.index), index=df.index)

    # 8. Compute valid row mask
    if common_mask is not None:
        valid_mask = common_mask & y.notna()
        if len(spec.features) > 0:
            valid_mask = valid_mask & X.notna().all(axis=1)
    elif dropna:
        if len(spec.features) > 0:
            valid_mask = X.notna().all(axis=1) & y.notna()
        else:
            valid_mask = y.notna()
    else:
        valid_mask = pd.Series(True, index=df.index)

    # 9. Filter data and set DatetimeIndex
    filtered_dates = dates_raw.loc[valid_mask].reset_index(drop=True)
    dt_index = pd.DatetimeIndex(filtered_dates)

    X = X.loc[valid_mask].copy()
    y = y.loc[valid_mask].copy()
    X.index = dt_index
    y.index = dt_index

    # 10. Extract row metadata for point-in-time auditing
    meta_cols = [
        c
        for c in [
            "market_date",
            "brent_observed_date",
            "brent_observed_time_sgt",
            "target_market_date",
            "economic_shock_flag",
        ]
        if c in df.columns
    ]
    row_meta = df.loc[valid_mask, meta_cols].copy()
    row_meta.index = dt_index

    # 11. Rigorous Integrity Assertions
    if len(filtered_dates) > 1:
        if not filtered_dates.is_monotonic_increasing:
            raise DataContractViolationError(
                f"TEMPORAL INTEGRITY VIOLATION: Market dates for '{model_id}' are not strictly monotonically increasing!"
            )
        if not filtered_dates.is_unique:
            raise DataContractViolationError(
                f"TEMPORAL INTEGRITY VIOLATION: Duplicate market dates detected in sample for '{model_id}'!"
            )

    # Check numeric feature data types (fail-fast against object/string columns)
    if len(spec.features) > 0 and len(X) > 0:
        non_numeric_cols = [c for c in X.columns if not pd.api.types.is_numeric_dtype(X[c])]
        if non_numeric_cols:
            raise DataContractViolationError(
                f"DTYPE VIOLATION: Non-numeric feature columns detected in X for '{model_id}': {non_numeric_cols}"
            )

    # Check finite numbers (no NaN after filtering, no Inf/-Inf)
    if len(spec.features) > 0 and len(X) > 0:
        x_vals = X.to_numpy(dtype=float)
        if np.isinf(x_vals).any():
            raise DataContractViolationError(
                f"NUMERICAL INTEGRITY VIOLATION: Infinite values (Inf/-Inf) detected in predictor matrix X for '{model_id}'!"
            )
    if len(y) > 0:
        if not pd.api.types.is_numeric_dtype(y):
            raise DataContractViolationError(
                f"DTYPE VIOLATION: Non-numeric target vector detected for '{model_id}': {y.dtype}"
            )
        y_vals = y.to_numpy(dtype=float)
        if np.isinf(y_vals).any():
            raise DataContractViolationError(
                f"NUMERICAL INTEGRITY VIOLATION: Infinite values (Inf/-Inf) detected in target vector y for '{model_id}'!"
            )

    logger.debug(
        "Extracted matrix for %s: X=%s, y=%s (rows=%d, date_range=[%s, %s])",
        model_id,
        list(X.columns),
        y.name,
        len(y),
        str(filtered_dates.iloc[0].date()) if len(filtered_dates) > 0 else "None",
        str(filtered_dates.iloc[-1].date()) if len(filtered_dates) > 0 else "None",
    )

    return ModelDataMatrix(
        X=X,
        y=y,
        dates=filtered_dates,
        spec=spec,
        row_meta=row_meta,
    )


def extract_common_sample_matrices(
    df: pd.DataFrame,
    model_ids: tuple[str, ...] = ("M0a", "M0b", "M1", "M2", "M3"),
    *,
    enforce_stream_purity: bool = True,
) -> dict[str, ModelDataMatrix]:
    """Extract model matrices for multiple models aligned to their EXACT common valid dates.

    Guarantees that comparative econometric testing (Diebold-Mariano, Clark-West,
    and leaderboard generation) operates on the identical underlying sample without
    any temporal mismatch or loss differential length errors.

    Args:
        df (pd.DataFrame): Dataset containing features, targets, and 'market_date'.
        model_ids (tuple[str, ...], optional): Sequence of model IDs to extract and align.
            Defaults to ("M0a", "M0b", "M1", "M2", "M3").
        enforce_stream_purity (bool, optional): If True, strictly prevents mixing models from
            different research streams (e.g. Stream 1 Econometric 2008–2025 vs Stream 2 ML 2017–2025).
            This guards against inadvertent sample truncation that would destroy the statistical
            power of Stream 1 econometric Wald tests. Defaults to True.

    Returns:
        dict[str, ModelDataMatrix]: Dictionary mapping model_id to its aligned ModelDataMatrix,
            each guaranteed to have the exact same number of rows and matching dates.

    Raises:
        DataContractViolationError: If stream purity is violated (enforce_stream_purity=True),
            or if common valid sample is empty.
    """
    # Validate stream purity to guard against Stream Intersection Trap
    streams_found = {get_model_spec(mid).stream for mid in model_ids}
    if enforce_stream_purity and len(streams_found) > 1:
        raise DataContractViolationError(
            f"STREAM PURITY VIOLATION: Cannot extract common sample across mixed streams {sorted(streams_found)} "
            f"for requested models {list(model_ids)} (enforce_stream_purity=True). "
            f"Stream 1 (2008–2025, N=4,425) must NOT be truncated by Stream 2 (2017–2025) feature dependencies! "
            f"To evaluate models within a stream, request only models from that stream. "
            f"If intentionally benchmarking Stream 1 models on the Stream 2 test window, explicitly pass enforce_stream_purity=False."
        )

    if len(streams_found) > 1:
        logger.warning(
            "CROSS-STREAM BENCHMARK AUDIT: Common sample extracted across mixed streams %s with enforce_stream_purity=False. "
            "Observations are truncated to the common valid intersection. "
            "Ensure this truncation is intended exclusively for ML benchmarking comparison and NOT for full-sample RQ1 inference.",
            sorted(streams_found),
        )

    # Compute intersection of valid masks across all requested models
    combined_mask = pd.Series(True, index=df.index)
    for mid in model_ids:
        spec = get_model_spec(mid)
        if spec.target in df.columns:
            combined_mask = combined_mask & df[spec.target].notna()
        for f in spec.features:
            if f in df.columns:
                combined_mask = combined_mask & df[f].notna()

    common_count = int(combined_mask.sum())
    if common_count == 0:
        raise DataContractViolationError(
            f"Common valid sample across models {model_ids} has 0 observations! Check missing features."
        )

    logger.info(
        "Common sample alignment for %s: %d observations guaranteed across all %d models.",
        list(model_ids),
        common_count,
        len(model_ids),
    )

    matrices: dict[str, ModelDataMatrix] = {}
    for mid in model_ids:
        matrices[mid] = extract_model_matrix(df, mid, common_mask=combined_mask)

    return matrices


def diagnose_multicollinearity(
    X: pd.DataFrame,
    model_id: str = "Unknown",
) -> MulticollinearityReport:
    """Diagnose multicollinearity in the design predictor matrix X.

    Calculates:
    1. Variance Inflation Factor (VIF) for each predictor column via inverted correlation matrix
       (or auxiliary pseudo-inverse).
    2. Condition Number via singular value decomposition (SVD) on centered and standardized features.

    Evaluates standard econometric thresholds (Belsley et al., 1980; Wooldridge, 2015):
    - Condition Number >= 30.0 or any VIF >= 10.0: Severe multicollinearity.
    - Condition Number >= 15.0 or any VIF >= 5.0: Moderate multicollinearity.

    Args:
        X (pd.DataFrame): Design matrix of predictor features (without constant).
        model_id (str, optional): Model identifier for reporting. Defaults to "Unknown".

    Returns:
        MulticollinearityReport: Complete diagnostic metrics and automated threshold evaluation.
    """
    if X.shape[1] == 0:
        return MulticollinearityReport(
            model_id=model_id,
            num_features=0,
            condition_number=1.0,
            vif_scores={},
            max_vif_feature="",
            max_vif_value=1.0,
            has_severe_multicollinearity=False,
            warning_message=None,
        )

    if X.shape[1] == 1:
        col = str(X.columns[0])
        return MulticollinearityReport(
            model_id=model_id,
            num_features=1,
            condition_number=1.0,
            vif_scores={col: 1.0},
            max_vif_feature=col,
            max_vif_value=1.0,
            has_severe_multicollinearity=False,
            warning_message=None,
        )

    # Convert to clean numeric float matrix
    X_num = X.select_dtypes(include=[np.number]).copy()
    cols = list(X_num.columns)
    k = len(cols)

    # Check for zero-variance (constant) columns
    stds = X_num.std(ddof=1)
    zero_var_cols = stds[stds == 0].index.tolist()
    if zero_var_cols:
        return MulticollinearityReport(
            model_id=model_id,
            num_features=k,
            condition_number=float("inf"),
            vif_scores={c: float("inf") if c in zero_var_cols else 1.0 for c in cols},
            max_vif_feature=zero_var_cols[0],
            max_vif_value=float("inf"),
            has_severe_multicollinearity=True,
            warning_message=(
                f"PERFECT MULTICOLLINEARITY: Predictor columns {zero_var_cols} have zero variance (constant)!"
            ),
        )

    # Centered and scaled Z matrix for condition number
    Z = (X_num - X_num.mean()) / stds
    s = np.linalg.svd(Z.to_numpy(), compute_uv=False)
    if s[-1] > 1e-12:
        cond_num = float(s[0] / s[-1])
    else:
        cond_num = float("inf")

    # VIF calculation via correlation matrix inversion
    corr = X_num.corr().to_numpy()
    vif_dict: dict[str, float] = {}
    try:
        inv_corr = np.linalg.inv(corr)
        for i, c in enumerate(cols):
            vif_dict[c] = float(max(1.0, inv_corr[i, i]))
    except np.linalg.LinAlgError:
        logger.warning("Correlation matrix inversion failed for %s. Using pseudo-inverse.", model_id)
        inv_corr = np.linalg.pinv(corr)
        for i, c in enumerate(cols):
            vif_dict[c] = float(max(1.0, inv_corr[i, i]))

    # Find maximum VIF
    max_feature = max(vif_dict, key=vif_dict.get) if vif_dict else ""
    max_vif = float(vif_dict[max_feature]) if max_feature else 1.0

    # Evaluate thresholds
    is_severe = bool(cond_num >= 30.0 or max_vif >= 10.0)
    warning_msg: Optional[str] = None

    if is_severe:
        warning_msg = (
            f"HIGH MULTICOLLINEARITY WARNING for model '{model_id}': "
            f"Condition Number = {cond_num:.2f} (threshold >= 30.0) or "
            f"Max VIF = {max_vif:.2f} on '{max_feature}' (threshold >= 10.0). "
            "Estimator coefficients remain unbiased, but HAC standard errors and Wald tests "
            "may suffer from inflated variance and reduced statistical power."
        )
        logger.warning(warning_msg)
    elif cond_num >= 15.0 or max_vif >= 5.0:
        warning_msg = (
            f"MODERATE MULTICOLLINEARITY NOTICE for model '{model_id}': "
            f"Condition Number = {cond_num:.2f} (threshold >= 15.0) or "
            f"Max VIF = {max_vif:.2f} on '{max_feature}' (threshold >= 5.0)."
        )
        logger.info(warning_msg)

    return MulticollinearityReport(
        model_id=model_id,
        num_features=k,
        condition_number=cond_num,
        vif_scores=vif_dict,
        max_vif_feature=max_feature,
        max_vif_value=max_vif,
        has_severe_multicollinearity=is_severe,
        warning_message=warning_msg,
    )
