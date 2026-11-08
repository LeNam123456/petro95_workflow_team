# Domain Docs

How the engineering skills consume this repo's domain documentation when exploring or restructuring the SPAFS V5.2 codebase around **Hướng 4 (Dự báo khoảng dao động và rủi ro giá xăng Singapore đa kỳ hạn)**.

## Before exploring, read these

- **`docs/GLOSSARY.md`** (canonical domain glossary for SPAFS V5.2 & Hướng 4)
- **`docs/adr/`**: read Architectural Decision Records (ADRs) that touch the area you are about to work in before proposing changes to data pipelines, walk-forward validation, risk/quantile models (`Q0–Q4`), or evaluation metrics.

If you are working in a specific layer, cross-reference:
- `docs/adr/0001-pivot-multi-horizon-to-interval-and-risk-forecasting.md` for why multi-horizon forecasting targets intervals and risk regimes rather than point direction at weekly/monthly horizons.
- `docs/adr/0002-shared-purged-walk-forward-and-0830-sgt-pit-governance.md` for Point-in-Time (08:30 SGT) and purged walk-forward invariants.
- `docs/adr/0003-fhs-and-linear-quantile-regression-over-ml-for-interval-forecasts.md` for quantile model architecture (`Q0–Q4`) and frozen post-fit variance recursion state.
- `docs/adr/0004-dual-sample-evaluation-and-non-overlapping-backtests.md` for why both Stream 2 (2023–2025) and Stream 1 (2012–2025) are mandatory and why Kupiec/Christoffersen tests subsample every $h$-th origin.
- `docs/adr/0005-repository-restructuring-around-direction-4.md` for the target directory layout and module boundaries.

## File structure

Single-context repo centralized under `docs/`:

```text
/
├── docs/
│   ├── GLOSSARY.md                        ← Canonical ubiquitous language (SPAFS V5.2 & Hướng 4)
│   ├── agents/
│   │   ├── issue-tracker.md               ← Issue tracker & wayfinding conventions
│   │   ├── domain.md                      ← This file: consumer rules for domain docs
│   │   └── triage-labels.md               ← Canonical triage role labels
│   └── adr/
│       ├── 0001-pivot-multi-horizon-to-interval-and-risk-forecasting.md
│       ├── 0002-shared-purged-walk-forward-and-0830-sgt-pit-governance.md
│       ├── 0003-fhs-and-linear-quantile-regression-over-ml-for-interval-forecasts.md
│       ├── 0004-dual-sample-evaluation-and-non-overlapping-backtests.md
│       └── 0005-repository-restructuring-around-direction-4.md
└── src/
    ├── data_proccessing/                  ← Point-in-Time data foundation & feature engineering
    └── models/
        ├── econometric/                   ← Point baselines & asymmetric ADL (M0a–M3)
        ├── ml/                            ← Point LightGBM models (M4–M5)
        ├── risk/                          ← Direction 4 quantile & risk models (Q0–Q4) + figures
        ├── validation/                    ← Shared purged/embargoed walk-forward engine
        └── evaluation/                    ← Point & interval statistical tests (DM, Kupiec, Christoffersen)
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a function signature, or a test name), use the term as defined in `docs/GLOSSARY.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (update `docs/GLOSSARY.md` via `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR in `docs/adr/`, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0002 (shared purged walk-forward & 08:30 SGT cutoff), but worth reopening because…_
