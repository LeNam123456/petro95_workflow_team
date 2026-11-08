"""Forecast evaluation for SPAFS V5.2: the single source of truth for OOS metrics and tests.

Interface (everything a caller needs to know):

    forecast_metrics(y, pred, *, benchmark=None)            -> dict
    dm_test(y, pred_candidate, pred_benchmark, *, loss, horizon, ...) -> TestResult
    dm_test_losses(loss_candidate, loss_benchmark, *, horizon, ...)   -> TestResult
    cw_test(y, pred_candidate, pred_benchmark, *, horizon, ...)       -> TestResult
    pt_test(y, pred)                                         -> TestResult

Conventions enforced here so callers cannot get them wrong:

1. Every function takes *predictions*, never errors.
2. Pairwise tests always orient the differential as candidate vs benchmark. A
   negative DM statistic and a positive CW statistic both mean "candidate is better".
   ``p_value_one_sided`` always tests H1: candidate better than benchmark.
3. The HAC bandwidth is derived from ``horizon`` (h - 1 autocovariances, the
   MA(h-1) structure of optimal h-step errors). Callers never pass lag counts.
   DM and CW share one long-run variance estimator (uniform weights, Bartlett
   fallback if non-positive). PT is only reported for horizon = 1.
4. Rows where any input is NaN are dropped jointly. If ``y`` and predictions are
   all ``pd.Series``, they are first aligned on their common index.
5. Direction is the sign of a return: up = (r > 0).

References:
    Diebold & Mariano (1995); Harvey, Leybourne & Newbold (1997);
    Clark & West (2007); Pesaran & Timmermann (1992); Campbell & Thompson (2008).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

import numpy as np
import pandas as pd
from scipy import stats

ArrayLike = "pd.Series | np.ndarray | list[float]"


@dataclass(frozen=True)
class TestResult:
    """Outcome of one statistical test."""

    test: str
    statistic: float
    p_value_one_sided: float
    p_value_two_sided: float
    sample_size: int
    candidate_id: str = ""
    benchmark_id: str = ""
    hac_lags: int = 0
    mean_differential: float = float("nan")
    details: dict[str, Any] = field(default_factory=dict)

    def reject_at(self, alpha: float = 0.05) -> bool:
        """One-sided rejection (candidate better / predictive ability) at level alpha."""
        return bool(np.isfinite(self.p_value_one_sided) and self.p_value_one_sided < alpha)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        details = out.pop("details")
        out.update(details)
        out["reject_h0_005"] = self.reject_at(0.05)
        return out


# --------------------------------------------------------------------------- #
# Internal helpers (internal seams, not part of the interface)
# --------------------------------------------------------------------------- #
def _align(*arrays) -> list[np.ndarray]:
    """Align Series on a common index (if all are Series), then drop joint NaNs."""
    if all(isinstance(a, pd.Series) for a in arrays):
        idx = arrays[0].index
        for a in arrays[1:]:
            idx = idx.intersection(a.index)
        arrays = tuple(a.loc[idx] for a in arrays)
    cols = [np.asarray(a, dtype=float) for a in arrays]
    n = {len(c) for c in cols}
    if len(n) != 1:
        raise ValueError(f"Inputs have different lengths {sorted(n)} and cannot be aligned.")
    mask = np.ones(len(cols[0]), dtype=bool)
    for c in cols:
        mask &= np.isfinite(c)
    return [c[mask] for c in cols]


def _autocov(d: np.ndarray, k: int) -> float:
    dm = d - d.mean()
    if k == 0:
        return float(np.dot(dm, dm) / len(d))
    return float(np.dot(dm[k:], dm[:-k]) / len(d))


def _long_run_variance(d: np.ndarray, lags: int, kernel: Literal["uniform", "bartlett"]) -> float:
    """Long-run variance of d (not divided by n)."""
    lrv = _autocov(d, 0)
    for k in range(1, lags + 1):
        w = 1.0 if kernel == "uniform" else 1.0 - k / (lags + 1.0)
        lrv += 2.0 * w * _autocov(d, k)
    return lrv


def _check_n(n: int, name: str, minimum: int = 10) -> None:
    if n < minimum:
        raise ValueError(f"Insufficient paired observations ({n} < {minimum}) for {name}.")


def _hac_lags(horizon: int) -> int:
    if horizon < 1:
        raise ValueError(f"horizon must be >= 1, got {horizon}")
    return horizon - 1


# --------------------------------------------------------------------------- #
# Public interface
# --------------------------------------------------------------------------- #
def dm_test(
    y,
    pred_candidate,
    pred_benchmark,
    *,
    loss: Literal["squared", "absolute"] = "squared",
    horizon: int = 1,
    candidate_id: str = "candidate",
    benchmark_id: str = "benchmark",
) -> TestResult:
    """Diebold-Mariano (1995) test with the HLN (1997) small-sample correction.

    d_t = L(y - pred_candidate) - L(y - pred_benchmark).
    Long-run variance uses h-1 autocovariances with uniform weights (as in DM 1995
    and R ``forecast::dm.test``); if that estimate is non-positive it falls back to
    Bartlett (Newey-West) weights. The HLN statistic is referred to t(n-1).

    Statistic < 0 means the candidate has lower loss.
    """
    yt, pc, pb = _align(y, pred_candidate, pred_benchmark)
    ec, eb = yt - pc, yt - pb
    if loss == "squared":
        lc, lb = ec**2, eb**2
    elif loss == "absolute":
        lc, lb = np.abs(ec), np.abs(eb)
    else:
        raise ValueError(f"Unknown loss '{loss}'")
    res = dm_test_losses(lc, lb, horizon=horizon, candidate_id=candidate_id, benchmark_id=benchmark_id)
    return TestResult(
        **{**res.__dict__, "test": f"Diebold-Mariano HLN ({loss} loss)", "details": {**res.details, "loss": loss}}
    )


def dm_test_losses(
    loss_candidate,
    loss_benchmark,
    *,
    horizon: int = 1,
    candidate_id: str = "candidate",
    benchmark_id: str = "benchmark",
) -> TestResult:
    """Diebold-Mariano HLN test on pre-computed per-period losses (any loss function).

    Same variance estimator and conventions as ``dm_test``: statistic < 0 means the
    candidate has lower average loss; ``p_value_one_sided`` tests that hypothesis.
    """
    lc, lb = _align(loss_candidate, loss_benchmark)
    n = len(lc)
    _check_n(n, "Diebold-Mariano")
    d = lc - lb
    lags = _hac_lags(horizon)

    kernel = "uniform"
    lrv = _long_run_variance(d, lags, "uniform")
    if lrv <= 0.0:
        kernel = "bartlett"
        lrv = _long_run_variance(d, lags, "bartlett")

    d_mean = float(d.mean())
    dm_raw = 0.0 if lrv <= 0.0 else d_mean / np.sqrt(lrv / n)
    h = horizon
    hln = float(np.sqrt((n + 1.0 - 2.0 * h + h * (h - 1.0) / n) / n))
    stat = float(dm_raw * hln)
    return TestResult(
        test="Diebold-Mariano HLN",
        statistic=stat,
        p_value_one_sided=float(stats.t.cdf(stat, df=n - 1)),
        p_value_two_sided=float(2.0 * stats.t.sf(abs(stat), df=n - 1)),
        sample_size=n,
        candidate_id=candidate_id,
        benchmark_id=benchmark_id,
        hac_lags=lags,
        mean_differential=d_mean,
        details={
            "horizon": horizon,
            "dm_stat_raw": float(dm_raw),
            "hln_factor": hln,
            "variance_kernel": kernel,
            "candidate_loss_mean": float(lc.mean()),
            "benchmark_loss_mean": float(lb.mean()),
        },
    )


def cw_test(
    y,
    pred_candidate,
    pred_benchmark,
    *,
    horizon: int = 1,
    candidate_id: str = "candidate",
    benchmark_id: str = "benchmark",
) -> TestResult:
    """Clark-West (2007) MSPE-adjusted test for nested models.

    The candidate is the *larger* (nesting) model, the benchmark the smaller one.
        f_t = e_bench^2 - [e_cand^2 - (pred_bench - pred_cand)^2]
    t-statistic of mean(f) with the same long-run variance as ``dm_test`` (h-1
    autocovariances, uniform weights, Bartlett fallback), referred to N(0,1). Statistic > 0 means the candidate adds predictive content.
    """
    yt, pc, pb = _align(y, pred_candidate, pred_benchmark)
    n = len(yt)
    _check_n(n, "Clark-West")
    ec, eb = yt - pc, yt - pb
    adj = (pb - pc) ** 2
    f = eb**2 - (ec**2 - adj)
    lags = _hac_lags(horizon)
    kernel = "uniform"
    lrv = _long_run_variance(f, lags, "uniform")
    if lrv <= 0.0:
        kernel = "bartlett"
        lrv = _long_run_variance(f, lags, "bartlett")
    f_mean = float(f.mean())
    stat = 0.0 if lrv <= 0.0 else float(f_mean / np.sqrt(lrv / n))
    return TestResult(
        test="Clark-West (2007)",
        statistic=stat,
        p_value_one_sided=float(stats.norm.sf(stat)),
        p_value_two_sided=float(2.0 * stats.norm.sf(abs(stat))),
        sample_size=n,
        candidate_id=candidate_id,
        benchmark_id=benchmark_id,
        hac_lags=lags,
        mean_differential=f_mean,
        details={
            "horizon": horizon,
            "mspe_candidate": float(np.mean(ec**2)),
            "mspe_benchmark": float(np.mean(eb**2)),
            "mspe_raw_difference": float(np.mean(eb**2) - np.mean(ec**2)),
            "cw_adjustment": float(adj.mean()),
            "variance_kernel": kernel,
        },
    )


def _pt_from_directions(actual_up: np.ndarray, pred_up: np.ndarray) -> tuple[float, float, float]:
    """Return (statistic, p_one_sided, p_star). NaN statistic if the test is undefined."""
    n = len(actual_up)
    p_hat = float(np.mean(actual_up == pred_up))
    py = float(np.mean(actual_up))
    px = float(np.mean(pred_up))
    p_star = py * px + (1.0 - py) * (1.0 - px)
    v_hat = p_star * (1.0 - p_star) / n
    v_star = (
        (2.0 * py - 1.0) ** 2 * px * (1.0 - px) / n
        + (2.0 * px - 1.0) ** 2 * py * (1.0 - py) / n
        + 4.0 * py * px * (1.0 - py) * (1.0 - px) / n**2
    )
    denom = v_hat - v_star
    # Undefined when either series is constant (e.g. M0a always predicts 0 => "down").
    if denom <= 1e-15 or px in (0.0, 1.0) or py in (0.0, 1.0):
        return float("nan"), float("nan"), p_star
    s = (p_hat - p_star) / np.sqrt(denom)
    return float(s), float(stats.norm.sf(s)), p_star


def pt_test(y, pred) -> TestResult:
    """Pesaran-Timmermann (1992) test of directional predictive ability.

    S = (P_hat - P*) / sqrt(V(P_hat) - V(P*)) ~ N(0,1); one-sided H1: S > 0.
    Returns NaN statistic/p-values when a series has no sign variation.
    """
    yt, yp = _align(y, pred)
    n = len(yt)
    _check_n(n, "Pesaran-Timmermann")
    s, p1, p_star = _pt_from_directions(yt > 0.0, yp > 0.0)
    return TestResult(
        test="Pesaran-Timmermann (1992)",
        statistic=s,
        p_value_one_sided=p1,
        p_value_two_sided=float(2.0 * stats.norm.sf(abs(s))) if np.isfinite(s) else float("nan"),
        sample_size=n,
        details={"p_star": p_star},
    )


def forecast_metrics(y, pred, *, benchmark=None, horizon: int = 1) -> dict[str, float]:
    """Point and directional accuracy of one forecast series.

    Returns n, rmse, mae, mse, r2_oos_pct, da_pct, mcc, pt_stat, pt_p_value.
    ``r2_oos_pct`` is the Campbell-Thompson OOS R^2 (in %) against ``benchmark``;
    when ``benchmark`` is None the zero forecast (M0a) is used.
    The PT test assumes serially independent outcomes, so for overlapping
    multi-step targets (horizon > 1) pt_stat / pt_p_value are NaN.
    """
    if benchmark is None:
        yt, yp = _align(y, pred)
        yb = np.zeros_like(yt)
    else:
        yt, yp, yb = _align(y, pred, benchmark)
    n = len(yt)
    if n == 0:
        raise ValueError("No valid observations to evaluate.")
    e = yt - yp
    mse = float(np.mean(e**2))
    mse_b = float(np.mean((yt - yb) ** 2))

    up_t, up_p = yt > 0.0, yp > 0.0
    tp = int(np.sum(up_t & up_p))
    tn = int(np.sum(~up_t & ~up_p))
    fp = int(np.sum(~up_t & up_p))
    fn = int(np.sum(up_t & ~up_p))
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = float((tp * tn - fp * fn) / denom) if denom > 0 else 0.0
    if n >= 10 and horizon == 1:
        pt_s, pt_p, _ = _pt_from_directions(up_t, up_p)
    else:
        pt_s, pt_p = float("nan"), float("nan")

    return {
        "n": n,
        "rmse": float(np.sqrt(mse)),
        "mae": float(np.mean(np.abs(e))),
        "mse": mse,
        "r2_oos_pct": float((1.0 - mse / mse_b) * 100.0) if mse_b > 0 else float("nan"),
        "da_pct": float(np.mean(up_t == up_p) * 100.0),
        "mcc": mcc,
        "pt_stat": pt_s,
        "pt_p_value": pt_p,
    }


__all__ = ["TestResult", "dm_test", "dm_test_losses", "cw_test", "pt_test", "forecast_metrics"]
