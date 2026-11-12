"""Forecasting models module."""

from src.models.base import Forecaster
from src.models.baseline import NaivePersistenceModel
from src.models.xgboost_model import XGBoostConfig, XGBoostForecaster

__all__ = ["Forecaster", "NaivePersistenceModel", "XGBoostForecaster", "XGBoostConfig"]
