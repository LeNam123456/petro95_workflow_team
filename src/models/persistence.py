"""Artifact Persistence and Reproducibility Manager for SPAFS V5.2.

Provides zero-retrain serialization and structured storage:
- artifacts/models/: Binary .joblib estimators and .json structural coefficients
- artifacts/predictions/: Full time-series out-of-sample predictions (.parquet)
- artifacts/metrics/: Leaderboard CSVs and hypothesis test reports (.json)
- artifacts/manifests/: Cryptographic execution manifests with SHA-256 hashes
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.models.base import BaseForecastingModel

logger = logging.getLogger("SPAFS_V5.2")


def _get_sha256(filepath: Path | str) -> str:
    """Compute SHA-256 checksum of a file on disk."""
    path = Path(filepath)
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ArtifactManager:
    """Manages reading and writing model artifacts conforming to SPAFS standards.

    Args:
        base_dir (Path | str, optional): Root directory for artifacts. Defaults to 'artifacts'.
    """

    def __init__(self, base_dir: Path | str = "artifacts") -> None:
        self.base_dir = Path(base_dir)
        self.models_dir = self.base_dir / "models"
        self.predictions_dir = self.base_dir / "predictions"
        self.metrics_dir = self.base_dir / "metrics"
        self.manifests_dir = self.base_dir / "manifests"

        for d in (self.models_dir, self.predictions_dir, self.metrics_dir, self.manifests_dir):
            d.mkdir(parents=True, exist_ok=True)

    def save_model(self, model: BaseForecastingModel) -> Path:
        """Save fitted model object to .joblib binary."""
        path = self.models_dir / f"{model.model_id}.joblib"
        model.save(path)
        return path

    def save_coefficients(self, model: BaseForecastingModel) -> Path:
        """Save structural parameters and coefficient tables to formatted .json."""
        summary = model.get_params_summary()
        path = self.models_dir / f"{model.model_id}_coefficients.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("Saved coefficients for %s to %s", model.model_id, path)
        return path

    def save_predictions(self, df: pd.DataFrame, model_id: str, tag: str = "stream1") -> Path:
        """Save point-in-time predictions to .parquet file."""
        path = self.predictions_dir / f"pred_{model_id}_{tag}.parquet"
        df.to_parquet(path, index=True)
        logger.info("Saved predictions for %s to %s (rows=%d)", model_id, path, len(df))
        return path

    def save_metrics(self, data: dict[str, Any], filename: str) -> Path:
        """Save metric reports (e.g. Wald test results) to .json file."""
        path = self.metrics_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Saved metrics to %s", path)
        return path

    def save_leaderboard(self, df: pd.DataFrame, filename: str = "stream1_econometric_leaderboard.csv") -> Path:
        """Save comparative evaluation leaderboard to CSV."""
        path = self.metrics_dir / filename
        df.to_csv(path, index=False)
        logger.info("Saved leaderboard to %s (models=%d)", path, len(df))
        return path

    def create_manifest(
        self,
        stream_name: str,
        models_executed: list[str],
        data_path: Path | str,
        extra_meta: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Build cryptographic execution manifest recording timestamps and SHA-256 hashes."""
        data_p = Path(data_path)
        manifest_data = {
            "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "stream_name": stream_name,
            "models_executed": models_executed,
            "dataset": {
                "path": str(data_p),
                "sha256": _get_sha256(data_p),
            },
            "artifacts_generated": {},
        }

        # Scan generated artifacts
        for f in self.base_dir.glob("**/*"):
            if f.is_file() and not f.name.endswith(".log") and "manifest" not in f.name:
                manifest_data["artifacts_generated"][str(f.relative_to(self.base_dir))] = _get_sha256(f)

        if extra_meta:
            manifest_data["metadata"] = extra_meta

        path = self.manifests_dir / f"{stream_name}_execution_manifest.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info("Created execution manifest at %s", path)
        return path


__all__ = ["ArtifactManager"]
