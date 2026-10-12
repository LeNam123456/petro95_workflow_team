"""Hypothesis Testing Framework for Econometric Models in SPAFS V5.2.

Provides:
- run_wald_test: Computes general linear hypothesis Wald test statistic W ~ χ²(J) and F ~ F(J, N-K)
  under Newey-West HAC covariance matrix:
      H0: R β = q
- evaluate_rq1_hypotheses: Comprehensive evaluation suite for RQ1 pricing transmission asymmetry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from scipy import stats

logger = logging.getLogger("SPAFS_V5.2")


@dataclass(frozen=True)
class WaldTestResult:
    """Immutable result container for a linear restriction Wald hypothesis test."""

    hypothesis: str
    num_restrictions: int
    wald_chi2: float
    p_value_chi2: float
    wald_f: float
    p_value_f: float
    df_denom: Optional[int]
    reject_at_005: bool
    reject_at_001: bool


def run_wald_test(
    params: np.ndarray,
    cov_params: np.ndarray,
    R: np.ndarray,
    q: Optional[np.ndarray] = None,
    df_denom: Optional[int] = None,
    hypothesis_name: str = "Linear Restriction Test",
) -> WaldTestResult:
    """Execute general linear hypothesis Wald test R β = q using HAC covariance.

    Args:
        params: Estimated parameter vector (K,).
        cov_params: Estimated parameter covariance matrix (K, K) (e.g. Newey-West HAC).
        R: Restriction matrix (J, K).
        q: Restriction target vector (J,). Defaults to zeros.
        df_denom: Residual degrees of freedom N - K for F-distribution.
        hypothesis_name: Label for the hypothesis.

    Returns:
        WaldTestResult: Computed test statistics and p-values.
    """
    beta = np.asarray(params, dtype=float)
    V = np.asarray(cov_params, dtype=float)
    R_mat = np.atleast_2d(np.asarray(R, dtype=float))

    J, K = R_mat.shape
    if beta.shape[0] != K or V.shape != (K, K):
        raise ValueError(f"Dimension mismatch: beta({beta.shape}), V({V.shape}), R({R_mat.shape})")

    if q is None:
        q_vec = np.zeros(J)
    else:
        q_vec = np.asarray(q, dtype=float)

    # Restriction difference: r_diff = R β - q
    r_diff = R_mat @ beta - q_vec

    # Variance of restriction: V_r = R V R'
    V_r = R_mat @ V @ R_mat.T

    # Wald statistic: W = r_diff' (V_r)^(-1) r_diff
    try:
        inv_V_r = np.linalg.inv(V_r)
    except np.linalg.LinAlgError:
        inv_V_r = np.linalg.pinv(V_r)

    chi2_stat = float(r_diff.T @ inv_V_r @ r_diff)
    p_val_chi2 = float(1.0 - stats.chi2.cdf(chi2_stat, df=J))

    f_stat = float(chi2_stat / J)
    if df_denom is not None and df_denom > 0:
        p_val_f = float(1.0 - stats.f.cdf(f_stat, dfn=J, dfd=df_denom))
    else:
        p_val_f = p_val_chi2

    return WaldTestResult(
        hypothesis=hypothesis_name,
        num_restrictions=J,
        wald_chi2=chi2_stat,
        p_value_chi2=p_val_chi2,
        wald_f=f_stat,
        p_value_f=p_val_f,
        df_denom=df_denom,
        reject_at_005=bool(p_val_chi2 < 0.05),
        reject_at_001=bool(p_val_chi2 < 0.01),
    )


def build_dynamic_restriction_matrix(
    param_names: list[str],
    restrictions: list[tuple[str, str]],
) -> tuple[np.ndarray, np.ndarray]:
    """Construct dynamic linear restriction matrix R and target vector q for Wald test.

    Each restriction tuple (var_pos, var_neg) represents the null hypothesis:
        H0: beta_{var_pos} - beta_{var_neg} = 0

    Args:
        param_names: Ordered list of parameter names in the estimated model.
        restrictions: List of pairs (var1, var2) defining equality restrictions beta_{var1} = beta_{var2}.

    Returns:
        tuple[np.ndarray, np.ndarray]: (R, q) where R has shape (J, K) and q has shape (J,).

    Raises:
        KeyError: If any variable in restrictions is not found in param_names.
    """
    param_to_idx = {name: idx for idx, name in enumerate(param_names)}
    num_restr = len(restrictions)
    num_params = len(param_names)

    R = np.zeros((num_restr, num_params), dtype=float)
    q = np.zeros(num_restr, dtype=float)

    for i, (var1, var2) in enumerate(restrictions):
        if var1 not in param_to_idx:
            raise KeyError(f"Variable '{var1}' not found in model parameters: {param_names}")
        if var2 not in param_to_idx:
            raise KeyError(f"Variable '{var2}' not found in model parameters: {param_names}")

        R[i, param_to_idx[var1]] = 1.0
        R[i, param_to_idx[var2]] = -1.0

    return R, q


def run_rq1_wald_tests(m3_model: Any) -> dict[str, Any]:
    """Execute all three formal Wald hypothesis tests for Research Question 1 (RQ1).

    Tests:
    1. Contemporaneous symmetry: H0^(1): beta_0+ = beta_0-
    2. Cumulative 2-day symmetry: H0^(2): beta_0+ + beta_1+ = beta_0- + beta_1-
    3. Joint nested symmetry: H0^(joint): beta_0+ = beta_0- AND beta_1+ = beta_1- (M3 nests M2)

    Args:
        m3_model: Fitted AsymmetricAdlModel instance.

    Returns:
        dict[str, Any]: Dictionary containing test results for all three hypotheses.
    """
    if (
        hasattr(m3_model, "test_contemporaneous_asymmetry")
        and hasattr(m3_model, "test_cumulative_asymmetry")
        and hasattr(m3_model, "test_joint_nested_symmetry")
    ):
        return {
            "h0_contemporaneous": m3_model.test_contemporaneous_asymmetry(),
            "h0_cumulative": m3_model.test_cumulative_asymmetry(),
            "h0_joint_nested": m3_model.test_joint_nested_symmetry(),
        }
    raise AttributeError("m3_model must provide RQ1 Wald test methods.")


__all__ = [
    "WaldTestResult",
    "run_wald_test",
    "build_dynamic_restriction_matrix",
    "run_rq1_wald_tests",
]
