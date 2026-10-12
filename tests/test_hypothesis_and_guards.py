"""Unit tests for hypothesis testing and advanced defensive guards in SPAFS V5.2."""

import numpy as np
import pandas as pd
import pytest

from src.data_proccessing.exceptions import DataContractViolationError
from src.data_proccessing.model_schemas import (
    ComparisonSpec,
    PAIRWISE_COMPARISONS,
    extract_model_matrix,
    get_model_spec,
)
from src.models.evaluation.hypothesis import (
    build_dynamic_restriction_matrix,
    run_rq1_wald_tests,
)


def test_unique_dates_guard_triggers_on_duplicates():
    """Verify that extract_model_matrix raises DataContractViolationError if duplicate dates exist."""
    df_dup = pd.DataFrame({
        "market_date": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-02"]),
        "target_return_pct": [0.01, -0.02, 0.005],
        "mg95_return_pct": [0.005, -0.01, 0.002],
    })
    with pytest.raises(DataContractViolationError, match="Duplicate market dates"):
        extract_model_matrix(df_dup, "M1")


def test_non_numeric_dtype_guard():
    """Verify that non-numeric feature columns raise DataContractViolationError."""
    df_bad_type = pd.DataFrame({
        "market_date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        "target_return_pct": [0.01, -0.02, 0.005],
        "mg95_return_pct": ["string_val", "bad", "type"],
    })
    with pytest.raises(DataContractViolationError, match="DTYPE VIOLATION"):
        extract_model_matrix(df_bad_type, "M1")


def test_dynamic_wald_restriction_builder():
    """Verify that restriction matrix R is constructed dynamically from variable names."""
    param_names = [
        "const",
        "mg95_return_pct",
        "mg95_return_lag1",
        "brent_return_pos",
        "brent_return_neg",
        "brent_return_pos_lag1",
        "brent_return_neg_lag1",
        "spread_mg95_brent_lag1",
    ]
    restr = [
        ("brent_return_pos", "brent_return_neg"),
        ("brent_return_pos_lag1", "brent_return_neg_lag1"),
    ]
    R, q = build_dynamic_restriction_matrix(param_names, restr)

    assert R.shape == (2, 8)
    assert q.shape == (2,)
    # Check row 0: brent_return_pos (idx 3) = 1, brent_return_neg (idx 4) = -1
    assert R[0, 3] == 1.0
    assert R[0, 4] == -1.0
    assert R[0, 0] == 0.0
    # Check row 1: brent_return_pos_lag1 (idx 5) = 1, brent_return_neg_lag1 (idx 6) = -1
    assert R[1, 5] == 1.0
    assert R[1, 6] == -1.0


def test_dynamic_wald_missing_variable_raises():
    """Verify that attempting to test a non-existent parameter raises KeyError."""
    param_names = ["const", "mg95_return_pct"]
    restr = [("non_existent_var", "mg95_return_pct")]
    with pytest.raises(KeyError, match="not found in model parameters"):
        build_dynamic_restriction_matrix(param_names, restr)


def test_pairwise_comparisons_stream_alignment_spec():
    """Verify that all pairwise comparisons specify an eval_stream and flag cross-stream comparisons."""
    for comp in PAIRWISE_COMPARISONS:
        assert hasattr(comp, "eval_stream")
        assert comp.eval_stream in ("stream1", "stream2")
        cand_spec = get_model_spec(comp.candidate_id)
        bench_spec = get_model_spec(comp.benchmark_id)
        if cand_spec.stream != bench_spec.stream:
            assert comp.requires_cross_stream_alignment is True
