"""Unit tests for SPAFS V5.2 Formal Model Schemas and Registry.

Verifies:
1. Zero target leakage via hard programmatic assert guards across all models.
2. Ingestion paradigm (input_mode) and supervised learning task (task) integrity.
3. Decoupling of M0b directional baseline from continuous regression baselines.
4. Symmetric lag decomposition of M3 for contemporaneous and cumulative Wald tests.
5. Extraction, unpacking, and DatetimeIndex monotonicity on real processed data.
6. Common sample alignment (N = 4,425) across all Stream 1 models.
7. Validation of Pairwise Comparison Registry (no cross-task comparisons).
8. Stream purity enforcement in extract_common_sample_matrices (guarding against Stream Intersection Trap).
9. Multicollinearity diagnostics: Condition Number and VIF computation on real design matrices.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_proccessing.exceptions import DataContractViolationError
from src.data_proccessing.model_schemas import (
    MODEL_REGISTRY,
    PAIRWISE_COMPARISONS,
    ComparisonSpec,
    ModelDataMatrix,
    ModelSpec,
    MulticollinearityReport,
    diagnose_multicollinearity,
    extract_common_sample_matrices,
    extract_model_matrix,
    get_model_spec,
    list_models,
)

STREAM1_PARQUET = Path("data/processed/stream1_econometric_2008_2025.parquet")


@pytest.fixture(scope="session")
def stream1_df():
    if not STREAM1_PARQUET.exists():
        pytest.skip("Stream 1 Parquet dataset not found on disk")
    return pd.read_parquet(STREAM1_PARQUET)


class TestModelSchemasSpecification:
    """Verifies declarative model specifications."""

    def test_all_models_registered(self):
        expected_ids = {"M0a", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"}
        assert set(MODEL_REGISTRY.keys()) == expected_ids
        assert len(list_models()) == 8

    def test_task_typing(self):
        for mid, spec in MODEL_REGISTRY.items():
            if mid == "M0b":
                assert spec.task == "classification"
                assert spec.target == "target_direction"
            else:
                assert spec.task == "regression"
                assert spec.target == "target_return_pct"

    def test_input_mode_typing(self):
        assert MODEL_REGISTRY["M0a"].input_mode == "null_baseline"
        assert MODEL_REGISTRY["M0b"].input_mode == "null_baseline"
        assert MODEL_REGISTRY["M1"].input_mode == "univariate_series"
        for mid in ("M2", "M3", "M4", "M5", "M6"):
            assert MODEL_REGISTRY[mid].input_mode == "feature_matrix"

    def test_m0b_decoupled_from_m0a(self):
        spec = get_model_spec("M0b")
        assert spec.benchmark_id is None, "M0b must not benchmark against regression model M0a!"
        assert "mcnemar" not in spec.statistical_tests, "Cross-task McNemar test is invalid!"
        assert "pesaran_timmermann" in spec.statistical_tests

    def test_m1_univariate_mle_spec(self):
        spec = get_model_spec("M1")
        assert spec.features == ("mg95_return_pct",)
        assert spec.input_mode == "univariate_series"
        assert spec.benchmark_id == "M0a"

    def test_m3_asymmetric_lag_features(self):
        spec = get_model_spec("M3")
        assert len(spec.features) == 7
        assert "brent_return_pos" in spec.features
        assert "brent_return_neg" in spec.features
        assert "brent_return_pos_lag1" in spec.features
        assert "brent_return_neg_lag1" in spec.features
        assert "spread_mg95_brent_lag1" in spec.features

    def test_zero_target_in_feature_whitelist(self):
        for mid, spec in MODEL_REGISTRY.items():
            assert "target_return_pct" not in spec.features, f"Target leaked into {mid} whitelist!"
            assert "target_direction" not in spec.features, f"Target direction leaked into {mid} whitelist!"


class TestPairwiseComparisonsRegistry:
    """Verifies that all pairwise comparisons are statistically valid."""

    def test_no_cross_task_comparisons(self):
        for comp in PAIRWISE_COMPARISONS:
            cand = get_model_spec(comp.candidate_id)
            bench = get_model_spec(comp.benchmark_id)
            assert cand.task == bench.task, (
                f"Invalid comparison: Candidate {cand.model_id} ({cand.task}) vs "
                f"Benchmark {bench.model_id} ({bench.task})!"
            )
            assert cand.target == bench.target, (
                f"Target mismatch: {cand.target} != {bench.target}!"
            )


class TestMatrixExtractionOnRealData:
    """Verifies extraction and matrix contracts on the real Stream 1 dataset."""

    def test_extract_m0a(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M0a")
        assert mat.num_features == 0
        assert mat.X.shape[1] == 0
        # 4,427 rows because the last row lacks target_return_pct (t+1 is unobserved)
        assert len(mat.y) == 4427
        assert "target_return_pct" not in mat.X.columns

    def test_extract_m0b(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M0b")
        assert mat.num_features == 1
        assert "mg95_return_pct" in mat.X.columns
        assert "target_direction" not in mat.X.columns
        assert mat.y.name == "target_direction"

    def test_extract_m1_univariate(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M1")
        assert mat.num_features == 1
        assert mat.X.columns.tolist() == ["mg95_return_pct"]
        assert "target_return_pct" not in mat.X.columns

    def test_extract_m3_adl(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M3")
        assert mat.num_features == 7
        assert "target_return_pct" not in mat.X.columns
        assert "target_direction" not in mat.X.columns
        assert len(mat.y) == 4425
        assert mat.X.index.is_monotonic_increasing

    def test_matrix_unpacking(self, stream1_df):
        X, y = extract_model_matrix(stream1_df, "M2")
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(y) == 4425

    def test_common_sample_alignment(self, stream1_df):
        matrices = extract_common_sample_matrices(stream1_df, ("M0a", "M1", "M2", "M3"))
        assert len(matrices) == 4
        # All models must have identical length of 4,425 and matching DatetimeIndex
        for mid, mat in matrices.items():
            assert mat.num_observations == 4425
            assert mat.dates.iloc[0] == matrices["M0a"].dates.iloc[0]
            assert mat.dates.iloc[-1] == matrices["M0a"].dates.iloc[-1]

    def test_row_meta_integrity(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M3")
        assert "market_date" in mat.row_meta.columns
        assert len(mat.row_meta) == len(mat.y)
        assert mat.row_meta.index.equals(mat.y.index)

    def test_stream_purity_enforcement(self, stream1_df):
        """Verifies that mixing streams raises DataContractViolationError by default."""
        with pytest.raises(DataContractViolationError, match="STREAM PURITY VIOLATION"):
            extract_common_sample_matrices(
                stream1_df,
                ("M3", "M4"),
                enforce_stream_purity=True,
            )

        # When enforce_stream_purity=False, extraction proceeds with audit warning
        matrices = extract_common_sample_matrices(
            stream1_df,
            ("M3", "M4"),
            enforce_stream_purity=False,
        )
        assert len(matrices) == 2
        assert matrices["M3"].num_observations == matrices["M4"].num_observations


class TestMulticollinearityDiagnostics:
    """Verifies multicollinearity diagnostics (VIF and Condition Number)."""

    def test_diagnose_empty_and_single_feature(self):
        rep0 = diagnose_multicollinearity(pd.DataFrame(), model_id="M0a")
        assert rep0.num_features == 0
        assert rep0.condition_number == 1.0
        assert not rep0.has_severe_multicollinearity

        df1 = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0]})
        rep1 = diagnose_multicollinearity(df1, model_id="M0b")
        assert rep1.num_features == 1
        assert rep1.vif_scores["feat1"] == 1.0
        assert not rep1.has_severe_multicollinearity

    def test_diagnose_m2_empirical_data(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M2")
        rep = diagnose_multicollinearity(mat.X, model_id="M2")
        assert isinstance(rep, MulticollinearityReport)
        assert rep.num_features == 5
        # Empirical condition number is well below 15.0
        assert rep.condition_number < 15.0
        # All VIFs are well below 5.0
        assert rep.max_vif_value < 5.0
        assert rep.vif_scores["spread_mg95_brent_lag1"] < 2.0
        assert not rep.has_severe_multicollinearity

    def test_diagnose_m3_empirical_data(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M3")
        rep = diagnose_multicollinearity(mat.X, model_id="M3")
        assert rep.num_features == 7
        # Empirical condition number ~2.37, far below danger threshold 30.0
        assert rep.condition_number < 15.0
        # All VIFs are well below danger threshold 10.0 (actual max < 2.0)
        assert rep.max_vif_value < 5.0
        assert rep.vif_scores["spread_mg95_brent_lag1"] < 2.0
        assert rep.vif_scores["brent_return_pos"] < 2.0
        assert rep.vif_scores["brent_return_neg"] < 2.0
        assert not rep.has_severe_multicollinearity

    def test_diagnose_perfect_collinearity_synthetic(self):
        # Create collinear matrix where x2 = 2 * x1
        x1 = np.linspace(1, 10, 50)
        x2 = 2.0 * x1
        x3 = np.random.default_rng(42).standard_normal(50)
        collinear_df = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
        rep = diagnose_multicollinearity(collinear_df, model_id="CollinearTest")
        assert rep.has_severe_multicollinearity
        assert rep.condition_number >= 30.0 or rep.max_vif_value >= 10.0
