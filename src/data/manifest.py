"""Packaging utilities for the reproducible experiment manifest and audit reporting.

Assembles:
1. Canonical dataset and physical partition SHA-256 checksums and verification status.
2. Proxy availability flag counts and statistics across canonical and partitioned sets.
3. Point-in-Time (PIT) audit verification and zero-lookahead confirmation.
4. Canonical random seed and complete model hyperparameters.
5. Runtime library and OS execution environment (Python, PyTorch, XGBoost, pandas, etc.).
6. Per-configuration and total execution runtimes.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any
import pandas as pd

from src.data.validation import PITAuditReport


def get_library_environment() -> dict[str, Any]:
    """Inspect and collect runtime environment and library package versions."""
    libs: dict[str, str] = {}

    packages_to_check = [
        "numpy",
        "pandas",
        "torch",
        "xgboost",
        "scipy",
        "sklearn",
        "matplotlib",
        "pyarrow",
        "yaml",
    ]

    for pkg_name in packages_to_check:
        try:
            mod = __import__(pkg_name)
            version = getattr(mod, "__version__", "unknown")
            libs[pkg_name] = str(version)
        except ImportError:
            libs[pkg_name] = "not installed"

    # PyTorch acceleration info
    torch_info: dict[str, Any] = {}
    try:
        import torch
        torch_info["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            torch_info["cuda_device_name"] = str(torch.cuda.get_device_name(0))
        mps_avail = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        torch_info["mps_available"] = bool(mps_avail)
        torch_info["num_threads"] = int(torch.get_num_threads())
    except ImportError:
        torch_info["available"] = False

    return {
        "python_version": platform.python_version(),
        "python_full_version": sys.version,
        "python_executable": sys.executable,
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "libraries": libs,
        "torch_acceleration": torch_info,
    }


def compute_proxy_flag_statistics(
    canonical_df: pd.DataFrame,
    partitions: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    """Compute counts, distributions, and percentages of proxy availability flags."""
    flag_columns = [
        "publication_datetime_is_proxy",
        "availability_datetime_is_proxy",
        "brent_availability_datetime_is_proxy",
        "brent_calendar_exact_match",
        "brent_outlier_flag",
    ]

    def _summarize_flags(df: pd.DataFrame) -> dict[str, Any]:
        res: dict[str, Any] = {"total_rows": len(df)}
        for col in flag_columns:
            if col in df.columns:
                series = df[col]
                # Coerce boolean
                true_c = int((series == True).sum())  # noqa: E712
                false_c = int((series == False).sum())  # noqa: E712
                total_c = len(series)
                res[col] = {
                    "total": total_c,
                    "true_count": true_c,
                    "false_count": false_c,
                    "true_pct": round(float(true_c / total_c * 100.0), 3) if total_c > 0 else 0.0,
                    "false_pct": round(float(false_c / total_c * 100.0), 3) if total_c > 0 else 0.0,
                }
        return res

    summary: dict[str, Any] = {
        "canonical_panel": _summarize_flags(canonical_df),
    }

    if partitions:
        partition_stats: dict[str, Any] = {}
        for part_name, part_df in partitions.items():
            partition_stats[part_name] = _summarize_flags(part_df)
        summary["partitions"] = partition_stats

    return summary


def build_experiment_manifest(
    benchmark_stage: str,
    seed: int,
    models_evaluated: list[str],
    target_representations_evaluated: list[str],
    horizons_evaluated: list[int] | tuple[int, ...],
    splits_manifest_path: str | Path,
    canonical_df: pd.DataFrame,
    pit_audit_report: dict[str, Any] | PITAuditReport,
    splits_integrity: dict[str, Any],
    hyperparameters: dict[str, Any],
    leaderboard_df: pd.DataFrame,
    saved_checkpoints: list[str] | None = None,
    partitions: dict[str, pd.DataFrame] | None = None,
    configuration_runtimes: list[dict[str, Any]] | None = None,
    total_runtime_seconds: float | None = None,
    artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct full reproducible experiment manifest."""
    m_path = Path(splits_manifest_path)
    splits_manifest_content = {}
    if m_path.exists():
        try:
            splits_manifest_content = json.loads(m_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Extract checksums
    checksums = {
        "source_dataset": {
            "path": splits_manifest_content.get("dataset_source", "data/interim/canonical_market_panel.parquet"),
            "sha256": splits_manifest_content.get("source_sha256"),
        },
        "partitions": {},
        "integrity_verification": splits_integrity,
    }

    for p_name, p_info in splits_manifest_content.get("partitions", {}).items():
        checksums["partitions"][p_name] = {
            "rows": p_info.get("rows"),
            "parquet_sha256": p_info.get("parquet_sha256"),
            "csv_sha256": p_info.get("csv_sha256"),
        }

    # Format pit audit
    if isinstance(pit_audit_report, PITAuditReport):
        pit_dict = pit_audit_report.to_dict()
    else:
        pit_dict = dict(pit_audit_report)

    # Proxy flag statistics
    proxy_stats = compute_proxy_flag_statistics(canonical_df, partitions=partitions)

    # Library and environment
    env_info = get_library_environment()

    # Runtimes per configuration
    if configuration_runtimes is None:
        cfg_runtimes: list[dict[str, Any]] = []
        if not leaderboard_df.empty:
            for _, row in leaderboard_df.iterrows():
                cfg_runtimes.append({
                    "model": row.get("model"),
                    "scenario": row.get("scenario"),
                    "target_representation": row.get("target_representation"),
                    "horizon": int(row.get("horizon")) if "horizon" in row else None,
                    "runtime_seconds": float(row.get("runtime_seconds")) if "runtime_seconds" in row and pd.notna(row.get("runtime_seconds")) else None,
                })
        configuration_runtimes = cfg_runtimes

    # Sample counts in test
    test_counts = {}
    for h in horizons_evaluated:
        matches = leaderboard_df[leaderboard_df["horizon"] == h]
        if not matches.empty and "n_samples" in matches.columns:
            test_counts[f"h{h}"] = int(matches["n_samples"].iloc[0])

    manifest: dict[str, Any] = {
        "pipeline": "Pipeline Du bao Diem & Chieu huong Xang Platts Singapore Mogas 95",
        "benchmark_stage": benchmark_stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "models_evaluated": list(models_evaluated),
        "target_representations_evaluated": list(target_representations_evaluated),
        "horizons_evaluated": list(horizons_evaluated),
        "total_configurations": len(leaderboard_df),
        "test_sample_counts": test_counts,
        "data_checksums": checksums,
        "splits_integrity": splits_integrity,
        "proxy_availability_flag_statistics": proxy_stats,
        "pit_audit": pit_dict,
        "hyperparameters": hyperparameters,
        "library_environment": env_info,
        "execution_runtimes": {
            "total_benchmark_runtime_seconds": total_runtime_seconds,
            "configurations": configuration_runtimes,
        },
        "saved_checkpoints": sorted(list(set(saved_checkpoints or []))),
        "artifacts": artifacts or {},
    }

    return manifest


def save_experiment_manifest(manifest: dict[str, Any], output_path: str | Path) -> Path:
    """Serialize and write experiment manifest to formatted JSON file."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return out_p
