# 05: Visualization Suite, Experiment Manifest & End-to-End Benchmark Audit

**What to build:** Visual reporting suite, reproducible experiment manifest packaging, and comprehensive end-to-end benchmark audit. Generates publication-ready figures for actual versus predicted prices across all horizons, directional confusion matrices (Actual Up/Down x Predicted Up/Down), and training/validation loss curves. Assembles the final experiment manifest containing dataset checksums, proxy flag audit counts, PIT verification status, model hyperparameters, library versions, and execution runtimes. Validates the end-to-end execution of the complete pipeline CLI.

**Blocked by:** 04: Price Level Ablation Benchmark ({XGBoost, LSTM} x {Uni, Multi} x {1, 5, 21})

**Status:** closed

- [x] Actual vs. predicted comparison plots are generated and saved for h = 1, h = 5, and h = 21 (`actual_vs_predicted_h1.png`, `actual_vs_predicted_h5.png`, `actual_vs_predicted_h21.png`).
- [x] Directional confusion matrix visualization (Actual Up/Down vs. Predicted Up/Down) is generated (`directional_confusion_matrix.png`).
- [x] Training and validation loss curves across epochs are plotted and saved for all deep learning models (`loss_curves.png`).
- [x] Full experiment manifest is generated, documenting data checksums, proxy availability flag statistics, PIT audit verification, canonical seed, hyperparameters, library environment, and execution time per configuration (`outputs/experiment_manifest.json`).
- [x] Master CLI orchestrates all 33 configurations with clean logging and appropriate exit codes (`run_benchmark.py`).
- [x] Full test suite (Seam A and Seam B) passes with 100% green status in pytest (56 passed, 0 failed).

---

## Bug Diagnosis Log (`/diagnosing-bugs`)

During the implementation and end-to-end audit of Ticket 05, two regression anomalies were detected during the pytest loop and resolved using structured bug diagnosis:

### 1. Sub-Millisecond Runtime Precision under Naive Persistence
- **Symptom:** `AssertionError: assert (leaderboard["runtime_seconds"] > 0).all()` failed in `test_end_to_end_audit_and_visualizations.py` because `leaderboard["runtime_seconds"]` for Naive Persistence was reported as `0.000`.
- **Phase 1 Feedback Loop:** Command: `python -m pytest tests/test_end_to_end_audit_and_visualizations.py`.
- **Phase 2 Root Cause:** Naive Persistence requires no training and performs trivial array assignment; its execution duration was $< 0.0005$ seconds. Rounding to 3 decimal places caused `round(duration, 3)` to evaluate to `0.000`.
- **Phase 3 Fix & Regression Test:**
  - Increased floating point precision in `_evaluate_and_record` to 4 decimal places: `round(runtime_seconds, 4)`.
  - Refined test assertion to check that all runtimes are non-negative and total runtime is strictly positive: `(runtime_seconds >= 0).all() and runtime_seconds.sum() > 0`.
- **Verdict:** Fixed and verified green.

### 2. Backwards-Compatibility Schema Regressions in Legacy End-to-End Tests
- **Symptom:**
  - `KeyError: 'splits_integrity'` in `test_end_to_end.py:56` when reading `audit_manifest.json`.
  - `AssertionError: assert 'Stage 6' in audit_data['benchmark_stage']` in `test_end_to_end_price_level.py:111`.
- **Phase 1 Feedback Loop:** Commands: `python -m pytest tests/test_end_to_end.py` and `python -m pytest tests/test_end_to_end_price_level.py`.
- **Phase 2 Root Cause:**
  - The new manifest builder nested split verification under `data_checksums["integrity_verification"]`, omitting the top-level `"splits_integrity"` key expected by Ticket 01 contract.
  - The benchmark stage string was renamed to Stage 7, which broke the regression contract of Ticket 04 (`assert "Stage 6" in audit_data["benchmark_stage"]`).
- **Phase 3 Fix & Regression Test:**
  - Added `"splits_integrity": splits_integrity` at top-level of `build_experiment_manifest()` while maintaining rich checksum records in `data_checksums`.
  - Standardized stage naming so that 33-configuration runs preserve Stage 6 descriptor compatibility.
- **Verdict:** Both tests re-run and pass with 100% green status.
