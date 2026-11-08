"""Tests for direction 4: interval metrics, quantile walk-forward and risk models Q0-Q4."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.models.evaluation.interval_tests import (
    build_unified_decision_card,
    christoffersen_test,
    compare_quantile_forecasts,
    conditional_coverage_test,
    evaluate_quantile_forecast,
    kupiec_test,
    pinball_loss,
    prob_up_from_quantiles,
)
from src.models.risk import LEVELS, RISK_MODEL_IDS, make_risk_model
from src.models.validation.walk_forward import run_walk_forward_quantiles


def _normal_quantiles(mu: np.ndarray, sd: np.ndarray) -> pd.DataFrame:
    z = stats.norm.ppf(LEVELS)
    return pd.DataFrame(mu[:, None] + sd[:, None] * z[None, :], columns=list(LEVELS))


def _garch_sample(n=2600, seed=11):
    """Daily GARCH(1,1)-t returns + all feature columns the risk models read."""
    rng = np.random.default_rng(seed)
    omega, alpha, beta = 0.05, 0.08, 0.9
    r = np.zeros(n)
    s2 = omega / (1 - alpha - beta)
    for t in range(n):
        e = rng.standard_t(6) / np.sqrt(6 / 4)
        r[t] = np.sqrt(s2) * e
        s2 = omega + alpha * r[t] ** 2 + beta * s2
    idx = pd.date_range("2010-01-01", periods=n, freq="B")
    X = pd.DataFrame(0.0, index=idx, columns=[
        "mg95_return_pct", "mg95_return_lag1", "mg95_return_lag2", "mg95_return_lag3",
        "brent_return_pct_aligned", "brent_return_lag1", "brent_return_lag2", "brent_return_lag3",
        "vol_mg95_30d", "economic_shock_flag", "spread_mg95_mg92", "spread_mg95_do005",
        "spread_mg95_brent", "spread_mg95_brent_lag1", "octane_spread_nonpositive_flag",
    ])
    X["mg95_return_pct"] = r
    X["brent_return_pct_aligned"] = rng.standard_normal(n)
    return X, r


def _h_target(r: np.ndarray, h: int, index) -> pd.Series:
    y = pd.Series(r, index=index).shift(-1).rolling(h).sum().shift(-(h - 1))
    return y


# --------------------------------------------------------------------------- metrics
def test_pinball_matches_definition():
    y = np.array([1.0, -2.0])
    q = pd.DataFrame([[0.0, 0.5], [0.0, 0.5]], columns=[0.1, 0.9])
    # row1: u=1 -> 0.1*1, u=0.5 -> 0.9*0.5 ; row2: u=-2 -> 0.9*2, u=-2.5 -> 0.1*2.5
    expected = np.array([(0.1 + 0.45) / 2, (1.8 + 0.25) / 2])
    assert pinball_loss(y, q) == pytest.approx(expected)


def test_kupiec_closed_form():
    hits = np.r_[np.ones(30), np.zeros(170)]
    n, x, a = 200, 30, 0.2
    ll0 = (n - x) * np.log(1 - a) + x * np.log(a)
    ll1 = (n - x) * np.log(1 - x / n) + x * np.log(x / n)
    lr, p = kupiec_test(hits, a)
    assert lr == pytest.approx(-2 * (ll0 - ll1))
    assert p == pytest.approx(stats.chi2.sf(lr, 1))


def test_christoffersen_detects_clustering():
    rng = np.random.default_rng(0)
    iid = (rng.random(2000) < 0.2).astype(int)
    clustered = np.repeat((rng.random(200) < 0.2).astype(int), 10)
    assert christoffersen_test(iid)[1] > 0.01
    assert christoffersen_test(clustered)[1] < 1e-6


def test_prob_up_from_symmetric_quantiles_is_half():
    q = _normal_quantiles(np.zeros(3), np.ones(3))
    assert prob_up_from_quantiles(q) == pytest.approx(0.5, abs=1e-9)
    q2 = _normal_quantiles(np.full(1, 10.0), np.ones(1))
    assert prob_up_from_quantiles(q2)[0] > 0.98


def test_evaluate_correct_model_is_calibrated_and_discriminates_risk():
    rng = np.random.default_rng(1)
    sd = np.exp(rng.normal(0, 0.5, 4000))
    y = sd * rng.standard_normal(4000)
    res = evaluate_quantile_forecast(y, _normal_quantiles(np.zeros(4000), sd), horizon=1, p_up_reference=0.5)
    assert res["coverage_80"] == pytest.approx(0.8, abs=0.02)
    assert res["coverage_95"] == pytest.approx(0.95, abs=0.01)
    assert res["kupiec_p_80"] > 0.01
    assert res["risk_ratio_high_low"] > 2.0
    wrong = evaluate_quantile_forecast(y, _normal_quantiles(np.zeros(4000), np.full(4000, sd.mean())), horizon=1)
    assert res["pinball"] < wrong["pinball"]
    assert np.isnan(wrong["spearman_width_absret"])  # constant width carries no risk signal


def test_compare_prefers_true_model():
    rng = np.random.default_rng(2)
    sd = np.exp(rng.normal(0, 0.6, 3000))
    y = sd * rng.standard_normal(3000)
    good = _normal_quantiles(np.zeros(3000), sd)
    bad = _normal_quantiles(np.zeros(3000), np.full(3000, sd.mean()))
    t = compare_quantile_forecasts(y, good, bad, horizon=1)
    assert t.statistic < 0 and t.reject_at(0.05)


# --------------------------------------------------------------------------- walk-forward
class _SpyQ:
    log: list = []

    def fit(self, X, y):
        self.last = len(X) - 1
        return self

    def predict_quantiles(self, X):
        _SpyQ.log.append((self.last, X.index[0], X.index[-1]))
        return pd.DataFrame(0.0, index=X.index, columns=list(LEVELS))


@pytest.mark.parametrize("h,emb", [(1, 0), (5, 2), (21, 5)])
def test_quantile_walk_forward_purges(h, emb):
    X = pd.DataFrame({"a": np.zeros(300)})
    y = pd.Series(np.zeros(300))
    _SpyQ.log = []
    out = run_walk_forward_quantiles(lambda: _SpyQ(), X, y, initial_train_size=200,
                                     refit_every=20, horizon=h, embargo=emb)
    assert list(out.columns) == ["actual_return", *LEVELS] and len(out) == 100
    for tau, (train_end, first, last) in zip(range(200, 300), _SpyQ.log):
        assert train_end + h + emb <= tau and first == train_end + 1 and last == tau


# --------------------------------------------------------------------------- models
def test_unknown_model_rejected():
    with pytest.raises(ValueError):
        make_risk_model("Q9", 1)


@pytest.mark.parametrize("mid", RISK_MODEL_IDS)
@pytest.mark.parametrize("h", [1, 5])
def test_models_produce_sorted_quantiles_with_reasonable_coverage(mid, h):
    X, r = _garch_sample()
    y = _h_target(r, h, X.index)
    keep = y.notna()
    X, y = X[keep], y[keep]
    out = run_walk_forward_quantiles(lambda: make_risk_model(mid, h), X, y,
                                     initial_train_size=1600, refit_every=100, horizon=h)
    q = out[list(LEVELS)].to_numpy()
    assert np.all(np.diff(q, axis=1) >= -1e-12)
    res = evaluate_quantile_forecast(out["actual_return"], out[list(LEVELS)], horizon=h)
    assert 0.7 <= res["coverage_80"] <= 0.9


def test_volatility_models_beat_constant_risk_on_garch_data():
    X, r = _garch_sample(seed=5)
    y = _h_target(r, 1, X.index).dropna()
    X = X.loc[y.index]
    res = {}
    for mid in ("Q0", "Q1", "Q2"):
        out = run_walk_forward_quantiles(lambda m=mid: make_risk_model(m, 1), X, y,
                                         initial_train_size=1600, refit_every=50)
        res[mid] = evaluate_quantile_forecast(out["actual_return"], out[list(LEVELS)], horizon=1)
    assert res["Q2"]["pinball"] < res["Q0"]["pinball"]
    assert res["Q1"]["pinball"] < res["Q0"]["pinball"]
    assert res["Q2"]["risk_ratio_high_low"] > 1.5


def test_garch_h_step_variance_aggregation():
    X, r = _garch_sample(n=1500)
    m = make_risk_model("Q2", 5).fit(X.iloc[:1000], pd.Series(np.zeros(1000), index=X.index[:1000]))
    s2 = m._state
    x = X["mg95_return_pct"].iloc[1000]
    s2_next = m.omega + m.alpha * (x - m.mu) ** 2 + m.beta * s2
    expected = sum(m.vbar + (m.alpha + m.beta) ** k * (s2_next - m.vbar) for k in range(5))
    assert m._hstep_var(np.array([x]))[0] == pytest.approx(expected)


@pytest.mark.parametrize("mid", RISK_MODEL_IDS)
def test_predict_is_idempotent_between_refits(mid):
    """Regression: repeated predictions over rows after the training window must not
    re-run the volatility recursion on top of the previous call's state."""
    import copy

    X, r = _garch_sample(n=1300)
    y = _h_target(r, 1, X.index).dropna()
    X = X.loc[y.index]
    m = make_risk_model(mid, 1).fit(X.iloc[:1200], y.iloc[:1200])
    fresh = copy.deepcopy(m)
    for k in range(1, 20):  # what the walk-forward engine does between two refits
        m.predict_quantiles(X.iloc[1200 : 1200 + k])
    a = m.predict_quantiles(X.iloc[1200:1220]).iloc[-1]
    b = fresh.predict_quantiles(X.iloc[1200:1220]).iloc[-1]
    assert np.allclose(a.to_numpy(), b.to_numpy())


def test_conditional_coverage_and_seeded_risk_ranking():
    rng = np.random.default_rng(7)
    hits_good = (rng.random(500) < 0.2).astype(int)
    lr_uc, _ = kupiec_test(hits_good, 0.2)
    lr_ind, _ = christoffersen_test(hits_good)
    lr_cc, p_cc = conditional_coverage_test(hits_good, 0.2)
    assert lr_cc == pytest.approx(lr_uc + lr_ind)
    assert p_cc > 0.05

    sd = np.exp(rng.normal(0, 0.4, 300))
    y = sd * rng.standard_normal(300)
    q = _normal_quantiles(np.zeros(300), sd)
    seed_widths = np.exp(rng.normal(0, 0.4, 200)) * 2.56
    res = evaluate_quantile_forecast(y, q, horizon=1, history_width_80=seed_widths)
    assert "cc_p_80" in res and "upside_var_95_mean" in res and "downside_var_05_mean" in res
    assert res["risk_ratio_high_low"] > 1.3
    assert res["mz_r2"] > 0.02


def test_build_unified_decision_card():
    idx = pd.date_range("2025-01-01", periods=100, freq="B")
    q_df = _normal_quantiles(np.zeros(100), np.linspace(1.0, 3.0, 100))
    q_df.index = idx
    q_df["actual_return"] = 0.0
    card = build_unified_decision_card(
        {"daily": q_df, "weekly": q_df, "monthly": q_df},
        point_forecast_h1=0.45,
    )
    assert list(card["horizon"]) == ["daily", "weekly", "monthly"]
    assert card.loc[0, "point_forecast_pct"] == pytest.approx(0.45)
    assert card.loc[0, "ex_ante_risk_regime"] == "CAO (High)"



# --------------------------------------------------------------------------- missing rows, regime seeding, Q0 benchmark, arch-free GARCH
def test_compare_drops_missing_rows_jointly_not_per_forecast():
    """A NaN in one model's row must remove that row from BOTH loss series, so the
    DM test compares the two models on identical origins (not shifted rows)."""
    rng = np.random.default_rng(3)
    sd = np.exp(rng.normal(0, 0.6, 400))
    y = sd * rng.standard_normal(400)
    good = _normal_quantiles(np.zeros(400), sd)
    bad = _normal_quantiles(np.zeros(400), np.full(400, sd.mean()))
    good_gappy = good.copy()
    good_gappy.iloc[10] = np.nan
    bad_gappy = bad.copy()
    bad_gappy.iloc[200] = np.nan
    keep = np.ones(400, dtype=bool)
    keep[[10, 200]] = False
    expected = compare_quantile_forecasts(y[keep], good[keep].reset_index(drop=True),
                                          bad[keep].reset_index(drop=True), horizon=1)
    got = compare_quantile_forecasts(y, good_gappy, bad_gappy, horizon=1)
    assert got.sample_size == 398
    assert got.statistic == pytest.approx(expected.statistic)


def test_non_overlapping_subsample_keeps_original_origin_grid_when_rows_are_missing():
    """Coverage tests use every h-th ORIGIN; a missing row must not shift that grid."""
    h, n = 5, 500
    q = _normal_quantiles(np.zeros(n), np.ones(n))  # 80% interval ~ [-1.28, 1.28]
    y = np.zeros(n)
    y[1::h] = 5.0          # misses only on origins that are NOT on the 0, h, 2h, ... grid
    y[0] = np.nan          # first origin unrealised
    res = evaluate_quantile_forecast(y, q, horizon=h)
    assert res["n_independent_80"] == 99       # origins 5, 10, ..., 495
    assert res["kupiec_p_80"] == pytest.approx(kupiec_test(np.zeros(99), 0.2)[1])


def _calm_quantiles(n=20):
    q = _normal_quantiles(np.zeros(n), np.full(n, 0.5))
    q.index = pd.date_range("2024-01-01", periods=n, freq="B")
    return q


def test_decision_card_ranks_calm_origin_against_seeded_crisis_history():
    """Problem 4 of the spec: a calm regime must be ranked against historical widths,
    not against itself, and be labelled from the very first OOS origin."""
    crisis_widths = 2 * stats.norm.ppf(0.9) * np.linspace(1.0, 3.0, 300)
    card = build_unified_decision_card(
        {"daily": _calm_quantiles()},
        history_width_80_by_horizon={"daily": crisis_widths},
    )
    assert card.loc[0, "ex_ante_risk_regime"] == "THẤP (Low)"
    assert card.loc[0, "risk_regime_percentile"] == pytest.approx(0.0)


def test_decision_card_refuses_to_guess_a_regime_without_enough_history():
    with pytest.raises(ValueError, match="history"):
        build_unified_decision_card({"daily": _calm_quantiles()})


def test_q0_is_the_unweighted_full_history_benchmark():
    """US9: Q0 uses every training target equally (no burn-in, no time decay)."""
    X, r = _garch_sample(n=600)
    y = pd.Series(np.r_[np.full(100, 8.0), r[100:500]], index=X.index[:500])  # early crisis rows
    m = make_risk_model("Q0", 1).fit(X.iloc[:500], y)
    got = m.predict_quantiles(X.iloc[500:503]).to_numpy()
    expected = np.quantile(y.to_numpy(), LEVELS)
    assert np.allclose(got, np.tile(expected, (3, 1)))


@pytest.mark.parametrize("mid", ["Q2", "Q3"])
def test_garch_models_work_without_the_arch_library(mid, monkeypatch):
    """US10: the self-contained Student-t GARCH(1,1) MLE keeps Q2/Q3 calibrated and
    better than constant risk in a minimal environment."""
    import sys

    monkeypatch.setitem(sys.modules, "arch", None)  # `from arch import ...` -> ImportError
    X, r = _garch_sample(seed=5)
    y = _h_target(r, 1, X.index).dropna()
    X = X.loc[y.index]
    res = {}
    for m in ("Q0", mid):
        out = run_walk_forward_quantiles(lambda m=m: make_risk_model(m, 1), X, y,
                                         initial_train_size=1600, refit_every=100)
        res[m] = evaluate_quantile_forecast(out["actual_return"], out[list(LEVELS)], horizon=1)
    assert 0.75 <= res[mid]["coverage_80"] <= 0.85
    assert res[mid]["pinball"] < res["Q0"]["pinball"]
    assert res[mid]["risk_ratio_high_low"] > 1.5
