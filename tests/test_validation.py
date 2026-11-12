from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import pytest

from src.data.validation import (
    PointInTimeViolationError,
    audit_point_in_time,
    verify_splits_integrity,
)


def test_verify_splits_integrity_success() -> None:
    manifest_path = Path("data/splits/splits_manifest.json")
    assert manifest_path.exists()
    report = verify_splits_integrity(manifest_path)
    assert report["all_valid"] is True
    assert len(report["partition_results"]) == 3
    assert report["source_result"]["valid"] is True


def test_verify_splits_integrity_mismatch(tmp_path: Path) -> None:
    fake_manifest = tmp_path / "splits_manifest.json"
    fake_source = tmp_path / "fake_source.parquet"
    fake_source.write_bytes(b"some content")

    manifest_data = {
        "dataset_source": str(fake_source),
        "source_sha256": "wrong_hash_value",
        "partitions": {},
    }
    fake_manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_splits_integrity(fake_manifest, raise_on_error=True)


def test_audit_point_in_time_passes_canonical() -> None:
    df = pd.read_parquet("data/interim/canonical_market_panel.parquet")
    report = audit_point_in_time(df, horizons=(1, 5, 21), raise_on_error=True)
    assert report.passed is True
    assert report.feature_violations == 0
    assert report.target_violations == 0


def test_audit_point_in_time_detects_feature_lookahead() -> None:
    df = pd.read_parquet("data/interim/canonical_market_panel.parquet").head(10).copy()
    # Artificially set an availability timestamp to be AFTER the forecast origin
    df.loc[0, "availability_datetime"] = df.loc[0, "forecast_origin_datetime"] + pd.Timedelta(hours=1)

    with pytest.raises(PointInTimeViolationError, match="Feature lookahead detected"):
        audit_point_in_time(df, horizons=(1,), raise_on_error=True)


def test_audit_point_in_time_detects_target_lookahead() -> None:
    df = pd.read_parquet("data/interim/canonical_market_panel.parquet").head(10).copy()
    # Artificially set target observation time to be BEFORE or EQUAL to forecast origin
    df.loc[1, "observation_datetime"] = df.loc[0, "forecast_origin_datetime"] - pd.Timedelta(hours=1)

    with pytest.raises(PointInTimeViolationError, match="Target lookahead detected"):
        audit_point_in_time(df, horizons=(1,), raise_on_error=True)
