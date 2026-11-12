# ADR-0007: XGBoost Feature Specification & Benchmark Execution Protocol

- **Status**: accepted
- **Date**: 2026-11-12
- **Branch**: `feature/traditional-deep-learning-pipeline`
- **Governing Spec**: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`

## Context

Following ADR-0006, three operational decisions remained open for the 33-configuration benchmark pipeline:
1. **XGBoost Feature Representation**: Tabular gradient boosting models require fixed-dimension feature vectors from the 30-session window. Under the Relative Change paradigm, including a raw price crack spread ($P^M_o - P^B_o$) would inject non-stationary price level information into stationary relative change regressions.
2. **Benchmark Execution & Seed Determinism**: Deep learning models (LSTM, GRU) require random initialization. We need deterministic results across runs while providing optional multi-seed support.
3. **Output Artifact Schemas**: Standardizing the structure of predictions, checkpoints, and experiment manifests.

## Decision

1. **XGBoost Feature Set**:
   - *Univariate (32 features)*: 30 locally-normalized relative lags of Mogas ($z^{(M)}_{o,k} = P^M_{o-k}/P^M_o - 1$ for $k=0 \dots 29$) plus 2 return/momentum features ($R_1 = (P^M_o - P^M_{o-1})/P^M_{o-1}$ and $R_5 = (P^M_o - P^M_{o-5})/P^M_{o-5}$).
   - *Multivariate (64 features)*: 32 Mogas features + 32 corresponding Brent features ($z^{(B)}_{o,k}$ for $k=0 \dots 29$, $R_1^{(B)}$, $R_5^{(B)}$).
   - Raw price spread ($P^M_o - P^B_o$) is excluded from MVP feature sets to avoid non-stationary contamination.
2. **Execution Protocol & Seed Policy**:
   - `run_benchmark.py` executes with a fixed canonical `seed = 42` (controlling PyTorch CPU/CUDA, XGBoost random state, NumPy, and Python hash seed) for all 33 configurations to generate the canonical `outputs/benchmark_leaderboard.csv`.
   - The CLI supports an optional `--seeds` argument (e.g. `--seeds 42,43,44`) for multi-seed sensitivity analysis without impacting standard 1-click execution.
3. **Output Standardization**:
   - Per-horizon prediction files: `outputs/predictions/predictions_h1.csv`, `predictions_h5.csv`, `predictions_h21.csv`.
   - Schema: `forecast_origin`, `target_timestamp`, `horizon`, `model`, `scenario`, `target_representation`, `actual_price`, `predicted_price` (both prices in USD/bbl).
   - Checkpoints: `outputs/checkpoints/<model>_<scenario>_<representation>_h<horizon>.pt` saved upon lowest Validation Loss via Early Stopping (patience = 15).

## Consequences

- Tabular features are mathematically stationary, matching the Relative Change regression target.
- Full reproducibility of `outputs/benchmark_leaderboard.csv` and `outputs/experiment_manifest.json`.
- Strict decoupling between fast canonical benchmark runs and multi-seed sensitivity runs.
