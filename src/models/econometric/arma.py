"""ARMA(1, 1) Univariate Time Series Model for SPAFS V5.2.

M1 forecasts r_{t+1} from the history of r_t only.

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

    def __init__(self, order: tuple[int, int, int] = (1, 0, 1), trend: str = "c", horizon: int = 1) -> None:
        super().__init__(model_id="M1")
        if horizon > 1 and (order[0] != 1 or order[1] != 0 or order[2] > 1):
            raise ValueError("Multi-step aggregation is implemented for ARMA(1, q<=1) only.")
        self.order = order
        self.trend = trend
        self.horizon = horizon
        self.results_: Optional[ARIMAResults] = None
        self.train_endog_: Optional[pd.Series] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> ArmaModel:
        """Fit ARMA(p, q) by Gaussian MLE on the observed return series r_t.

        Args:
            X (pd.DataFrame): Input features containing 'mg95_return_pct' (r_t, known at t).
            y (pd.Series): Target r_{t+1}; unused because r_{t+1} is r_t one row later.
        """
        X_val = self._validate_input_x(X)
        endog = X_val["mg95_return_pct"].copy()
        self.train_endog_ = endog
        # Positional index avoids date-frequency issues when appending new observations.
        model = ARIMA(endog.reset_index(drop=True), order=self.order, trend=self.trend)
        self.results_ = model.fit()
        self.is_fitted = True
        logger.debug("Fitted ARMA%s: AIC=%.2f, BIC=%.2f", self.order, self.results_.aic, self.results_.bic)
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Forecast r_{t+1} for every row t of X, i.e. E[r_{t+1} | r_s, s <= t].

        Contract: X is either the training rows themselves (in-sample one-step
        forecasts) or the rows that immediately follow the training sample, in order
        (as supplied by the walk-forward engine). The Kalman filter is updated with each
        new r_t (parameters fixed) before forecasting the next return.
        """
        self._check_is_fitted()
        assert self.results_ is not None and self.train_endog_ is not None

        endog_new = self._validate_input_x(X)["mg95_return_pct"]
        n_train = len(self.train_endog_)

        if endog_new.index.equals(self.train_endog_.index):
            # Prediction at position t+1 conditions on r_0..r_t; position n_train is the
            # first true out-of-sample forecast.
            preds = self.results_.predict(start=1, end=n_train)
        else:
            if len(self.train_endog_) and endog_new.index[0] <= self.train_endog_.index[-1]:
                raise ValueError("ArmaModel.predict expects rows that follow the training sample.")
            m = len(endog_new)
            updated = self.results_.append(endog_new.to_numpy(dtype=float))
            preds = updated.predict(start=n_train + 1, end=n_train + m)
        one_step = np.asarray(preds, dtype=float)
        if self.horizon > 1:
            # r_hat_{t,h} = sum_{j=1..h} E[r_{t+j} | F_t]. For ARMA(1, q<=1) around mean mu:
            # E[r_{t+j}|F_t] - mu = phi^(j-1) * (E[r_{t+1}|F_t] - mu).
            mu = float(self.results_.params.get("const", 0.0))
            phi = float(self.results_.params.get("ar.L1", 0.0))
            h = self.horizon
            geom = float(h) if abs(1.0 - phi) < 1e-12 else (1.0 - phi**h) / (1.0 - phi)
            one_step = h * mu + (one_step - mu) * geom
        return pd.Series(one_step, index=endog_new.index, name="pred_return_M1")

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
            "horizon": self.horizon,
            "sample_size": int(self.results_.nobs),
            "aic": float(self.results_.aic),
            "bic": float(self.results_.bic),
            "log_likelihood": float(self.results_.llf),
            "coefficients": coef_table,
        }


__all__ = ["ArmaModel"]
