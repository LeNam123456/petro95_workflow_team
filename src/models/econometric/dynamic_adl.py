"""Linear Dynamic Regression (M2) and Asymmetric ADL (M3) for SPAFS V5.2.

Provides:
- M2: LinearDynamicModel (Symmetric dynamic OLS with Newey-West HAC standard errors).
- M3: AsymmetricAdlModel (RQ1 Core Econometric Model decomposing contemporaneous and lagged Brent shocks
  into positive and negative branches with Newey-West HAC covariance and formal Wald hypothesis tests).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS, RegressionResultsWrapper

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


def _compute_auto_hac_lags(n: int) -> int:
    """Compute Newey-West (1994) automatic bandwidth lag floor: floor(4 * (T / 100)^(2/9))."""
    return max(1, int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0))))


class LinearDynamicModel(BaseForecastingModel):
    """M2: Linear Dynamic Regression (Symmetric Benchmark).

    Features (K = 5 + 1 constant):
        1. const: Intercept α
        2. mg95_return_pct: r_{MG95, t}
        3. mg95_return_lag1: r_{MG95, t-1}
        4. brent_return_pct_aligned: r_{Brent, t}
        5. brent_return_lag1: r_{Brent, t-1}
        6. spread_mg95_brent_lag1: Lagged crack margin anchor (MG95 - Brent)_{t-1}

    Args:
        hac_lags (int | str, optional): Newey-West Bartlett kernel lags.
            Integer (e.g. 5) or 'auto' for floor(4 * (T/100)^(2/9)). Defaults to 5.
    """

    def __init__(self, hac_lags: int | str = 5) -> None:
        super().__init__(model_id="M2")
        self.hac_lags_setting = hac_lags
        self.hac_lags_used: int = 5
        self.results_: Optional[RegressionResultsWrapper] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> LinearDynamicModel:
        """Fit OLS with Newey-West HAC covariance."""
        X_val = self._validate_input_x(X)
        X_with_const = sm.add_constant(X_val, has_constant="add")

        n = len(y)
        if self.hac_lags_setting == "auto":
            self.hac_lags_used = _compute_auto_hac_lags(n)
        else:
            self.hac_lags_used = int(self.hac_lags_setting)

        # Fit OLS with Newey-West HAC covariance
        ols_model = OLS(y, X_with_const)
        self.results_ = ols_model.fit(cov_type="HAC", cov_kwds={"maxlags": self.hac_lags_used})
        self.is_fitted = True

        logger.debug(
            "Fitted M2 (N=%d, HAC lags=%d): R²=%.4f, Adj R²=%.4f",
            n,
            self.hac_lags_used,
            self.results_.rsquared,
            self.results_.rsquared_adj,
        )
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate point return forecasts r̂_{t+1}."""
        self._check_is_fitted()
        assert self.results_ is not None

        X_val = self._validate_input_x(X)
        X_with_const = sm.add_constant(X_val, has_constant="add")
        preds = self.results_.predict(X_with_const)
        return pd.Series(preds.values, index=X.index, name="pred_return_M2")

    def get_params_summary(self) -> dict[str, Any]:
        """Return parameters, HAC standard errors, and fit metrics."""
        self._check_is_fitted()
        assert self.results_ is not None

        params = self.results_.params.to_dict()
        bse = self.results_.bse.to_dict()
        tvalues = self.results_.tvalues.to_dict()
        pvalues = self.results_.pvalues.to_dict()

        coef_table = {}
        for k in params:
            coef_table[k] = {
                "estimate": float(params[k]),
                "std_err": float(bse.get(k, np.nan)),
                "t_stat": float(tvalues.get(k, np.nan)),
                "p_value": float(pvalues.get(k, np.nan)),
            }

        return {
            "model_id": self.model_id,
            "name": self.spec.name,
            "sample_size": int(self.results_.nobs),
            "hac_lags": self.hac_lags_used,
            "r_squared": float(self.results_.rsquared),
            "r_squared_adj": float(self.results_.rsquared_adj),
            "aic": float(self.results_.aic),
            "bic": float(self.results_.bic),
            "coefficients": coef_table,
            "cov_matrix": self.results_.cov_params().values.tolist(),
        }


class AsymmetricAdlModel(BaseForecastingModel):
    """M3: Asymmetric Autoregressive Distributed Lag (ADL) Model (RQ1 Core Model).

    Formulation:
        r_{MG95, t+1} = α + ϕ₁ r_{MG95, t} + ϕ₂ r_{MG95, t-1}
                        + (β₀⁺ r_{Brent, t}⁺ + β₀⁻ r_{Brent, t}⁻)
                        + (β₁⁺ r_{Brent, t-1}⁺ + β₁⁻ r_{Brent, t-1}⁻)
                        + λ Spread_{t-1} + ϵ_{t+1}

    Features (K = 7 + 1 constant = 8 parameters):
        1. const: Intercept α
        2. mg95_return_pct: r_{MG95, t}
        3. mg95_return_lag1: r_{MG95, t-1}
        4. brent_return_pos: r_{Brent, t}⁺ = max(r, 0)
        5. brent_return_neg: r_{Brent, t}⁻ = min(r, 0)
        6. brent_return_pos_lag1: r_{Brent, t-1}⁺
        7. brent_return_neg_lag1: r_{Brent, t-1}⁻
        8. spread_mg95_brent_lag1: Lagged crack margin anchor (MG95 - Brent)_{t-1}

    Args:
        hac_lags (int | str, optional): Newey-West Bartlett kernel lags. Defaults to 5.
    """

    def __init__(self, hac_lags: int | str = 5) -> None:
        super().__init__(model_id="M3")
        self.hac_lags_setting = hac_lags
        self.hac_lags_used: int = 5
        self.results_: Optional[RegressionResultsWrapper] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> AsymmetricAdlModel:
        """Fit M3 OLS with Newey-West HAC covariance."""
        X_val = self._validate_input_x(X)
        X_with_const = sm.add_constant(X_val, has_constant="add")

        n = len(y)
        if self.hac_lags_setting == "auto":
            self.hac_lags_used = _compute_auto_hac_lags(n)
        else:
            self.hac_lags_used = int(self.hac_lags_setting)

        ols_model = OLS(y, X_with_const)
        self.results_ = ols_model.fit(cov_type="HAC", cov_kwds={"maxlags": self.hac_lags_used})
        self.is_fitted = True

        logger.debug(
            "Fitted M3 (N=%d, HAC lags=%d): R²=%.4f, Adj R²=%.4f",
            n,
            self.hac_lags_used,
            self.results_.rsquared,
            self.results_.rsquared_adj,
        )
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate point return forecasts r̂_{t+1}."""
        self._check_is_fitted()
        assert self.results_ is not None

        X_val = self._validate_input_x(X)
        X_with_const = sm.add_constant(X_val, has_constant="add")
        preds = self.results_.predict(X_with_const)
        return pd.Series(preds.values, index=X.index, name="pred_return_M3")

    def test_contemporaneous_asymmetry(self) -> dict[str, Any]:
        """Execute Wald test for H0^(1): β₀⁺ = β₀⁻ (Instantaneous symmetry).

        Restriction: R₁ β = 0 where R₁ = [0, 0, 0, 1, -1, 0, 0, 0]
        """
        self._check_is_fitted()
        assert self.results_ is not None

        r_matrix = "brent_return_pos = brent_return_neg"
        wald = self.results_.wald_test(r_matrix, scalar=True)

        beta_pos = float(self.results_.params["brent_return_pos"])
        beta_neg = float(self.results_.params["brent_return_neg"])
        diff = beta_pos - beta_neg

        fvalue = float(wald.statistic)
        pvalue = float(wald.pvalue)

        return {
            "hypothesis": "H0^(1): beta_0+ = beta_0- (Contemporaneous symmetry)",
            "beta_pos_0": beta_pos,
            "beta_neg_0": beta_neg,
            "diff": diff,
            "wald_f_stat": fvalue,
            "wald_chi2_stat": fvalue * 1.0,
            "df": 1,
            "p_value": pvalue,
            "reject_h0_at_005": bool(pvalue < 0.05),
            "economic_interpretation": (
                "Reject H0: Wholesale gasoline prices adjust asymmetrically to crude shocks within 24h."
                if pvalue < 0.05
                else "Do not reject H0: Wholesale gasoline prices adjust symmetrically to crude shocks within 24h."
            ),
        }

    def test_cumulative_asymmetry(self) -> dict[str, Any]:
        """Execute Wald test for H0^(2): β₀⁺ + β₁⁺ = β₀⁻ + β₁⁻ (2-day cumulative symmetry).

        Restriction: (brent_return_pos + brent_return_pos_lag1) = (brent_return_neg + brent_return_neg_lag1)
        """
        self._check_is_fitted()
        assert self.results_ is not None

        r_matrix = "brent_return_pos + brent_return_pos_lag1 = brent_return_neg + brent_return_neg_lag1"
        wald = self.results_.wald_test(r_matrix, scalar=True)

        sum_pos = float(self.results_.params["brent_return_pos"] + self.results_.params["brent_return_pos_lag1"])
        sum_neg = float(self.results_.params["brent_return_neg"] + self.results_.params["brent_return_neg_lag1"])
        diff = sum_pos - sum_neg

        fvalue = float(wald.statistic)
        pvalue = float(wald.pvalue)

        return {
            "hypothesis": "H0^(2): sum(beta+) = sum(beta-) (Cumulative 2-day symmetry)",
            "sum_beta_pos": sum_pos,
            "sum_beta_neg": sum_neg,
            "diff": diff,
            "wald_f_stat": fvalue,
            "wald_chi2_stat": fvalue * 1.0,
            "df": 1,
            "p_value": pvalue,
            "reject_h0_at_005": bool(pvalue < 0.05),
            "economic_interpretation": (
                "Reject H0: Cumulative transmission of crude shocks is asymmetric across a 2-day window."
                if pvalue < 0.05
                else "Do not reject H0: Cumulative transmission of crude shocks is symmetric across a 2-day window."
            ),
        }

    def test_joint_nested_symmetry(self) -> dict[str, Any]:
        """Execute Joint Wald test for H0^(joint): β₀⁺ = β₀⁻ AND β₁⁺ = β₁⁻ (M3 collapses to M2).

        Degrees of freedom: df = 2.
        """
        self._check_is_fitted()
        assert self.results_ is not None

        r_matrix = "brent_return_pos = brent_return_neg, brent_return_pos_lag1 = brent_return_neg_lag1"
        wald = self.results_.wald_test(r_matrix)

        fvalue = float(wald.statistic)
        pvalue = float(wald.pvalue)

        return {
            "hypothesis": "H0^(joint): beta_0+ = beta_0- AND beta_1+ = beta_1- (M3 nests M2)",
            "wald_f_stat": fvalue,
            "wald_chi2_stat": fvalue * 2.0,
            "df": 2,
            "p_value": pvalue,
            "reject_h0_at_005": bool(pvalue < 0.05),
            "economic_interpretation": (
                "Reject H0: Joint asymmetric structure is statistically significant over symmetric benchmark M2."
                if pvalue < 0.05
                else "Do not reject H0: Linear dynamic model M2 is an adequate representation; asymmetry is not supported."
            ),
        }

    def get_params_summary(self) -> dict[str, Any]:
        """Return parameters, HAC standard errors, fit metrics, and all 3 Wald test results."""
        self._check_is_fitted()
        assert self.results_ is not None

        params = self.results_.params.to_dict()
        bse = self.results_.bse.to_dict()
        tvalues = self.results_.tvalues.to_dict()
        pvalues = self.results_.pvalues.to_dict()

        coef_table = {}
        for k in params:
            coef_table[k] = {
                "estimate": float(params[k]),
                "std_err": float(bse.get(k, np.nan)),
                "t_stat": float(tvalues.get(k, np.nan)),
                "p_value": float(pvalues.get(k, np.nan)),
            }

        return {
            "model_id": self.model_id,
            "name": self.spec.name,
            "sample_size": int(self.results_.nobs),
            "hac_lags": self.hac_lags_used,
            "r_squared": float(self.results_.rsquared),
            "r_squared_adj": float(self.results_.rsquared_adj),
            "aic": float(self.results_.aic),
            "bic": float(self.results_.bic),
            "coefficients": coef_table,
            "cov_matrix": self.results_.cov_params().values.tolist(),
            "wald_test_contemporaneous": self.test_contemporaneous_asymmetry(),
            "wald_test_cumulative": self.test_cumulative_asymmetry(),
            "wald_test_joint_nested": self.test_joint_nested_symmetry(),
        }


__all__ = ["LinearDynamicModel", "AsymmetricAdlModel"]
