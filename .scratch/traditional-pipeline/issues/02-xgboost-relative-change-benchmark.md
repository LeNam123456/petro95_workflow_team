# 02: XGBoost Relative Change Benchmark (Tabular ML Slice)

**What to build:** Tabular feature engineering and direct multi-horizon XGBoost regression for the Relative Change primary target across horizons h in {1, 5, 21}. Constructs mathematically stationary tabular feature vectors from the 30-session window: 32 features for Univariate (30 locally-normalized relative lags and 2 momentum returns) and 64 features for Multivariate (adding 32 corresponding PIT-aligned Brent features), excluding raw price spreads. Trains and evaluates 6 independent XGBoost models, reconstructs prices in USD/barrel, appends results to the benchmark leaderboard (+6 rows, total 9 rows), and exports feature importance rankings.

**Blocked by:** 01: Naive Persistence Baseline & Walking Skeleton Pipeline

**Status:** closed

- [x] Feature engineering creates exact 32-feature Univariate vectors and 64-feature Multivariate vectors from locally normalized relative lags and momentum returns.
- [x] Raw price difference between Mogas and Brent is completely excluded from the feature set.
- [x] Direct Multi-Horizon strategy trains 6 independent XGBoost models (3 horizons x 2 scenarios) on Relative Change targets.
- [x] Hyperparameter tuning and model selection rely solely on Train and Validation partitions without lookahead into Test.
- [x] Predictions on Test partition are reconstructed to USD/barrel and evaluated with the 6 standard metrics and 3-state Directional Accuracy.
- [x] Benchmark leaderboard is updated to include the 6 XGBoost configurations alongside the Naive baseline (9 rows total).
- [x] XGBoost feature importance metrics are exported for analysis of lag and Brent contribution.
- [x] Integration tests verify deterministic execution and feature shape consistency.
