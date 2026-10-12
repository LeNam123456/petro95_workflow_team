"""ARMA(1, 1) Univariate Time Series Model for SPAFS V5.2.

Estimates univariate ARMA(1, 1) on endogenous Mogas 95 continuous returns via
Gaussian Maximum Likelihood Estimation (MLE) using Kalman Filter state-space recursions:
    r_{t+1} = c + ϕ₁ r_t + θ₁ ϵ_t + ϵ_{t+1},   ϵ_t ~ WN(0, σ²)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


class ArmaModel(BaseForecastingModel):
    """M1: ARMA(1, 1) Univariate Time-Series Model (statsmodels MLE).

    Args:
        order (tuple[int, int, int], optional): (p, d, q) order. Defaults to (1, 0, 1).
    """

    def __init__(self, order: tuple[int, int, int] = (1, 0, 1), trend: str = "c") -> None:
        super().__init__(model_id="M1")
        self.order = order
        self.trend = trend
        self.results_: Optional[ARIMAResults] = None
        self.train_endog_: Optional[pd.Series] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> ArmaModel:
        """Fit ARMA(1, 1) via Gaussian MLE.

        Args:
            X (pd.DataFrame): Input features containing 'mg95_return_pct'.
            y (pd.Series): Target series r_{t+1}.
        """
        X_val = self._validate_input_x(X)
        endog = X_val["mg95_return_pct"].copy()
        self.train_endog_ = endog

        # Fit Gaussian MLE with Kalman filter
        model = ARIMA(endog, order=self.order, trend=self.trend)
        self.results_ = model.fit()
        self.is_fitted = True
        logger.debug("Fitted ARMA%s: AIC=%.2f, BIC=%.2f", self.order, self.results_.aic, self.results_.bic)
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Generate forecasts from fitted ARMA model.

        If X dates overlap with training data, returns 1-step-ahead in-sample filtered predictions.
        If X represents new sequential observations, updates Kalman state and produces 1-step forecasts.
        """
        self._check_is_fitted()
        assert self.results_ is not None and self.train_endog_ is not None

        X_val = self._validate_input_x(X)
        endog_new = X_val["mg95_return_pct"]

        # If identical to training index, use 1-step in-sample predictions
        if endog_new.index.equals(self.train_endog_.index):
            preds = self.results_.predict(start=0, end=len(endog_new) - 1)
            pred_series = pd.Series(preds.values, index=endog_new.index, name="pred_return_M1")
            return pred_series

        # If out-of-sample or walk-forward step, apply state-space filter to new observations
        try:
            applied = self.results_.apply(endog_new)
            preds = applied.predict(start=0, end=len(endog_new) - 1)
            return pd.Series(preds.values, index=endog_new.index, name="pred_return_M1")
        except Exception:
            # Fallback 1-step static ARMA recursion
            c = float(self.results_.params.get("const", 0.0))
            phi = float(self.results_.params.get("ar.L1", 0.0))
            theta = float(self.results_.params.get("ma.L1", 0.0))
            last_val = float(endog_new.iloc[-1]) if len(endog_new) > 0 else 0.0
            forecast_val = c + phi * last_val
            return pd.Series(forecast_val, index=endog_new.index, name="pred_return_M1")

    def get_params_summary(self) -> dict[str, Any]:
        """Return estimated parameters, standard errors, and AIC/BIC."""
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
            "order": self.order,
            "sample_size": int(self.results_.nobs),
            "aic": float(self.results_.aic),
            "bic": float(self.results_.bic),
            "log_likelihood": float(self.results_.llf),
            "coefficients": coef_table,
        }


__all__ = ["ArmaModel"]
