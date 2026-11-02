"""Machine learning model family for SPAFS V5.2.

Provides:
- TechnicalLGBMModel (M4)
- EconomicLGBMModel (M5)
"""

from .lgbm import EconomicLGBMModel, TechnicalLGBMModel

__all__ = ["TechnicalLGBMModel", "EconomicLGBMModel"]
