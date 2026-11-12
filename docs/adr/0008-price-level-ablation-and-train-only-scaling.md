# ADR-0008: Price Level Ablation Specification & Train-Only Normalization Policy

- **Status**: accepted
- **Date**: 2026-11-12
- **Branch**: `feature/traditional-deep-learning-pipeline`
- **Governing Spec**: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`

## Context

To address Research Question 1 (RQ1: Target Representation — Relative Change vs. direct Price Level), `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md` (Sections 3.2, 6.2, and 12) specifies a secondary ablation study evaluating direct Price Level forecasting ($y_{o,h} = P^M_{o+h}$) against the primary Relative Change methodology.

Three core technical requirements govern the Price Level ablation:
1. **Train-Only Normalization Policy**: For models requiring feature and target scaling (particularly neural architectures), scalers must be fitted strictly and exclusively on the Train partition (2008–2020). Validation (2021–2023) and Test (2024–2025) data must be transformed strictly using Train statistics without updating mean or variance parameters.
2. **Strict No-Clipping Invariant**: Values in Validation and Test that fall outside the historical Train price range (such as high-volatility spikes or regime shifts) must **never** be clipped or clamped to the Train minimum or maximum. Neural network architectures must utilize an unconstrained linear output head ($\text{Linear}(H, 1)$ without bounding activations such as sigmoid, tanh, or ReLU) so that out-of-distribution price levels can be predicted.
3. **Representative 12-Configuration Matrix**: To prevent combinatorial explosion, the Price Level ablation is restricted to 12 representative configurations: 2 model families ({XGBoost, LSTM}) $\times$ 2 data scenarios ({Univariate, Multivariate}) $\times$ 3 horizons ($h \in \{1, 5, 21\}$). GRU is omitted from the secondary ablation per Section 6.2.
4. **Fair Comparison in USD/bbl**: Predictions must be mapped back to physical USD/barrel before computing evaluation metrics (MAE, MSE, RMSE, MAPE, $R^2$, DA), evaluated on the exact same Point-in-Time sample origins as the Relative Change models.

## Decision

1. **Scaler Architecture (`PriceLevelScaler`)**:
   - A dedicated `PriceLevelScaler` is implemented in `src/data/scaling.py`.
   - Normalization applies standard z-score scaling:
     $$\tilde{x} = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}, \qquad \tilde{y} = \frac{y - \mu_{y,\text{train}}}{\sigma_{y,\text{train}}}$$
   - Scaling parameters $(\mu_{\text{train}}, \sigma_{\text{train}})$ are computed exclusively from the Train partition. If a standard deviation is zero or near-zero ($< 10^{-12}$), it is safely defaulted to $1.0$.
   - The transformation is strictly unbounded: no clipping is applied on transformed or inverse-transformed arrays.
   - Inverse transformation restores predictions to physical USD/barrel:
     $$\hat{P} = \hat{\tilde{y}} \cdot \sigma_{y,\text{train}} + \mu_{y,\text{train}}$$
2. **Feature Set for Tabular Price Level Forecasting**:
   - In `src/features/engineering.py`, when `target_representation == "price_level"`, the 30 lag features are the actual historical price levels $P_{o-k}$ for $k = 0 \dots 29$ (rather than relative deviations), combined with momentum returns $R_1 = (P_o - P_{o-1})/P_{o-1}$ and $R_5 = (P_o - P_{o-5})/P_{o-5}$.
   - For XGBoost under Price Level, tabular features and targets are scaled using the Train-only scaler, and predictions are mapped back via inverse transformation.
3. **Neural Architecture Head**:
   - `LSTMNet` maintains an unconstrained `nn.Linear(hidden_dim, 1)` head with no activation function, allowing predictions to extrapolate freely across the real line.
4. **Execution Protocol & Leaderboard Integration**:
   - `run_benchmark.py` and `experiments/benchmark.py` support running the 12 Price Level ablation configurations alongside the 21 Relative Change configurations, completing the full 33-configuration MVP benchmark leaderboard.
   - Predictions are exported into `outputs/predictions/predictions_h{1,5,21}.csv` with `target_representation = "price_level"`.
   - Checkpoints are saved as `outputs/checkpoints/lstm_{scenario}_price_level_h{horizon}.pt`.
5. **RQ1 Synthesis Document**:
   - An empirical analysis comparing Relative Change vs. Price Level across MAE, RMSE, $R^2$, and Directional Accuracy is documented in `docs/experiments/rq1_target_representation_analysis.md`.

## Consequences

- Zero data leakage from Validation or Test sets into feature/target scaling parameters.
- Out-of-distribution test prices (e.g. Test price swings outside the Train range) are preserved without distortion.
- The 33-row benchmark leaderboard fully answers RQ1, RQ2, and RQ3 within a unified, reproducible framework.
