# Domain Docs

How the engineering skills consume this repo's domain documentation when developing the **Pipeline Dự báo Điểm & Chiều hướng Xăng Platts Singapore Mogas 95 (Naive, XGBoost, LSTM, GRU)** on branch `feature/traditional-deep-learning-pipeline`.

## 1. Authoritative Specification

- **`docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`**: **The single authoritative specification** for this project (3 Research Questions RQ1–RQ3, Point-in-Time governance at 08:30 SGT, Direct Multi-Horizon Strategy for $h \in \{1, 5, 21\}$, 33 experiment matrix configurations, 4 MVP models: Naive Persistence, XGBoost, LSTM, GRU, evaluation metrics MAE, MSE, RMSE, MAPE, $R^2$, DA).

## 2. Legacy SPAFS V5.2 Notice (Do Not Apply to Traditional Pipeline)

> [!WARNING] Legacy Documents
> The files `GLOSSARY.md` (and `docs/GLOSSARY.md`) as well as `docs/adr/0001–0005` belong to the legacy **SPAFS V5.2 (Hướng 4: Multi-Horizon Interval & Risk Forecasting)** project (focusing on Quantile Regimes Q0–Q4, GARCH/FHS, and asymmetric ADL).
> 
> **Rules for agents:**
> - Do **not** apply ADR-0001 to ADR-0005 constraints (e.g. interval forecasting over point direction, Q0–Q4 quantile models, purged walk-forward subsampling) to this traditional deep learning pipeline.
> - The vocabulary and constraints in `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` supersede legacy definitions.
> - Any new Architectural Decision Records specific to this project should be added starting from `docs/adr/0006-...`.

## 3. File structure

Single-context repo layout under `docs/`:

```text
/
├── configs/
│   ├── data.yaml
│   ├── experiment.yaml
│   └── models.yaml
├── data/
│   ├── interim/
│   │   └── canonical_market_panel.parquet  ← Immutable dataset (4,428 sessions, 2008–2025, UTC)
│   └── splits/                             ← Physical splits (train_2008_2020, val_2021_2023, test_2024_2025, manifest)
├── docs/
│   ├── PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md  ← Authoritative specification & methodology
│   ├── GLOSSARY.md                                    ← Legacy SPAFS V5.2 glossary (reference only)
│   ├── agents/
│   │   ├── issue-tracker.md                           ← Local Markdown Issue Tracker (.scratch/traditional-pipeline/issues/)
│   │   ├── domain.md                                  ← This file: consumer rules for domain docs
│   │   └── triage-labels.md                           ← Canonical triage role labels
│   └── adr/                                           ← 0001–0005 (legacy SPAFS V5.2), 0006+ (new project)
├── src/
│   ├── data/                                          ← PIT alignment, validation, splitting, dataset
│   ├── features/                                      ← Feature engineering & scaling
│   ├── models/                                        ← Naive baseline, XGBoost, LSTM, GRU
│   ├── training/                                      ← Trainer, callbacks, early stopping
│   └── evaluation/                                    ← Price reconstruction, metrics, visualization
├── experiments/
│   └── benchmark.py                                   ← 33-configuration benchmark runner
├── outputs/
│   ├── checkpoints/                                   ← Checkpoints for LSTM, GRU
│   ├── predictions/                                   ← Predictions by horizon (h=1, 5, 21)
│   ├── figures/                                       ← Plots (actual vs predicted, confusion matrix, loss curves)
│   ├── benchmark_leaderboard.csv                      ← 33-configuration benchmark leaderboard
│   └── experiment_manifest.json                       ← Experiment metadata & reproducibility audit
├── run_benchmark.py
└── README.md
```

## 4. Use the REVISED specification vocabulary

When your output names a domain concept (in an issue title, a spec, a code implementation, a function signature, or a test name), use the terms defined in `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`.
