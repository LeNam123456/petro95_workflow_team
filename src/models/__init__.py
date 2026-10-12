"""SPAFS V5.2 Modeling and Forecasting Framework.

Subpackages:
- econometric: M0a, M0b, M1, M2, M3
- ml: M4 (Technical LightGBM)
- evaluation: Metrics, Wald Hypothesis Tests, Pairwise Tests (Diebold-Mariano, Clark-West)
- validation: Expanding Window Walk-Forward 1-step-ahead engine
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
    PairwiseTestResult,
    WaldTestResult,
    clark_west_test,
    compute_directional_metrics,
    compute_regression_metrics,
    diebold_mariano_test,
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
    "compute_regression_metrics",
    "compute_directional_metrics",
    "WaldTestResult",
    "run_wald_test",
    "PairwiseTestResult",
    "diebold_mariano_test",
    "clark_west_test",
    # Validation & Walk-Forward
    "WalkForwardResult",
    "run_walk_forward_evaluation",
]
