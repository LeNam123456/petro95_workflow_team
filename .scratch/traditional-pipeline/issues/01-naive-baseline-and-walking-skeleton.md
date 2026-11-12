# 01: Naive Persistence Baseline & Walking Skeleton Pipeline

**What to build:** A minimal end-to-end forecasting pipeline (Walking Skeleton) and Supervised Sample Builder (Seam B) that reads the immutable Canonical Market Panel and physical splits in read-only mode, audits Point-in-Time (PIT) alignment at the 08:30 SGT forecast origin, extracts lookback windows of 30 sessions, borrows up to 29 sessions of context across partition boundaries, truncates targets extending past partitions, and executes the Naive Persistence baseline for horizons h in {1, 5, 21}. Reconstructs prices in USD/barrel, calculates 6 standard evaluation metrics (MAE, MSE, RMSE, MAPE, R², 3-state Directional Accuracy) alongside actual Up/Down/Flat distributions and majority directional baselines, and generates the initial 3-row leaderboard, per-horizon prediction files, and PIT audit report.

**Blocked by:** None (can start immediately)

**Status:** closed

- [x] Source panel and physical splits are accessed strictly read-only and verified against expected SHA-256 checksums from the splits manifest.
- [x] Point-in-Time audit strictly enforces `feature_available_at <= forecast_origin` (08:30 SGT) and `target_timestamp > forecast_origin`; pipeline halts immediately on violation.
- [x] Supervised sample construction (Seam B) correctly borrows up to 29 observations from the preceding partition as context for early Validation and Test samples.
- [x] Sample truncation at partition boundaries produces exact Test sample counts of 664 (h=1), 660 (h=5), and 644 (h=21).
- [x] Naive Persistence predictions (forecast = latest available price at origin) are evaluated across h in {1, 5, 21}.
- [x] Price reconstruction restores values to USD/barrel before computing MAE, MSE, RMSE, MAPE, R², and 3-state Directional Accuracy.
- [x] 3-state sign rule correctly evaluates Directional Accuracy (unchanged prices are correct only if prediction is also flat); Up/Down/Flat distribution and majority class baseline are reported.
- [x] Initial 3-row benchmark leaderboard, per-horizon prediction files, and audit manifest are written to outputs.
- [x] Seam B tests and Seam A end-to-end tests for the Naive baseline pass in the test suite.
