"""Data ingestion, validation, sample building, scaling, and manifest modules."""

from src.data.dataset import SupervisedBatch, build_supervised_samples
from src.data.manifest import (
    build_experiment_manifest,
    compute_proxy_flag_statistics,
    get_library_environment,
    save_experiment_manifest,
)
from src.data.scaling import PriceLevelScaler, TabularPriceLevelScaler
from src.data.splitting import load_physical_splits
from src.data.validation import audit_point_in_time, verify_splits_integrity

__all__ = [
    "SupervisedBatch",
    "build_supervised_samples",
    "PriceLevelScaler",
    "TabularPriceLevelScaler",
    "load_physical_splits",
    "audit_point_in_time",
    "verify_splits_integrity",
    "build_experiment_manifest",
    "compute_proxy_flag_statistics",
    "get_library_environment",
    "save_experiment_manifest",
]
