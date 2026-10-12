"""Unit and Integration Tests for SPAFS V5.2 Model Implementations (M0a to M4).

Tests:
1. M0a (NaiveZeroModel): EMH zero baseline contract.
2. M0b (NaiveDirectionModel): Directional momentum contract.
3. M1 (ArmaModel): Univariate MLE Kalman Filter fitting & prediction.
4. M2 (LinearDynamicModel): Symmetric dynamic OLS with Newey-West HAC covariance.
5. M3 (AsymmetricAdlModel): Asymmetric ADL with 3 Wald hypothesis tests for RQ1.
6. M4 (TechnicalLGBMModel): Multi-seed LightGBM ensemble training & feature importances.
7. Residual diagnostics (Ljung-Box, ARCH-LM, Jarque-Bera).
8. Pairwise tests (Diebold-Mariano HLN 1997, Clark-West 2007).
9. Walk-Forward expanding window out-of-sample simulation.
10. Model persistence and joblib roundtrip serialization.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_proccessing.model_schemas import extract_model_matrix
from src.models import (
    ArmaModel,
    ArtifactManager,
    AsymmetricAdlModel,
    LinearDynamicModel,
    NaiveDirectionModel,
    NaiveZeroModel,
    TechnicalLGBMModel,
    clark_west_test,
    compute_directional_metrics,
    compute_regression_metrics,
    diagnose_residuals,
    diebold_mariano_test,
    run_walk_forward_evaluation,
)

STREAM1_PARQUET = Path("data/processed/stream1_econometric_2008_2025.parquet")


@pytest.fixture(scope="session")
def stream1_df():
    if not STREAM1_PARQUET.exists():
        pytest.skip("Stream 1 Parquet dataset not found on disk")
    return pd.read_parquet(STREAM1_PARQUET)


class TestEconometricModelsM0ToM3:
    """Verifies econometric models M0a through M3 on empirical dataset."""

    def test_m0a_naive_zero(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M0a")
        model = NaiveZeroModel()
        model.fit(mat.X, mat.y)
        assert model.is_fitted

        preds = model.predict(mat.X)
        assert (preds == 0.0).all()
        assert len(preds) == len(mat.y)
        assert preds.index.equals(mat.y.index)

        dirs = model.predict_direction(mat.X)
        assert (dirs == 0).all()

        summary = model.get_params_summary()
        assert summary["model_id"] == "M0a"
        assert summary["num_parameters"] == 0

    def test_m0b_naive_direction(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M0b")
        model = NaiveDirectionModel()
        model.fit(mat.X, mat.y)
        assert model.is_fitted

        preds = model.predict(mat.X)
        dirs = model.predict_direction(mat.X)
        assert len(preds) == len(mat.y)

        # Direction should match sign(mg95_return_pct > 0)
        expected_dir = (mat.X["mg95_return_pct"] > 0.0).astype(int)
        assert (dirs == expected_dir).all()

    def test_m1_arma_mle(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M1")
        # Fit on last 500 rows for fast testing
        sample_X = mat.X.iloc[-500:]
        sample_y = mat.y.iloc[-500:]

        model = ArmaModel(order=(1, 0, 1))
        model.fit(sample_X, sample_y)
        assert model.is_fitted

        preds = model.predict(sample_X)
        assert len(preds) == len(sample_y)
        assert not np.isnan(preds).any()

        summary = model.get_params_summary()
        assert "coefficients" in summary
        assert "ar.L1" in summary["coefficients"]
        assert "ma.L1" in summary["coefficients"]

    def test_m2_linear_dynamic_hac(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M2")
        model = LinearDynamicModel(hac_lags=5)
        model.fit(mat.X, mat.y)
        assert model.is_fitted

        preds = model.predict(mat.X)
        assert len(preds) == len(mat.y)
        assert not np.isnan(preds).any()

        summary = model.get_params_summary()
        assert summary["hac_lags"] == 5
        assert summary["r_squared"] > 0.0
        assert "spread_mg95_brent_lag1" in summary["coefficients"]
        assert "brent_return_pct_aligned" in summary["coefficients"]

    def test_m3_asymmetric_adl_and_wald_tests(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M3")
        model = AsymmetricAdlModel(hac_lags=5)
        model.fit(mat.X, mat.y)
        assert model.is_fitted

        # Contemporaneous asymmetry test: H0^(1)
        w1 = model.test_contemporaneous_asymmetry()
        assert "wald_f_stat" in w1
        assert "p_value" in w1
        assert 0.0 <= w1["p_value"] <= 1.0

        # Cumulative 2-day asymmetry test: H0^(2)
        w2 = model.test_cumulative_asymmetry()
        assert "sum_beta_pos" in w2
        assert "sum_beta_neg" in w2
        assert 0.0 <= w2["p_value"] <= 1.0

        # Joint nested symmetry test: H0^(joint) (df=2)
        wj = model.test_joint_nested_symmetry()
        assert wj["df"] == 2
        assert 0.0 <= wj["p_value"] <= 1.0

        summary = model.get_params_summary()
        assert "wald_test_contemporaneous" in summary
        assert "wald_test_cumulative" in summary
        assert "wald_test_joint_nested" in summary


class TestMachineLearningModelM4:
    """Verifies technical LightGBM model M4."""

    def test_m4_technical_lgbm(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M4")
        # Train on last 400 rows with 2 seeds for fast test
        X_sub = mat.X.iloc[-400:]
        y_sub = mat.y.iloc[-400:]

        model = TechnicalLGBMModel(n_estimators=20, seeds=(42, 101))
        model.fit(X_sub, y_sub)
        assert model.is_fitted

        preds = model.predict(X_sub)
        assert len(preds) == len(y_sub)
        assert not np.isnan(preds).any()

        dirs = model.predict_direction(X_sub)
        assert set(dirs.unique()).issubset({0, 1})

        summary = model.get_params_summary()
        assert summary["num_seeds"] == 2
        assert "feature_importance_gain" in summary
        assert len(summary["feature_importance_gain"]) == 10


class TestEvaluationAndDiagnostics:
    """Verifies metrics, pairwise tests, and diagnostics."""

    def test_metrics_calculation(self):
        y_true = pd.Series([1.0, -2.0, 3.0, -1.0, 2.0])
        y_pred = pd.Series([0.8, -1.5, 2.5, -0.5, 1.8])
        y_bench = pd.Series([0.0, 0.0, 0.0, 0.0, 0.0])

        reg_m = compute_regression_metrics(y_true, y_pred, y_bench)
        assert reg_m["rmse"] > 0.0
        assert reg_m["mae"] > 0.0
        assert "oos_r2" in reg_m

        dir_m = compute_directional_metrics(y_true > 0, y_pred > 0)
        assert 0.0 <= dir_m["directional_accuracy"] <= 1.0
        assert "pt_stat" in dir_m
        assert "pt_p_value" in dir_m

    def test_pairwise_diebold_mariano_and_clark_west(self):
        rng = np.random.default_rng(42)
        y_true = rng.standard_normal(100)
        e_cand = rng.standard_normal(100) * 0.8
        e_bench = rng.standard_normal(100) * 1.2

        # DM test
        dm_res = diebold_mariano_test(e_cand, e_bench, loss="squared", h=1)
        assert dm_res.sample_size == 100
        assert 0.0 <= dm_res.p_value <= 1.0

        # CW test
        pred_small = y_true - e_bench
        pred_large = y_true - e_cand
        cw_res = clark_west_test(y_true, pred_small, pred_large)
        assert cw_res.sample_size == 100
        assert 0.0 <= cw_res.p_value <= 1.0

    def test_residual_diagnostics(self):
        rng = np.random.default_rng(42)
        res = pd.Series(rng.standard_normal(200))
        diag = diagnose_residuals(res, lags=(1, 5))
        assert diag["n_obs"] == 200
        assert "jarque_bera" in diag
        assert "ljung_box" in diag
        assert "arch_lm" in diag


class TestValidationAndPersistence:
    """Verifies walk-forward simulation and artifact persistence."""

    def test_walk_forward_simulation(self, stream1_df):
        mat = extract_model_matrix(stream1_df, "M0a")
        # Run small window: 100 train, 20 test steps
        X_sub = mat.X.iloc[:120]
        y_sub = mat.y.iloc[:120]

        wf_res = run_walk_forward_evaluation(
            model_factory=lambda: NaiveZeroModel(),
            X=X_sub,
            y=y_sub,
            initial_train_size=100,
            refit_every=5,
        )
        assert wf_res.num_oos_forecasts == 20
        assert len(wf_res.predictions_df) == 20
        assert "residual" in wf_res.predictions_df.columns
        assert (wf_res.predictions_df["predicted_return"] == 0.0).all()

    def test_artifact_manager_save_load(self, stream1_df, tmp_path):
        mat = extract_model_matrix(stream1_df, "M2")
        model = LinearDynamicModel(hac_lags=5)
        model.fit(mat.X.iloc[:100], mat.y.iloc[:100])

        mgr = ArtifactManager(base_dir=tmp_path)
        joblib_path = mgr.save_model(model)
        assert joblib_path.exists()

        coef_path = mgr.save_coefficients(model)
        assert coef_path.exists()

        # Test reload
        loaded = LinearDynamicModel.load(joblib_path)
        assert loaded.model_id == "M2"
        assert loaded.is_fitted
        p1 = model.predict(mat.X.iloc[100:105])
        p2 = loaded.predict(mat.X.iloc[100:105])
        assert (p1 == p2).all()
