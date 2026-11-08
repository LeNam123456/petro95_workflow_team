# -*- coding: utf-8 -*-
"""Master Pipeline Orchestrator for SPAFS V5.2.

Organizes the entire repository into 3 end-to-end execution flows + verification:

    Flow 1 (data)  : Raw CSV -> 8-gate PIT pipeline -> Multi-horizon targets -> PIT & Stationarity audits
    Flow 2 (point) : Point & direction forecasting (M0a-M5, RNN, LSTM) + DM/CW/PT/Wald tests
    Flow 3 (risk)  : Interval & volatility risk forecasting (Q0-Q4) + Kupiec/Christoffersen/Pinball/DM + figures
    Verify (test)  : Full 81-test suite (pytest)

Usage (recommended environment: D:\\Test\\env_prj\\Scripts\\python.exe):
    python run_pipeline.py --flow test
    python run_pipeline.py --flow data
    python run_pipeline.py --flow point
    python run_pipeline.py --flow risk
    python run_pipeline.py --flow all
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

FLOW_COMMANDS: dict[str, list[tuple[str, list[str]]]] = {
    "data": [
        ("1.1 Point-in-Time Data Pipeline (8 Gates)", ["-m", "src.data_proccessing.pipeline"]),
        ("1.2 Multi-Horizon Target Engineering (h=1,5,21)", ["-m", "src.data_proccessing.data_handling.multi_horizon_targets"]),
        ("1.3 Record-Level PIT Timestamp Audit", ["-m", "src.data_proccessing.data_handling.audit_record_level_pit"]),
        ("1.4 ADF & KPSS Stationarity Audit", ["-m", "src.data_proccessing.data_handling.stationarity_audit"]),
    ],
    "point": [
        ("2.1 Stream 1 Econometric Models (M0a-M3) & RQ1 Wald Tests", ["src/models/runner_econometric.py"]),
        ("2.2 Multi-Horizon Deep Learning Ensembles (RNN, LSTM x 5 seeds)", ["src/models/dl/sequence_models.py"]),
        ("2.3 Multi-Horizon Traditional Models (M0a-M5, h=1,5,21)", ["src/models/runner_multi_horizon_traditional.py"]),
        ("2.4 Stream 2 Machine Learning Models (M4, M5) & RQ2 Tests", ["src/models/runner_ml.py", "--model", "all"]),
        ("2.5 Master Multi-Horizon Consolidation & Shock Analysis", ["src/models/evaluation/consolidate_multi_horizon_analysis.py"]),
        ("2.6 Reproducible Pairwise Statistical Audit (754 OOS sessions)", ["src/models/evaluation/reproducible_pairwise_audit.py"]),
    ],
    "risk": [
        ("3.1 Multi-Horizon Quantile & Risk Models (Q0-Q4 on Stream 1 & 2)", ["src/models/runner_risk_multi_horizon.py", "--dataset", "all"]),
        ("3.2 Risk & Interval Visualization Figures", ["src/models/risk/figures.py"]),
    ],
    "test": [
        ("4.1 Automated Unit & Integration Test Suite (81 tests)", ["-m", "pytest", "-q", "tests"]),
    ],
}


def run_flow(flow_name: str) -> None:
    steps = FLOW_COMMANDS[flow_name]
    print("=" * 78)
    print(f"SPAFS V5.2 — EXECUTING FLOW: {flow_name.upper()} ({len(steps)} steps)")
    print("=" * 78)
    for label, cmd_args in steps:
        t0 = time.time()
        print(f"\n>>> [{label}]")
        print(f"    Command: {sys.executable} {' '.join(cmd_args)}")
        res = subprocess.run([sys.executable, *cmd_args], cwd=PROJECT_ROOT)
        dt = time.time() - t0
        if res.returncode != 0:
            raise SystemExit(f"[FAILED] Step '{label}' exited with code {res.returncode} after {dt:.1f}s.")
        print(f"    [OK] Completed in {dt:.1f}s.")


def main() -> None:
    parser = argparse.ArgumentParser(description="SPAFS V5.2 Master Pipeline Orchestrator")
    parser.add_argument(
        "--flow",
        choices=["data", "point", "risk", "test", "all"],
        default="test",
        help="Pipeline flow to execute (default: test).",
    )
    args = parser.parse_args()

    order = ["test", "data", "point", "risk"] if args.flow == "all" else [args.flow]
    t_start = time.time()
    for fl in order:
        run_flow(fl)
    print("\n" + "=" * 78)
    print(f"ALL REQUESTED FLOWS ({', '.join(order)}) COMPLETED IN {time.time() - t_start:.1f}s.")
    print("=" * 78)


if __name__ == "__main__":
    main()
