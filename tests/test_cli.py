from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import pytest


def test_cli_help() -> None:
    res = subprocess.run(
        [sys.executable, "run_benchmark.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Mogas 95 Forecasting Pipeline Benchmark Runner" in res.stdout
    assert "--audit-only" in res.stdout


def test_cli_audit_only() -> None:
    res = subprocess.run(
        [sys.executable, "run_benchmark.py", "--audit-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "POINT-IN-TIME (PIT) & SPLIT INTEGRITY AUDIT" in res.stdout
    assert "Zero Lookahead Bias Verified: True" in res.stdout


def test_cli_execution_naive(tmp_path: Path) -> None:
    out_dir = tmp_path / "cli_outputs"
    res = subprocess.run(
        [
            sys.executable,
            "run_benchmark.py",
            "--model", "naive",
            "--horizons", "1",
            "--no-include-ablation",
            "--output-dir", str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert (out_dir / "benchmark_leaderboard.csv").exists()
    assert (out_dir / "experiment_manifest.json").exists()
    assert (out_dir / "figures" / "actual_vs_predicted_h1.png").exists()
