"""Evaluation, metrics, and hypothesis testing suite for SPAFS V5.2.

- forecast_tests: forecast_metrics, dm_test, cw_test, pt_test (single source of truth)
- hypothesis: in-sample Wald tests for RQ1
"""

from .forecast_tests import TestResult, cw_test, dm_test, forecast_metrics, pt_test
from .hypothesis import (
    WaldTestResult,
    build_dynamic_restriction_matrix,
    run_rq1_wald_tests,
    run_wald_test,
)

__all__ = [
    "TestResult",
    "forecast_metrics",
    "dm_test",
    "cw_test",
    "pt_test",
    "WaldTestResult",
    "run_wald_test",
    "build_dynamic_restriction_matrix",
    "run_rq1_wald_tests",
]
