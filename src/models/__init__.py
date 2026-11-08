"""SPAFS V5.2 Modeling and Forecasting Framework.

Subpackages:
- econometric: M0a, M0b, M1, M2, M3
- ml: M4 (Technical LightGBM)
- evaluation: forecast_metrics, DM/CW/PT tests (forecast_tests), Wald hypothesis tests
- validation: Expanding-window walk-forward engine with purging/embargo (any horizon)
- diagnostics: Multicollinearity (VIF, Condition Number) & Residual diagnostics
- persistence: ArtifactManager for reproducible storage
"""

from .base import BaseForecastingModel
from .diagnostics import diagnose_multicollinearity, diagnose_residuals
from .econometric import (
    ArmaModel,
    AsymmetricAdlModel,
    LinearDynamicModel,
    NaiveDirectionModel,
    NaiveZeroModel,
)
from .evaluation import (
    TestResult,
    WaldTestResult,
    cw_test,
    dm_test,
    forecast_metrics,
    pt_test,
    run_wald_test,
)
from .ml import TechnicalLGBMModel
from .persistence import ArtifactManager
from .validation import WalkForwardResult, run_walk_forward_evaluation

__all__ = [
    # Base & Core
    "BaseForecastingModel",
    "ArtifactManager",
    # Econometric models (M0a to M3)
    "NaiveZeroModel",
    "NaiveDirectionModel",
    "ArmaModel",
    "LinearDynamicModel",
    "AsymmetricAdlModel",
    # Machine learning (M4)
    "TechnicalLGBMModel",
    # Diagnostics
    "diagnose_multicollinearity",
    "diagnose_residuals",
    # Evaluation & Hypothesis testing
    "forecast_metrics",
    "dm_test",
    "cw_test",
    "pt_test",
    "TestResult",
    "WaldTestResult",
    "run_wald_test",
    # Validation & Walk-Forward
    "WalkForwardResult",
    "run_walk_forward_evaluation",
]
