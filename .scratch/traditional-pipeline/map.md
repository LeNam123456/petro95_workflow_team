# Wayfinding Map: Traditional Forecasting Pipeline

Governing Spec: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`
Active Spec: `.scratch/traditional-pipeline/spec.md`
Tracker Directory: `.scratch/traditional-pipeline/issues/`

## Notes
- Physical splits in `data/splits/` are immutable (3,099 Train, 664 Val, 665 Test).
- Forecast origin is strictly 08:30 Asia/Singapore (`feature_available_at <= forecast_origin`).
- Primary target: Relative Change with Local Window Normalization ($L=30$).
- Secondary ablation: Price Level with Train-only scaler and no Test clipping.
- Canonical seed: 42 for all 33 MVP configurations.
- Testing seams: Seam A (Benchmark Runner) and Seam B (Supervised Sample Builder).

## Decisions-so-far
- **ADR-0006**: Split Reconciliation (70/15/15 sequential index split with representative market-period file names), Legacy SPAFS V5.2 isolation, Context borrowing (up to 29 sessions), Target horizon truncation (Test sample counts: 664, 660, 644), 3-state Directional Accuracy sign rule.
- **ADR-0007**: XGBoost Feature Set (32 features Univariate, 64 features Multivariate, zero raw price spread), Canonical seed 42, Output schemas and checkpoint names.

## Tickets & Frontier
- [x] [01-naive-baseline-and-walking-skeleton.md](file:///d:/Petro_95/.scratch/traditional-pipeline/issues/01-naive-baseline-and-walking-skeleton.md) — Blocked by: None (Completed)
- [x] [02-xgboost-relative-change-benchmark.md](file:///d:/Petro_95/.scratch/traditional-pipeline/issues/02-xgboost-relative-change-benchmark.md) — Blocked by: 01 (Completed)
- [x] [03-sequence-deep-learning-benchmark.md](file:///d:/Petro_95/.scratch/traditional-pipeline/issues/03-sequence-deep-learning-benchmark.md) — Blocked by: 01 (Completed)
- [ ] [04-price-level-ablation-benchmark.md](file:///d:/Petro_95/.scratch/traditional-pipeline/issues/04-price-level-ablation-benchmark.md) — Blocked by: 02, 03 *(Current Frontier)*
- [ ] [05-visualizations-manifest-and-audit.md](file:///d:/Petro_95/.scratch/traditional-pipeline/issues/05-visualizations-manifest-and-audit.md) — Blocked by: 04
