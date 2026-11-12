# ADR-0009: Visualization Suite, Manifest Packaging & End-to-End Benchmark Audit

- **Status**: accepted
- **Date**: 2026-11-12
- **Branch**: `feature/traditional-deep-learning-pipeline`
- **Governing Spec**: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` (Sections 10 and 12)

## Context

To achieve full academic reproducibility, transparent Point-in-Time (PIT) verification, and publication-ready reporting for the Platts Singapore Mogas 95 forecasting benchmark:
1. `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` Section 10 specifies mandatory visual outputs and manifest artifacts:
   - `outputs/figures/actual_vs_predicted_h1.png`, `actual_vs_predicted_h5.png`, `actual_vs_predicted_h21.png`
   - `outputs/figures/directional_confusion_matrix.png`
   - `outputs/figures/loss_curves.png`
   - `outputs/experiment_manifest.json`
2. Ticket 05 requires:
   - Publication-ready figures comparing actual prices vs. predicted prices across all horizons ($h \in \{1, 5, 21\}$) with residual time series.
   - 2x2 Directional confusion matrix heatmaps (Actual Up/Down vs. Predicted Up/Down) across models and horizons, reporting Accuracy, Precision, and Recall for both Up and Down states.
   - Training and validation loss curves across epochs for all neural network configurations.
   - Full experiment manifest packaging data checksums (SHA-256), proxy availability flag counts and distributions, PIT audit verification, canonical seed, complete hyperparameters, runtime library versions (Python, PyTorch, XGBoost, etc.), and per-configuration execution runtimes.
   - Master CLI orchestrating all 33 configurations with clean logging, `--audit-only`, and `--export-only-plots`.

## Decision

1. **Visualization Module (`src/evaluation/visualization.py`)**:
   - `compute_directional_confusion_matrix`: Computes binary Up/Down classification metrics where Up is defined by $\Delta P > 0$ and Down is $\Delta P \le 0$. Computes TP, FN, FP, TN, Directional Accuracy, Sensitivity (Up Recall), Specificity (Down Recall), Precision (Up), and Precision (Down).
   - `plot_actual_vs_predicted`: Two-panel publication figure:
     - Upper panel: Actual Mogas 95 physical price series (solid black) alongside multi-model predictions (Naive, XGBoost, LSTM, GRU).
     - Lower panel: Forecast error / residual time series ($e_t = \hat{P}_t - P_t$) with zero-reference baseline.
   - `plot_directional_confusion_matrices`: Multi-panel $3 \times 3$ grid displaying confusion matrix heatmaps across all three forecast horizons ($h = 1, 5, 21$) for XGBoost, LSTM, and GRU models.
   - `plot_loss_curves`: Multi-panel loss curve figures for all deep learning architectures across training epochs.
2. **Experiment Manifest Packaging (`src/data/manifest.py`)**:
   - `compute_proxy_flag_statistics`: Audits proxy availability flags (`publication_datetime_is_proxy`, `availability_datetime_is_proxy`, `brent_availability_datetime_is_proxy`, `brent_calendar_exact_match`, `brent_outlier_flag`) across the canonical dataset and physical splits (Train, Val, Test).
   - `get_library_environment`: Captures OS platform, architecture, Python version, PyTorch acceleration status (CUDA/MPS/CPU threads), and version strings for all key numerical dependencies (`numpy`, `pandas`, `torch`, `xgboost`, `scipy`, `sklearn`, `matplotlib`, `pyarrow`, `yaml`).
   - `build_experiment_manifest`: Packages SHA-256 checksums, PIT audit verification, proxy statistics, hyperparameters, library environment, per-configuration runtimes, and generated artifact references into `outputs/experiment_manifest.json` and `outputs/audit_manifest.json`.
3. **Execution Runtime Tracking**:
   - In `experiments/benchmark.py`, model fitting and evaluation time is recorded per configuration and stored as `runtime_seconds` in `outputs/benchmark_leaderboard.csv` and documented in `outputs/experiment_manifest.json`.
4. **Master CLI Orchestration (`run_benchmark.py`)**:
   - Provides `--audit-only` for instant PIT audit and data checksum verification.
   - Provides `--export-only-plots` to re-generate publication figures from existing prediction files without re-training models.
   - Returns exit code 0 on successful benchmark execution or audit verification, and non-zero on failure.

## Consequences

- All 5 required publication-ready figures are generated and saved in `outputs/figures/`.
- Full traceability and reproducibility metadata is packaged in `outputs/experiment_manifest.json`.
- The complete test suite (56 tests) verifies Seam A (Benchmark Runner & Manifest) and Seam B (Supervised Dataset & Feature Pipeline) with 100% green status in pytest and zero mypy typing errors.
