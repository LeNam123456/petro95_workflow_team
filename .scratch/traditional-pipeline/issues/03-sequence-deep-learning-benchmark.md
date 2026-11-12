# 03: Sequence Deep Learning Benchmark (LSTM & GRU for Relative Change)

**What to build:** Deep learning recurrent sequence pipeline for Relative Change forecasting across horizons h in {1, 5, 21} using LSTM and GRU architectures. Builds 3D sequence tensors (30x1 for Univariate, 30x2 for Multivariate) with Local Window Normalization, implements PyTorch training workflows with Early Stopping (patience = 15 on Validation loss) and checkpoint saving, enforces deterministic seed control (seed = 42) with optional multi-seed support via CLI, and evaluates all 12 recurrent configurations on the Test partition.

**Blocked by:** 01: Naive Persistence Baseline & Walking Skeleton Pipeline

**Status:** closed

- [x] Sequence datasets produce 3D tensors (batch_size, 30, 1) for Univariate and (batch_size, 30, 2) for Multivariate with Local Window Normalization `z(j,o,k) = P(j,o-k)/P(j,o) - 1`.
- [x] LSTM and GRU neural architectures are implemented with configurable hidden dimensions and recurrent layers.
- [x] Training loop implements Early Stopping with patience = 15 monitoring Validation loss and saves the best model checkpoint to the checkpoints directory.
- [x] Deterministic seed management guarantees identical outputs with canonical seed 42 across PyTorch, NumPy, and Python.
- [x] All 12 recurrent configurations (2 models x 2 scenarios x 3 horizons) are trained independently under the Direct Multi-Horizon Strategy.
- [x] Test predictions are reconstructed to USD/barrel and evaluated on the same 6 metrics and Directional Accuracy.
- [x] Benchmark leaderboard reaches 21 configurations (3 Naive + 6 XGBoost + 12 Recurrent) and training/validation loss curves are logged.
- [x] Tests verify sequence tensor shapes, absence of NaN/infinite losses, and deterministic repeatability.
