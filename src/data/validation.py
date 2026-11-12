"""Data integrity verification and Point-in-Time (PIT) auditing.

Enforces:
1. Canonical panel and physical splits read-only checksum verification.
2. PIT governance: feature_available_at <= forecast_origin and
   target_timestamp > forecast_origin.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
import pandas as pd


class PointInTimeViolationError(Exception):
    """Raised when data violates Point-in-Time causal ordering."""


@dataclass(frozen=True)
class PITAuditReport:
    """Audit report of Point-in-Time checks across horizons."""

    passed: bool
    total_rows: int
    feature_violations: int
    target_violations: int
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_sha256(file_path: Path | str) -> str:
    """Compute the SHA-256 hex digest of a file in streaming chunks."""
    path = Path(file_path)
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_splits_integrity(
    manifest_path: str | Path,
    base_dir: str | Path | None = None,
    raise_on_error: bool = False,
) -> dict[str, Any]:
    """Verify SHA-256 hashes of canonical source and split files against splits_manifest.json."""
    manifest_p = Path(manifest_path)
    root = Path(base_dir) if base_dir is not None else manifest_p.parent.parent.parent
    splits_dir = manifest_p.parent

    manifest_data = json.loads(manifest_p.read_text(encoding="utf-8"))

    partition_results: dict[str, dict[str, Any]] = {}
    all_valid = True

    # 1. Source verification
    source_rel = manifest_data.get("dataset_source")
    expected_src_sha = manifest_data.get("source_sha256")
    source_result: dict[str, Any] = {"path": source_rel, "valid": True}

    if source_rel and expected_src_sha:
        src_path = Path(source_rel) if Path(source_rel).is_absolute() else root / source_rel
        if not src_path.exists():
            source_result["valid"] = False
            source_result["error"] = f"Source file not found: {src_path}"
            all_valid = False
        else:
            actual_src_sha = compute_sha256(src_path)
            if actual_src_sha != expected_src_sha:
                source_result["valid"] = False
                source_result["expected_sha256"] = expected_src_sha
                source_result["actual_sha256"] = actual_src_sha
                all_valid = False

    # 2. Partitions verification
    for part_name, info in manifest_data.get("partitions", {}).items():
        parquet_name = f"{part_name}.parquet"
        csv_name = f"{part_name}.csv"
        parquet_path = splits_dir / parquet_name
        csv_path = splits_dir / csv_name

        part_res: dict[str, Any] = {"parquet_valid": True, "csv_valid": True}

        if "parquet_sha256" in info:
            if not parquet_path.exists():
                part_res["parquet_valid"] = False
                all_valid = False
            else:
                act_p_sha = compute_sha256(parquet_path)
                if act_p_sha != info["parquet_sha256"]:
                    part_res["parquet_valid"] = False
                    part_res["parquet_error"] = f"Expected {info['parquet_sha256']}, got {act_p_sha}"
                    all_valid = False

        if "csv_sha256" in info:
            if not csv_path.exists():
                part_res["csv_valid"] = False
                all_valid = False
            else:
                act_c_sha = compute_sha256(csv_path)
                if act_c_sha != info["csv_sha256"]:
                    part_res["csv_valid"] = False
                    part_res["csv_error"] = f"Expected {info['csv_sha256']}, got {act_c_sha}"
                    all_valid = False

        partition_results[part_name] = part_res

    if not all_valid and raise_on_error:
        raise ValueError(f"Checksum mismatch or missing files in splits manifest: {manifest_path}")

    return {
        "all_valid": all_valid,
        "source_result": source_result,
        "partition_results": partition_results,
    }


def audit_point_in_time(
    df: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 21),
    raise_on_error: bool = True,
) -> PITAuditReport:
    """Audit Point-in-Time compliance on a market panel.

    Rules enforced:
    - feature_available_at <= forecast_origin_datetime
    - target_observation_datetime > forecast_origin_datetime for all horizons
    """
    total_rows = len(df)
    origin_col = "forecast_origin_datetime"
    if origin_col not in df.columns:
        raise ValueError(f"Required forecast origin column '{origin_col}' not in DataFrame.")

    feature_cols = [
        col for col in ["availability_datetime", "brent_availability_datetime"]
        if col in df.columns
    ]

    feature_violations = 0
    violation_details: dict[str, Any] = {}

    for col in feature_cols:
        viol_mask = df[col] > df[origin_col]
        count = int(viol_mask.sum())
        if count > 0:
            feature_violations += count
            violation_details[f"feature_{col}"] = {
                "count": count,
                "first_violation_index": int(viol_mask.idxmax()),
            }

    target_violations = 0
    if "observation_datetime" in df.columns:
        obs_col = "observation_datetime"
        for h in horizons:
            shifted_target = df[obs_col].shift(-h)
            valid_mask = shifted_target.notna()
            # Target timestamp must be strictly after forecast origin
            viol_mask = valid_mask & (shifted_target <= df[origin_col])
            count = int(viol_mask.sum())
            if count > 0:
                target_violations += count
                violation_details[f"target_h{h}"] = {
                    "count": count,
                    "first_violation_index": int(viol_mask.idxmax()),
                }

    passed = (feature_violations == 0) and (target_violations == 0)

    if not passed and raise_on_error:
        if feature_violations > 0:
            raise PointInTimeViolationError(
                f"Feature lookahead detected: {feature_violations} violations! Details: {violation_details}"
            )
        if target_violations > 0:
            raise PointInTimeViolationError(
                f"Target lookahead detected: {target_violations} violations! Details: {violation_details}"
            )

    return PITAuditReport(
        passed=passed,
        total_rows=total_rows,
        feature_violations=feature_violations,
        target_violations=target_violations,
        details=violation_details,
    )
