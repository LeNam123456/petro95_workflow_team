# ADR-0006: Traditional Forecasting Pipeline Foundation & Split Policy Reconciliation

- **Status**: accepted
- **Date**: 2026-11-12
- **Branch**: `feature/traditional-deep-learning-pipeline`
- **Governing Spec**: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`

## Context

The repository contains legacy artifacts from the SPAFS V5.2 project (`GLOSSARY.md` and `docs/adr/0001–0005.md`), which targeted interval and quantile risk forecasting ($Q0\text{–}Q4$, GARCH/FHS, purged walk-forward CV, and log-returns). 

For the new **Pipeline Dự báo Điểm & Chiều hướng Xăng Platts Singapore Mogas 95 (Naive, XGBoost, LSTM, GRU)** specified in `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`, we face six foundational design decisions:
1. **Split reconciliation**: Section 4.2 names files `train_2008_2020`, `val_2021_2023`, `test_2024_2025` with row counts 3,099 / 664 / 665. Pure calendar-year splits yield 3,174 / 751 / 503 rows, whereas 3,099 / 664 / 665 represents an exact 70% / 15% / 15% sequential index split.
2. **Legacy isolation**: ADRs 0001–0005 contradict the REVISED point forecasting methodology (Direct strategy, relative change, sequential split).
3. **Sliding window lookback ($L=30$) across partition boundaries**: Handling of context history for early samples in Validation and Test.
4. **Target horizon truncation at partition tails**: Handling of trailing samples where $t+h$ crosses partition boundaries.
5. **Directional Accuracy (DA) tie-breaking**: Handling zero price changes ($\Delta P = 0$).
6. **Codebase module placement**: Structuring the implementation at root `src/` vs nested subdirectories.

## Decision

1. **Physical Split Policy**: We preserve the existing physical datasets in `data/splits/` with 3,099 (Train), 664 (Validation), and 665 (Test) rows, corresponding to the exact 70% / 15% / 15% sequential index split. The file names `train_2008_2020`, `val_2021_2023`, and `test_2024_2025` are retained as representative market-period identifiers as cited in REVISED Section 4.2. Metadata in `splits_manifest.json` explicitly documents the date bounds (Train: 2008-05-02 to 2020-09-16; Val: 2020-09-17 to 2023-05-09; Test: 2023-05-10 to 2025-12-30).
2. **Legacy SPAFS V5.2 Isolation**: ADRs 0001–0005 and legacy terms in `GLOSSARY.md` are formally declared non-binding for the traditional deep learning pipeline. The ubiquitous language is governed strictly by `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`.
3. **Context Window Padding Across Partitions**: Samples at the start of Validation and Test are permitted to consume up to 29 preceding observations from the immediately prior partition as lookback context ($L=30$). Because these observations are strictly prior to the forecast origin, this satisfies Point-in-Time governance ($\text{feature\_available\_at} \leq \text{forecast\_origin}$) without discarding the initial 29 rows of Validation and Test.
4. **Target Horizon Truncation**: Supervised samples whose target timestamp $t+h$ extends past the partition's end are truncated. On the Test set ($N=665$), evaluated sample counts are strictly $N_{\text{test}}^{(h=1)} = 664$, $N_{\text{test}}^{(h=5)} = 660$, and $N_{\text{test}}^{(h=21)} = 644$.
5. **Directional Accuracy Tie-Breaking**: Directional Accuracy is computed using a 3-state sign function:
   $$\operatorname{sgn}(\Delta P) = \begin{cases} +1 & \text{if } \Delta P > 0 \\ -1 & \text{if } \Delta P < 0 \\ 0 & \text{if } \Delta P = 0 \end{cases}$$
   A forecast is marked correct if and only if $\operatorname{sgn}(\hat{P}_{t+h} - P_t) == \operatorname{sgn}(P_{t+h} - P_t)$. If actual price is unchanged ($\Delta P = 0$), non-zero predictions are classified as incorrect. Actual market distribution (Up%, Down%, Flat%) is reported alongside model DA.
6. **Codebase Module Architecture**: The pipeline is implemented directly under repo root `src/` (`data/`, `features/`, `models/`, `training/`, `evaluation/`) with top-level `configs/`, `experiments/`, and `outputs/`, fully matching Section 9 of REVISED.md.

## Consequences

- All 33 MVP configurations will evaluate on identical, reproducible sample sets without lookahead bias.
- Evaluation metrics will be consistent across Naive baseline, XGBoost, LSTM, and GRU.
- Test set size for $h=21$ is 644, maintaining robust statistical significance (> 2.5 years of trading sessions).
