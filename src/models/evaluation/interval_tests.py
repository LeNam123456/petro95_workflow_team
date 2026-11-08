"""Evaluation of quantile / interval / probability forecasts (SPAFS V5.2, direction 4).

Interface:

    evaluate_quantile_forecast(y, quantiles, *, horizon, p_up_reference=None,
                               history_width_80=None) -> dict
    compare_quantile_forecasts(y, q_candidate, q_benchmark, *, horizon, ...) -> TestResult
    prob_up_from_quantiles(quantiles) -> np.ndarray
    pinball_loss(y, quantiles) -> np.ndarray            (per-row mean over levels; NaN rows kept)
    kupiec_test(hits, alpha), christoffersen_test(hits), conditional_coverage_test(hits, alpha)
    build_unified_decision_card(quantiles_by_horizon, *, model_by_horizon=None,
                                point_forecast_h1=None,
                                history_width_80_by_horizon=None) -> pd.DataFrame
                                (raises ValueError if < 60 earlier widths to rank a regime)

``quantiles`` is a DataFrame whose columns are probability levels (floats), aligned with y.

Conventions:
* Intervals: 80% = [q0.10, q0.90], 95% = [q0.025, q0.975].
* Overlapping h-step targets: coverage, width and pinball use every origin; the
  Kupiec / Christoffersen / Conditional Coverage tests use the non-overlapping subsample
  (origins at positions 0, h, 2h, ... of the input, unaffected by dropped rows), because
  consecutive misses of overlapping targets are the same shock.
* Risk labels are based on the forecast 80% width ranked against *past* forecasts only
  (seeded expanding percentile or rolling 252-session window), so they are usable in real time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.models.evaluation.forecast_tests import TestResult, dm_test_losses

Z80 = float(stats.norm.ppf(0.9))
INTERVALS = {"80": (0.1, 0.9), "95": (0.025, 0.975)}


def _ordered(quantiles: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(levels ascending, quantile matrix with columns in that order)."""
    cols = sorted(quantiles.columns, key=float)
    return np.array([float(c) for c in cols]), quantiles[cols].to_numpy(dtype=float)


def _paired(y, quantiles: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    levels, q = _ordered(quantiles)
    yy = np.asarray(y, dtype=float)
    if len(yy) != len(q):
        raise ValueError("y and quantiles must have the same length.")
    return yy, q, levels


def _prep(y, quantiles: pd.DataFrame, horizon: int = 1) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Drop rows with a missing actual or quantile.

    Also returns a mask (over the kept rows) of the non-overlapping origins: original
    positions 0, h, 2h, ... so a dropped row never shifts the evaluation grid.
    """
    yy, q, levels = _paired(y, quantiles)
    ok = np.isfinite(yy) & np.isfinite(q).all(axis=1)
    on_grid = (np.arange(len(yy)) % horizon == 0)[ok]
    return yy[ok], q[ok], levels, on_grid


def pinball_loss(y, quantiles: pd.DataFrame) -> np.ndarray:
    """Per-row pinball (quantile) loss averaged over levels (≈ CRPS / 2).

    Row-aligned with the inputs: rows with a missing actual or quantile get NaN, so
    loss series of two models can be paired origin-by-origin before dropping gaps.
    """
    yy, q, levels = _paired(y, quantiles)
    u = yy[:, None] - q
    return np.mean(np.maximum(levels * u, (levels - 1.0) * u), axis=1)


def prob_up_from_quantiles(quantiles: pd.DataFrame) -> np.ndarray:
    """P(y > 0) by linear interpolation of the forecast CDF through the quantiles."""
    levels, q = _ordered(quantiles)
    lo_tail, hi_tail = levels[0] / 2.0, (1.0 + levels[-1]) / 2.0
    cdf0 = np.array([
        lo_tail if 0.0 < row[0] else hi_tail if 0.0 > row[-1]
        else float(np.interp(0.0, row, levels))
        for row in q
    ])
    return 1.0 - cdf0


def kupiec_test(hits: np.ndarray, alpha: float) -> tuple[float, float]:
    """Kupiec (1995) unconditional coverage LR test. hits = 1 if y fell outside the interval."""
    hits = np.asarray(hits, dtype=int)
    n, x = len(hits), int(hits.sum())
    if n == 0:
        return float("nan"), float("nan")
    pi = x / n

    def ll(p):
        p = min(max(p, 1e-12), 1 - 1e-12)
        return (n - x) * np.log(1 - p) + x * np.log(p)

    lr = -2.0 * (ll(alpha) - ll(pi))
    return float(lr), float(stats.chi2.sf(lr, 1))


def christoffersen_test(hits: np.ndarray) -> tuple[float, float]:
    """Christoffersen (1998) independence LR test (Markov first-order) of miss clustering."""
    h = np.asarray(hits, dtype=int)
    if len(h) < 3:
        return float("nan"), float("nan")
    a, b = h[:-1], h[1:]
    n00, n01 = int(np.sum((a == 0) & (b == 0))), int(np.sum((a == 0) & (b == 1)))
    n10, n11 = int(np.sum((a == 1) & (b == 0))), int(np.sum((a == 1) & (b == 1)))
    if n01 + n11 == 0 or n00 + n10 == 0:  # no misses or only misses: independence untestable
        return float("nan"), float("nan")

    def xlogy(x, p):
        return 0.0 if x == 0 else x * np.log(p)

    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / (n00 + n01 + n10 + n11)
    ll_ind = xlogy(n00, 1 - p01) + xlogy(n01, p01) + xlogy(n10, 1 - p11) + xlogy(n11, p11)
    ll_null = xlogy(n00 + n10, 1 - p) + xlogy(n01 + n11, p)
    lr = -2.0 * (ll_null - ll_ind)
    return float(lr), float(stats.chi2.sf(lr, 1))


def conditional_coverage_test(hits: np.ndarray, alpha: float) -> tuple[float, float]:
    """Christoffersen (1998) joint conditional coverage test: LR_cc = LR_uc + LR_ind ~ chi2(2)."""
    lr_uc, _ = kupiec_test(hits, alpha)
    lr_ind, _ = christoffersen_test(hits)
    if np.isnan(lr_uc) or np.isnan(lr_ind):
        return float("nan"), float("nan")
    lr_cc = float(lr_uc + lr_ind)
    return lr_cc, float(stats.chi2.sf(lr_cc, 2))


def _expanding_rank(
    x: np.ndarray,
    min_history: int = 60,
    history_seed: np.ndarray | None = None,
) -> np.ndarray:
    """Percentile of x_t among past observations (seeded with ``history_seed`` if provided)."""
    x = np.asarray(x, dtype=float)
    seed = np.asarray(history_seed, dtype=float) if history_seed is not None else np.empty(0)
    seed = seed[np.isfinite(seed)]
    full = np.concatenate([seed, x]) if len(seed) > 0 else x
    offset = len(seed)
    out = np.full(len(x), np.nan)
    for t in range(len(x)):
        idx = offset + t
        if idx >= min_history:
            out[t] = float(np.mean(full[:idx] < x[t]))
    return out


def _rolling_rank(
    x: np.ndarray,
    window: int = 252,
    min_history: int = 60,
    history_seed: np.ndarray | None = None,
) -> np.ndarray:
    """Percentile of x_t within the trailing ``window`` past observations."""
    x = np.asarray(x, dtype=float)
    seed = np.asarray(history_seed, dtype=float) if history_seed is not None else np.empty(0)
    seed = seed[np.isfinite(seed)]
    full = np.concatenate([seed, x]) if len(seed) > 0 else x
    offset = len(seed)
    out = np.full(len(x), np.nan)
    for t in range(len(x)):
        idx = offset + t
        if idx >= min_history:
            start = max(0, idx - window)
            out[t] = float(np.mean(full[start:idx] < x[t]))
    return out


def evaluate_quantile_forecast(
    y,
    quantiles: pd.DataFrame,
    *,
    horizon: int = 1,
    p_up_reference=None,
    history_width_80: np.ndarray | None = None,
) -> dict:
    """All direction-4 metrics for one model on one horizon.

    Returns coverage / width / Winkler score / Kupiec / Christoffersen / Conditional Coverage
    for the 80% and 95% intervals, mean pinball loss, QLIKE, Upside & Downside Tail VaR,
    probability-of-increase Brier score and log-loss (plus Brier skill vs ``p_up_reference``),
    Mincer-Zarnowitz R2, and risk-discrimination statistics (both expanding and rolling 252d).
    """
    yy, q, levels, on_grid = _prep(y, quantiles, horizon)
    n = len(yy)
    col = {float(lv): i for i, lv in enumerate(levels)}
    out: dict = {"n": n}

    for name, (lo_l, hi_l) in INTERVALS.items():
        lo, hi = q[:, col[lo_l]], q[:, col[hi_l]]
        alpha = 1.0 - (hi_l - lo_l)
        miss = (yy < lo) | (yy > hi)
        width = hi - lo
        winkler = width + (2.0 / alpha) * ((lo - yy) * (yy < lo) + (yy - hi) * (yy > hi))
        sub = miss[on_grid]
        out[f"coverage_{name}"] = float(1.0 - miss.mean())
        out[f"width_{name}"] = float(width.mean())
        out[f"winkler_{name}"] = float(winkler.mean())
        out[f"kupiec_p_{name}"] = kupiec_test(sub, alpha)[1]
        out[f"christoffersen_p_{name}"] = christoffersen_test(sub)[1]
        out[f"cc_p_{name}"] = conditional_coverage_test(sub, alpha)[1]
        out[f"n_independent_{name}"] = int(len(sub))

    out["pinball"] = float(pinball_loss(yy, pd.DataFrame(q, columns=levels)).mean())
    width80 = q[:, col[0.9]] - q[:, col[0.1]]
    sigma = np.maximum(width80 / (2.0 * Z80), 1e-6)
    centred = yy - q[:, col[0.5]]  # around the forecast median, so location shifts are not penalised here
    out["qlike"] = float(np.mean(np.log(sigma**2) + centred**2 / sigma**2))

    # Tail risk metrics (Upside risk for importers; Downside risk for inventory holders)
    if 0.95 in col and 0.975 in col:
        out["upside_var_95_mean"] = float(np.mean(q[:, col[0.95]]))
        out["upside_var_975_mean"] = float(np.mean(q[:, col[0.975]]))
    if 0.05 in col and 0.025 in col:
        out["downside_var_05_mean"] = float(np.mean(q[:, col[0.05]]))
        out["downside_var_025_mean"] = float(np.mean(q[:, col[0.025]]))

    # Direction as a probability
    p_up = np.clip(prob_up_from_quantiles(pd.DataFrame(q, columns=levels)), 1e-3, 1 - 1e-3)
    up = (yy > 0).astype(float)
    out["brier"] = float(np.mean((p_up - up) ** 2))
    out["log_loss"] = float(-np.mean(up * np.log(p_up) + (1 - up) * np.log(1 - p_up)))
    out["p_up_mean"] = float(p_up.mean())
    if p_up_reference is not None:
        ref = float(p_up_reference)
        brier_ref = float(np.mean((ref - up) ** 2))
        out["brier_skill_pct"] = float((1.0 - out["brier"] / brier_ref) * 100.0)

    # Risk discrimination: does a wider forecast precede bigger moves?
    absy = np.abs(yy)
    if np.std(width80) > 1e-12:
        sp = stats.spearmanr(width80, absy)
        out["spearman_width_absret"] = float(sp.statistic)
        out["spearman_p_width_absret"] = float(sp.pvalue)
        r_pearson = float(np.corrcoef(width80, absy)[0, 1])
        out["mz_r2"] = float(r_pearson * r_pearson)
    else:
        out["spearman_width_absret"] = float("nan")
        out["spearman_p_width_absret"] = float("nan")
        out["mz_r2"] = float("nan")

    rank = _expanding_rank(width80, history_seed=history_width_80)
    hi_mask, lo_mask = rank >= 0.75, rank <= 0.25
    if hi_mask.sum() >= 10 and lo_mask.sum() >= 10:
        sd_hi, sd_lo = float(np.std(yy[hi_mask])), float(np.std(yy[lo_mask]))
        out["realized_sd_high_risk"] = sd_hi
        out["realized_sd_low_risk"] = sd_lo
        out["risk_ratio_high_low"] = sd_hi / sd_lo
    else:
        out["realized_sd_high_risk"] = out["realized_sd_low_risk"] = out["risk_ratio_high_low"] = float("nan")

    rank_roll = _rolling_rank(width80, window=252, history_seed=history_width_80)
    hi_r, lo_r = rank_roll >= 0.75, rank_roll <= 0.25
    if hi_r.sum() >= 10 and lo_r.sum() >= 10:
        out["risk_ratio_rolling_252"] = float(np.std(yy[hi_r]) / max(np.std(yy[lo_r]), 1e-8))
    else:
        out["risk_ratio_rolling_252"] = float("nan")

    return out


def compare_quantile_forecasts(
    y, q_candidate: pd.DataFrame, q_benchmark: pd.DataFrame, *, horizon: int = 1,
    candidate_id: str = "candidate", benchmark_id: str = "benchmark",
) -> TestResult:
    """Diebold-Mariano (HLN, h-1 HAC lags) on per-row mean pinball loss.

    Statistic < 0 means the candidate's quantile forecasts are more accurate.
    """
    return dm_test_losses(
        pinball_loss(y, q_candidate), pinball_loss(y, q_benchmark), horizon=horizon,
        candidate_id=candidate_id, benchmark_id=benchmark_id,
    )


def build_unified_decision_card(
    quantiles_by_horizon: dict[str, pd.DataFrame],
    *,
    model_by_horizon: dict[str, str] | None = None,
    point_forecast_h1: float | None = None,
    history_width_80_by_horizon: dict[str, np.ndarray] | None = None,
) -> pd.DataFrame:
    """Build the operational Unified Multi-Horizon Decision Card at the latest forecast origin.

    Combines short-horizon point forecast (if provided) with 80%/95% intervals, median,
    probability of increase, Upside/Downside 95% Tail VaR, and Ex-Ante Risk Regime label
    across 1-day, 1-week, and 1-month horizons.

    The regime is the percentile of the latest 80% width among all *earlier* widths,
    seeded with ``history_width_80_by_horizon[h]`` (ex-ante widths forecast before the
    OOS window) so calm periods are judged against history, not against themselves.
    Raises ValueError if fewer than 60 earlier widths exist for a horizon.
    """
    seeds = history_width_80_by_horizon or {}
    default_models = {"daily": "Q3", "weekly": "Q3", "monthly": "Q2"}
    model_map = {**default_models, **(model_by_horizon or {})}
    rows = []
    for hname, df_q in quantiles_by_horizon.items():
        q_cols = [c for c in df_q.columns if c != "actual_return"]
        col_map = {float(str(c).lstrip("q")): c for c in q_cols}
        q_clean = df_q[q_cols].rename(columns={v: k for k, v in col_map.items()})
        w80 = (q_clean[0.9] - q_clean[0.1]).to_numpy(dtype=float)
        last_rank = float(_expanding_rank(w80, history_seed=seeds.get(hname))[-1])
        if not np.isfinite(last_rank):
            raise ValueError(
                f"Not enough width history to rank the '{hname}' risk regime; pass "
                "history_width_80_by_horizon with ex-ante widths from before the OOS window."
            )
        regime = "CAO (High)" if last_rank >= 0.75 else "THẤP (Low)" if last_rank <= 0.25 else "TRUNG BÌNH (Normal)"
        p_up = float(prob_up_from_quantiles(q_clean.iloc[[-1]])[0])
        last = q_clean.iloc[-1]
        rows.append({
            "horizon": hname,
            "origin_date": str(df_q.index[-1])[:10],
            "recommended_model": model_map.get(hname, "Q3"),
            "point_forecast_pct": round(float(point_forecast_h1), 3) if (hname == "daily" and point_forecast_h1 is not None) else round(float(last[0.5]), 3),
            "median_q50_pct": round(float(last[0.5]), 3),
            "interval_80_pct": f"[{last[0.1]:+.2f}%, {last[0.9]:+.2f}%]",
            "interval_95_pct": f"[{last[0.025]:+.2f}%, {last[0.975]:+.2f}%]",
            "prob_up_pct": round(p_up * 100.0, 1),
            "upside_tail_q95_pct": round(float(last[0.95]), 2),
            "downside_tail_q05_pct": round(float(last[0.05]), 2),
            "risk_regime_percentile": round(last_rank * 100.0, 1),
            "ex_ante_risk_regime": regime,
        })
    return pd.DataFrame(rows)


__all__ = [
    "INTERVALS",
    "evaluate_quantile_forecast",
    "compare_quantile_forecasts",
    "prob_up_from_quantiles",
    "pinball_loss",
    "kupiec_test",
    "christoffersen_test",
    "conditional_coverage_test",
    "build_unified_decision_card",
]
