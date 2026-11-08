"""Correctness tests for the deepened evaluation and walk-forward modules (SPAFS V5.2).

Each test crosses the public interface only and checks against an independent
closed-form or library computation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from scipy import stats

from src.models.base import BaseForecastingModel
from src.models.econometric import ArmaModel, NaiveDirectionModel, NaiveZeroModel
from src.models.evaluation.forecast_tests import cw_test, dm_test, forecast_metrics, pt_test
from src.models.validation.walk_forward import run_walk_forward_evaluation


@pytest.fixture
def series():
    rng = np.random.default_rng(7)
    y = rng.standard_normal(400)
    good = 0.6 * y + 0.5 * rng.standard_normal(400)
    bad = 0.1 * rng.standard_normal(400)
    return y, good, bad


# --------------------------------------------------------------------------- DM
def test_dm_h1_matches_closed_form(series):
    y, good, bad = series
    d = (y - good) ** 2 - (y - bad) ** 2
    n = len(d)
    raw = d.mean() / np.sqrt(np.var(d) / n)
    hln = np.sqrt((n + 1 - 2 + 0) / n)
    res = dm_test(y, good, bad, horizon=1)
    assert res.hac_lags == 0
    assert res.statistic == pytest.approx(raw * hln)
    assert res.p_value_one_sided == pytest.approx(stats.t.cdf(raw * hln, df=n - 1))
    assert res.statistic < 0 and res.reject_at(0.05)


def test_dm_is_antisymmetric(series):
    y, good, bad = series
    a = dm_test(y, good, bad, horizon=5)
    b = dm_test(y, bad, good, horizon=5)
    assert a.statistic == pytest.approx(-b.statistic)
    assert a.hac_lags == 4
    assert a.p_value_two_sided == pytest.approx(b.p_value_two_sided)


def test_dm_multistep_uses_uniform_h_minus_1_autocovariances(series):
    y, good, bad = series
    h = 3
    d = (y - good) ** 2 - (y - bad) ** 2
    n, dm_ = len(d), d - d.mean()
    g = [np.dot(dm_[k:], dm_[: n - k]) / n for k in range(h)]
    lrv = g[0] + 2 * sum(g[1:])
    expected = d.mean() / np.sqrt(lrv / n) * np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    assert dm_test(y, good, bad, horizon=h).statistic == pytest.approx(expected)


def test_dm_aligns_series_and_drops_nans():
    idx = pd.date_range("2024-01-01", periods=50, freq="B")
    rng = np.random.default_rng(0)
    y = pd.Series(rng.standard_normal(50), index=idx)
    a = pd.Series(rng.standard_normal(50), index=idx)
    b = pd.Series(rng.standard_normal(50), index=idx)
    a.iloc[3] = np.nan
    shuffled = b.sample(frac=1.0, random_state=1)  # different order must not matter
    assert dm_test(y, a, shuffled).sample_size == 49
    assert dm_test(y, a, shuffled).statistic == pytest.approx(dm_test(y, a, b).statistic)


# --------------------------------------------------------------------------- CW
def test_cw_h1_matches_statsmodels_ols_t_stat(series):
    y, good, bad = series
    f = (y - bad) ** 2 - ((y - good) ** 2 - (bad - good) ** 2)
    ols = sm.OLS(f, np.ones(len(f))).fit(cov_type="HAC", cov_kwds={"maxlags": 0, "use_correction": False})
    res = cw_test(y, good, bad, horizon=1)
    assert res.statistic == pytest.approx(float(ols.tvalues[0]), rel=1e-8)
    assert res.p_value_one_sided == pytest.approx(stats.norm.sf(res.statistic))


def test_cw_multistep_uses_same_variance_as_dm(series):
    y, good, bad = series
    h = 5
    f = (y - bad) ** 2 - ((y - good) ** 2 - (bad - good) ** 2)
    n, fm = len(f), f - f.mean()
    g = [np.dot(fm[k:], fm[: n - k]) / n for k in range(h)]
    expected = f.mean() / np.sqrt((g[0] + 2 * sum(g[1:])) / n)
    res = cw_test(y, good, bad, horizon=h)
    assert res.hac_lags == 4
    assert res.statistic == pytest.approx(expected)


def test_cw_rewards_informative_larger_model(series):
    y, good, _ = series
    zero = np.zeros_like(y)
    assert cw_test(y, good, zero).reject_at(0.05)


# --------------------------------------------------------------------------- PT
def test_pt_matches_pesaran_timmermann_1992(series):
    y, good, _ = series
    yu, pu = y > 0, good > 0
    n = len(y)
    P, py, px = np.mean(yu == pu), yu.mean(), pu.mean()
    ps = py * px + (1 - py) * (1 - px)
    v1 = ps * (1 - ps) / n
    v2 = ((2 * py - 1) ** 2 * px * (1 - px) / n + (2 * px - 1) ** 2 * py * (1 - py) / n
          + 4 * py * px * (1 - py) * (1 - px) / n**2)
    expected = (P - ps) / np.sqrt(v1 - v2)
    res = pt_test(y, good)
    assert res.statistic == pytest.approx(expected)
    assert res.statistic > 3


def test_pt_undefined_for_constant_forecast(series):
    y, _, _ = series
    res = pt_test(y, np.zeros_like(y))
    assert np.isnan(res.statistic) and np.isnan(res.p_value_one_sided)


def test_forecast_metrics_suppresses_pt_for_overlapping_targets(series):
    y, good, _ = series
    assert np.isfinite(forecast_metrics(y, good)["pt_stat"])
    m = forecast_metrics(y, good, horizon=5)
    assert np.isnan(m["pt_stat"]) and np.isnan(m["pt_p_value"])


def test_forecast_metrics_r2_against_benchmark(series):
    y, good, bad = series
    m = forecast_metrics(y, good, benchmark=bad)
    expected = (1 - np.mean((y - good) ** 2) / np.mean((y - bad) ** 2)) * 100
    assert m["r2_oos_pct"] == pytest.approx(expected)
    assert forecast_metrics(y, good)["r2_oos_pct"] == pytest.approx(
        (1 - np.mean((y - good) ** 2) / np.mean(y**2)) * 100
    )


# --------------------------------------------------------------------------- Walk-forward
class _Spy(BaseForecastingModel):
    """Records the training window and the rows passed to predict."""

    log: list = []

    def __init__(self):
        super().__init__("M0a")

    def fit(self, X, y):
        self.last_train = len(X) - 1
        self.is_fitted = True
        return self

    def predict(self, X):
        _Spy.log.append((self.last_train, X.index[0], X.index[-1]))
        return pd.Series(0.0, index=X.index)

    def get_params_summary(self):
        return {}


@pytest.mark.parametrize("h,emb,refit", [(1, 0, 1), (5, 2, 20), (21, 5, 7)])
def test_walk_forward_purges_and_embargoes(h, emb, refit):
    T = 300
    X = pd.DataFrame({"a": np.arange(T, dtype=float)})
    y = pd.Series(np.ones(T))
    _Spy.log = []
    res = run_walk_forward_evaluation(lambda: _Spy(), X, y, initial_train_size=200,
                                      refit_every=refit, horizon=h, embargo=emb)
    assert res.num_oos_forecasts == 100
    for tau, (train_end, first, last) in zip(range(200, T), _Spy.log):
        assert train_end + h + emb <= tau  # no label realised after tau - embargo
        assert first == train_end + 1 and last == tau


def test_walk_forward_rejects_too_short_training():
    X = pd.DataFrame({"a": np.zeros(100)})
    with pytest.raises(ValueError):
        run_walk_forward_evaluation(lambda: NaiveZeroModel(), X, pd.Series(np.zeros(100)),
                                    initial_train_size=60, horizon=21, embargo=5)


# --------------------------------------------------------------------------- Models
def _arma_data(n=700, seed=3):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal(n)
    r = np.zeros(n)
    for t in range(1, n):
        r[t] = 0.05 + 0.5 * r[t - 1] + e[t] + 0.2 * e[t - 1]
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"mg95_return_pct": r}, index=idx), r


def test_arma_walk_forward_forecasts_are_informative():
    X, r = _arma_data()
    y = pd.Series(np.r_[r[1:], 0.0], index=X.index)
    res = run_walk_forward_evaluation(lambda: ArmaModel(), X.iloc[:-1], y.iloc[:-1],
                                      initial_train_size=500, refit_every=20)
    p = res.predictions_df
    assert p["predicted_return"].std() > 0.3  # previously ~constant (bug)
    assert np.corrcoef(p["predicted_return"], p["actual_return"])[0, 1] > 0.3


def test_arma_horizon_equals_sum_of_iterated_forecasts():
    X, _ = _arma_data()
    m = ArmaModel(horizon=5).fit(X.iloc[:500], pd.Series(0.0, index=X.index[:500]))
    agg = m.predict(X.iloc[500:510]).iloc[-1]
    expected = m.results_.append(X["mg95_return_pct"].iloc[500:510].to_numpy()).forecast(5).sum()
    assert agg == pytest.approx(float(expected))


def test_persistence_horizon_is_last_realised_h_return():
    X, r = _arma_data(60)
    m = NaiveDirectionModel(horizon=5).fit(X, pd.Series(0.0, index=X.index))
    assert m.predict(X).iloc[-1] == pytest.approx(r[-5:].sum())
