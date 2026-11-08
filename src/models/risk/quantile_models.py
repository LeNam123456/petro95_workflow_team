"""Quantile (interval / risk) forecasters Q0-Q4 for SPAFS V5.2 (research direction 4).

Interface (everything a caller needs):

    LEVELS                                   probability levels forecast by every model
    RISK_MODEL_IDS                           ("Q0", "Q1", "Q2", "Q3", "Q4")
    make_risk_model(model_id, horizon) ->    object with
        .fit(X, y)                  X: feature rows (must contain DAILY_RETURN_COL), y: r_{t,h}
        .predict_quantiles(X)       -> DataFrame, index = X.index, columns = LEVELS (sorted,
                                       non-crossing). X must be the rows that immediately
                                       follow the training rows (the walk-forward engine
                                       guarantees this); volatility state is rolled forward
                                       through them without mutating the frozen post-fit state.

Models
    Q0  Historical simulation: empirical quantiles of the training targets.
    Q1  EWMA (lambda = 0.94) volatility x filtered historical simulation (FHS).
    Q2  GARCH(1,1)-t volatility (aggregated to h steps) x FHS.
    Q3  Location-Scale hybrid quantile regression: GARCH(1,1)-t scale + asymmetric Brent / spread features.
    Q4  LightGBM quantile regression + adaptive split conformal calibration (CQR).

FHS: training targets are standardised by the model's own ex-ante h-step volatility,
z_t = y_t / sigma_{h,t}; forecast quantiles are sigma_{h,tau} * time-decayed empirical
quantiles of z. This absorbs fat tails, non-zero drift and the gap between sqrt(h)
scaling and the true h-step variance (daily MG95 returns are negatively autocorrelated).
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

LEVELS: tuple[float, ...] = (0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.975)
RISK_MODEL_IDS: tuple[str, ...] = ("Q0", "Q1", "Q2", "Q3", "Q4")
DAILY_RETURN_COL = "mg95_return_pct"
EWMA_LAMBDA = 0.94

# Features for the conditional quantile models (all known at the 08:30 SGT origin).
Q3_FEATURES = (
    "brent_return_pct_aligned",
    "mg95_return_pct",
    "spread_mg95_brent_lag1",
    "economic_shock_flag",
)
Q4_FEATURES = (
    "mg95_return_pct", "mg95_return_lag1", "mg95_return_lag2", "mg95_return_lag3",
    "brent_return_pct_aligned", "brent_return_lag1", "brent_return_lag2", "brent_return_lag3",
    "vol_mg95_30d", "economic_shock_flag",
    "spread_mg95_mg92", "spread_mg95_do005", "spread_mg95_brent", "spread_mg95_brent_lag1",
    "octane_spread_nonpositive_flag",
)


# --------------------------------------------------------------------------- #
# Internal building blocks
# --------------------------------------------------------------------------- #
def _sorted_frame(values: np.ndarray, index) -> pd.DataFrame:
    """Rearrange quantiles to be non-decreasing (Chernozhukov et al., 2010)."""
    return pd.DataFrame(np.sort(np.atleast_2d(values), axis=1), index=index, columns=list(LEVELS))


def _empirical_quantiles(z: np.ndarray, half_life: int | None = 756) -> np.ndarray:
    """Empirical quantiles of standardised residuals with optional exponential time decay.

    A 756-session (~3 trading years) half-life lets FHS adapt smoothly when the market
    transitions from crisis (2020/2022) to calm regimes (2023-2025) while retaining
    full historical tail memory.
    """
    z = z[np.isfinite(z)]
    if len(z) < 30:
        raise ValueError(f"Too few training observations ({len(z)}) for empirical quantiles.")
    if half_life is None or half_life <= 0:
        return np.quantile(z, LEVELS)
    n = len(z)
    decay = np.exp(-np.log(2.0) * np.arange(n - 1, -1, -1, dtype=float) / float(half_life))
    order = np.argsort(z)
    z_sorted = z[order]
    w_sorted = decay[order]
    cdf = (np.cumsum(w_sorted) - 0.5 * w_sorted) / np.sum(w_sorted)
    return np.interp(LEVELS, cdf, z_sorted)


class _EwmaVariance:
    """Causal RiskMetrics variance: s2_t = lam * s2_{t-1} + (1 - lam) * r_t^2 (forecast of r_{t+1}^2).

    ``fit`` runs the recursion over the training rows and freezes the end state;
    ``run`` always restarts from that frozen state and never mutates it, so repeated
    predictions over the rows that follow the training sample are idempotent.
    """

    def __init__(self, lam: float = EWMA_LAMBDA) -> None:
        self.lam = lam
        self.fit_state: float | None = None

    def _recurse(self, r: np.ndarray, s2: float) -> tuple[np.ndarray, float]:
        out = np.empty(len(r))
        for i, x in enumerate(r):
            s2 = self.lam * s2 + (1.0 - self.lam) * x * x
            out[i] = s2
        return out, s2

    def fit(self, r: np.ndarray) -> np.ndarray:
        out, self.fit_state = self._recurse(r, float(np.nanvar(r[: min(len(r), 63)])))
        return out

    def run(self, r: np.ndarray) -> np.ndarray:
        if self.fit_state is None:
            raise RuntimeError("EWMA variance used before fit.")
        return self._recurse(r, self.fit_state)[0]


def _fit_garch11_t_params(rr: np.ndarray) -> tuple[float, float, float, float, bool]:
    """Estimate GARCH(1,1)-t parameters (mu, omega, alpha, beta, converged).

    Uses ``arch`` if installed; falls back to self-contained Student-t GARCH(1,1) MLE
    via ``scipy.optimize.minimize`` so Q2 and Q3 work in any environment.
    """
    try:
        from arch import arch_model

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = arch_model(rr, mean="Constant", vol="GARCH", p=1, q=1, dist="t", rescale=False).fit(disp="off")
        p = res.params
        return (
            float(p["mu"]),
            float(p["omega"]),
            float(p["alpha[1]"]),
            float(p["beta[1]"]),
            bool(res.convergence_flag == 0),
        )
    except Exception:
        pass

    # Self-contained Student-t GARCH(1,1) MLE via L-BFGS-B
    mu0 = float(np.median(rr))
    eps = rr - mu0
    eps2 = eps * eps
    v0 = max(float(np.var(rr)), 1e-6)

    def neg_loglik(theta: np.ndarray) -> float:
        omega, alpha, beta, nu = theta
        if omega <= 1e-7 or alpha < 1e-4 or beta < 0.5 or alpha + beta >= 0.9995 or nu <= 2.1:
            return 1e12
        s2 = np.empty(len(eps2))
        cur = v0
        for i, e2 in enumerate(eps2):
            s2[i] = cur
            cur = omega + alpha * e2 + beta * cur
        # Student-t log-likelihood (standardised to variance s2)
        c = gammaln(0.5 * (nu + 1.0)) - gammaln(0.5 * nu) - 0.5 * np.log(np.pi * (nu - 2.0))
        ll = c - 0.5 * np.log(s2) - 0.5 * (nu + 1.0) * np.log(1.0 + eps2 / ((nu - 2.0) * s2))
        val = -float(np.sum(ll))
        return val if np.isfinite(val) else 1e12

    x0 = np.array([0.02 * v0, 0.08, 0.90, 6.0])
    bounds = [(1e-6, 0.5 * v0), (0.01, 0.35), (0.55, 0.985), (2.5, 30.0)]
    try:
        opt = minimize(neg_loglik, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 80})
        omega, alpha, beta, _ = opt.x
        if alpha + beta >= 0.9995:
            scale = 0.995 / (alpha + beta)
            alpha, beta = alpha * scale, beta * scale
        return mu0, float(omega), float(alpha), float(beta), bool(opt.success)
    except Exception:
        return 0.0, 0.01 * v0, 0.06, 0.93, False


class _ScaleFHS:
    """Shared engine for volatility-scaled models (Q0, Q1, Q2).

    Subclasses implement ``_fit_vol(r)`` (estimate parameters, run the recursion over
    the training rows and freeze its end state) returning the training h-step variances,
    and ``_hstep_var(r)``: h-step variance per row for rows that follow the training
    sample, always restarting from the frozen post-fit state (no mutation).
    """

    model_id = "?"
    fhs_half_life: int | None = 756

    def __init__(self, horizon: int) -> None:
        self.horizon = horizon
        self.z_quantiles_: np.ndarray | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "_ScaleFHS":
        r = X[DAILY_RETURN_COL].to_numpy(dtype=float)
        v = self._fit_vol(r)
        z = y.to_numpy(dtype=float) / np.sqrt(v)
        # The first rows of the variance recursion are a burn-in.
        self.z_quantiles_ = _empirical_quantiles(
            z[min(63, len(z) // 4):],
            half_life=self.fhs_half_life,
        )
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> pd.DataFrame:
        v = self._hstep_var(X[DAILY_RETURN_COL].to_numpy(dtype=float))
        return _sorted_frame(np.sqrt(v)[:, None] * self.z_quantiles_[None, :], X.index)

    def _fit_vol(self, r: np.ndarray) -> np.ndarray:  # pragma: no cover - overridden
        raise NotImplementedError

    def _hstep_var(self, r: np.ndarray) -> np.ndarray:  # pragma: no cover - overridden
        raise NotImplementedError


class HistoricalSimulation(_ScaleFHS):
    """Q0: unconditional empirical quantiles of the training targets (constant scale)."""

    model_id = "Q0"
    fhs_half_life = None  # Q0 is the static full-history benchmark

    def _fit_vol(self, r: np.ndarray) -> np.ndarray:
        return np.ones(len(r))

    def _hstep_var(self, r: np.ndarray) -> np.ndarray:
        return np.ones(len(r))


class EwmaFHS(_ScaleFHS):
    """Q1: EWMA daily variance, flat h-step aggregation h * s2_t, FHS calibration."""

    model_id = "Q1"

    def _fit_vol(self, r: np.ndarray) -> np.ndarray:
        self._ewma = _EwmaVariance()
        return self.horizon * self._ewma.fit(r)

    def _hstep_var(self, r: np.ndarray) -> np.ndarray:
        return self.horizon * self._ewma.run(r)


class GarchFHS(_ScaleFHS):
    """Q2: GARCH(1,1) with Student-t innovations, FHS calibration.

    sigma2_{t+1|t} = omega + alpha * eps_t^2 + beta * sigma2_{t|t-1},  eps_t = r_t - mu
    E[sigma2_{t+k|t}] = vbar + phi^(k-1) (sigma2_{t+1|t} - vbar),  phi = alpha + beta
    """

    model_id = "Q2"

    def _fit_vol(self, r: np.ndarray) -> np.ndarray:
        rr = r[np.isfinite(r)]
        self.mu, self.omega, self.alpha, self.beta, self.converged = _fit_garch11_t_params(rr)
        self.phi = min(self.alpha + self.beta, 0.9999)
        self.vbar = self.omega / (1.0 - self.phi) if self.omega > 0 else float(np.var(rr))
        v, self._state = self._recurse(r, float(np.var(rr)))  # start: sample variance
        return v

    def _recurse(self, r: np.ndarray, s2: float) -> tuple[np.ndarray, float]:
        k = np.arange(self.horizon)
        out = np.empty(len(r))
        for i, x in enumerate(r):
            eps = x - self.mu
            s2 = self.omega + self.alpha * eps * eps + self.beta * s2  # sigma2_{t+1|t}
            out[i] = np.sum(self.vbar + self.phi**k * (s2 - self.vbar))
        return np.maximum(out, 1e-8), s2

    def _hstep_var(self, r: np.ndarray) -> np.ndarray:
        return self._recurse(r, self._state)[0]


def _ewma_scale(r: np.ndarray, horizon: int, ewma: _EwmaVariance, fit: bool = False) -> np.ndarray:
    return np.sqrt(horizon * (ewma.fit(r) if fit else ewma.run(r)))


class LinearQuantileRegression:
    """Q3: Conditional Location-Scale Hybrid Quantile Regression.

    Combines GARCH(1,1)-t h-step conditional volatility scale ``s_garch_t`` with
    overnight Brent pass-through (signed return and magnitude), MG95 return, lagged
    refining spread, and shock flag. Using GARCH-t scale instead of flat EWMA prevents
    miss clustering during crisis regimes while retaining Brent's 25% sharpness gain.
    """

    model_id = "Q3"

    def __init__(self, horizon: int) -> None:
        self.horizon = horizon

    def _design(self, X: pd.DataFrame, s: np.ndarray) -> np.ndarray:
        b = X["brent_return_pct_aligned"].to_numpy(dtype=float)
        cols = [np.ones(len(X)), s, b, np.abs(b)] + [X[c].to_numpy(dtype=float) for c in Q3_FEATURES[1:]]
        return np.column_stack(cols)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LinearQuantileRegression":
        from statsmodels.regression.quantile_regression import QuantReg

        self._garch = GarchFHS(self.horizon)
        r = X[DAILY_RETURN_COL].to_numpy(dtype=float)
        s = np.sqrt(self._garch._fit_vol(r))
        D, yy = self._design(X, s), y.to_numpy(dtype=float)
        burn = min(63, len(yy) // 4)
        self.params_ = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for q in LEVELS:
                self.params_.append(QuantReg(yy[burn:], D[burn:]).fit(q=q, max_iter=5000).params)
        self.params_ = np.column_stack(self.params_)
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> pd.DataFrame:
        r = X[DAILY_RETURN_COL].to_numpy(dtype=float)
        s = np.sqrt(self._garch._hstep_var(r))
        return _sorted_frame(self._design(X, s) @ self.params_, X.index)


class ConformalLightGBMQuantiles:
    """Q4: LightGBM quantile regression + split conformalised quantile regression (CQR).

    The training window is split chronologically into a proper-training part and the
    last ``calib_frac`` for calibration, separated by a gap of ``horizon`` rows so no
    calibration label overlaps a training label. For each symmetric pair (a, 1-a) the
    interval is widened (or narrowed) by the conformal quantile of the CQR scores
    E = max(q_a - y, y - q_{1-a}), so coverage is valid on exchangeable data.
    """

    model_id = "Q4"
    params = dict(
        n_estimators=200, learning_rate=0.03, num_leaves=15, min_child_samples=50,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=42,
        verbose=-1, n_jobs=1,
    )

    def __init__(self, horizon: int, calib_frac: float = 0.2) -> None:
        self.horizon = horizon
        self.calib_frac = calib_frac

    def _features(self, X: pd.DataFrame, s: np.ndarray) -> np.ndarray:
        return np.column_stack([X[list(Q4_FEATURES)].to_numpy(dtype=float), s])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "ConformalLightGBMQuantiles":
        import lightgbm as lgb

        self._ewma = _EwmaVariance()
        s = _ewma_scale(X[DAILY_RETURN_COL].to_numpy(dtype=float), self.horizon, self._ewma, fit=True)
        F, yy = self._features(X, s), y.to_numpy(dtype=float)
        n = len(yy)
        n_cal = max(50, int(n * self.calib_frac))
        cal_start = n - n_cal
        train_end = cal_start - self.horizon  # purge between proper-train and calibration
        self.models_ = []
        for q in LEVELS:
            m = lgb.LGBMRegressor(objective="quantile", alpha=q, **self.params)
            m.fit(F[:train_end], yy[:train_end])
            self.models_.append(m)

        qc = np.sort(np.column_stack([m.predict(F[cal_start:]) for m in self.models_]), axis=1)
        yc = yy[cal_start:]
        self.adjust_ = np.zeros(len(LEVELS))
        k = len(LEVELS)
        for i in range(k // 2):  # pairs (i, k-1-i)
            lo, hi = qc[:, i], qc[:, k - 1 - i]
            scores = np.maximum(lo - yc, yc - hi)
            alpha = 1.0 - (LEVELS[k - 1 - i] - LEVELS[i])
            level = min(1.0, np.ceil((len(yc) + 1) * (1.0 - alpha)) / len(yc))
            self.adjust_[i] = np.quantile(scores, level, method="higher")  # order statistic
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> pd.DataFrame:
        s = _ewma_scale(X[DAILY_RETURN_COL].to_numpy(dtype=float), self.horizon, self._ewma)
        q = np.sort(np.column_stack([m.predict(self._features(X, s)) for m in self.models_]), axis=1)
        k = len(LEVELS)
        for i in range(k // 2):
            q[:, i] -= self.adjust_[i]
            q[:, k - 1 - i] += self.adjust_[i]
        return _sorted_frame(q, X.index)


_REGISTRY: dict[str, Any] = {
    "Q0": HistoricalSimulation,
    "Q1": EwmaFHS,
    "Q2": GarchFHS,
    "Q3": LinearQuantileRegression,
    "Q4": ConformalLightGBMQuantiles,
}

MODEL_DESCRIPTIONS = {
    "Q0": "Historical simulation (constant risk)",
    "Q1": "EWMA volatility + FHS",
    "Q2": "GARCH(1,1)-t + FHS",
    "Q3": "Location-Scale quantile regression (GARCH-t + Brent + spread)",
    "Q4": "LightGBM quantiles + conformal (CQR)",
}


def make_risk_model(model_id: str, horizon: int):
    """Return a fresh, unfitted quantile forecaster."""
    if model_id not in _REGISTRY:
        raise ValueError(f"Unknown risk model '{model_id}'. Expected one of {RISK_MODEL_IDS}.")
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    return _REGISTRY[model_id](horizon)


__all__ = ["LEVELS", "RISK_MODEL_IDS", "MODEL_DESCRIPTIONS", "DAILY_RETURN_COL", "make_risk_model"]
