"""Evaluation, metrics, and hypothesis testing suite for SPAFS V5.2.

Provides:
- Metrics: compute_regression_metrics, compute_directional_metrics
- Hypothesis: run_wald_test, WaldTestResult
- Pairwise: diebold_mariano_test, clark_west_test, PairwiseTestResult
"""

from .hypothesis import (
    WaldTestResult,
    build_dynamic_restriction_matrix,
    run_rq1_wald_tests,
    run_wald_test,
)
from .metrics import compute_directional_metrics, compute_regression_metrics
from .pairwise import PairwiseTestResult, clark_west_test, diebold_mariano_test

__all__ = [
    "compute_regression_metrics",
    "compute_directional_metrics",
    "WaldTestResult",
    "run_wald_test",
    "build_dynamic_restriction_matrix",
    "run_rq1_wald_tests",
    "PairwiseTestResult",
    "diebold_mariano_test",
    "clark_west_test",
]
