"""Forecasting models module."""

from __future__ import annotations

from src.models.base import Forecaster
from src.models.baseline import NaivePersistenceModel
from src.models.gru import GRUForecaster, GRUNet
from src.models.lstm import LSTMForecaster, LSTMNet
from src.models.xgboost_model import XGBoostConfig, XGBoostForecaster

__all__ = [
    "Forecaster",
    "NaivePersistenceModel",
    "XGBoostConfig",
    "XGBoostForecaster",
    "LSTMForecaster",
    "LSTMNet",
    "GRUForecaster",
    "GRUNet",
]
