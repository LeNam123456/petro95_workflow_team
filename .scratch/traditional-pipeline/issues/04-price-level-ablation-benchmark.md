# 04: Price Level Ablation Benchmark ({XGBoost, LSTM} x {Uni, Multi} x {1, 5, 21})

**What to build:** Secondary ablation study for direct Price Level forecasting (`y = P(o+h)`) to empirically answer Research Question 1 (RQ1) against Relative Change. Implements a Train-only normalization policy where scalers are fitted exclusively on Train data and applied without clipping to Validation and Test, configures linear output layers on neural models to accommodate out-of-distribution values, trains 12 representative configurations (XGBoost and LSTM across 2 scenarios and 3 horizons), evaluates them in USD/barrel, and populates the full 33-row benchmark leaderboard.

**Blocked by:** 02: XGBoost Relative Change Benchmark (Tabular ML Slice), 03: Sequence Deep Learning Benchmark (LSTM & GRU for Relative Change)

**Status:** ready-for-agent

- [ ] Price Level target and feature scalers are fitted exclusively on the Train partition; Test and Validation data are strictly transformed without updating scaler statistics.
- [ ] Validation and Test values are never clipped to the Train range; neural models utilize linear output layers.
- [ ] 12 ablation models (2 model families x 2 scenarios x 3 horizons) are trained independently under the Direct Multi-Horizon strategy.
- [ ] Model predictions are mapped back to nominal USD/barrel and evaluated against the identical Test samples as Relative Change.
- [ ] Benchmark leaderboard is completed with all 33 MVP configurations (21 Relative Change + 12 Price Level).
- [ ] Empirical comparison between Relative Change and Price Level is documented to answer RQ1.
- [ ] Integration tests verify that modifying Test partition data does not alter Train-fitted scalers and that out-of-range outputs are produced without truncation.
