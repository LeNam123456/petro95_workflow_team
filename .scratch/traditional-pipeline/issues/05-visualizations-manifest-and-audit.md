# 05: Visualization Suite, Experiment Manifest & End-to-End Benchmark Audit

**What to build:** Visual reporting suite, reproducible experiment manifest packaging, and comprehensive end-to-end benchmark audit. Generates publication-ready figures for actual versus predicted prices across all horizons, directional confusion matrices (Actual Up/Down x Predicted Up/Down), and training/validation loss curves. Assembles the final experiment manifest containing dataset checksums, proxy flag audit counts, PIT verification status, model hyperparameters, library versions, and execution runtimes. Validates the end-to-end execution of the complete pipeline CLI.

**Blocked by:** 04: Price Level Ablation Benchmark ({XGBoost, LSTM} x {Uni, Multi} x {1, 5, 21})

**Status:** ready-for-agent

- [ ] Actual vs. predicted comparison plots are generated and saved for h = 1, h = 5, and h = 21.
- [ ] Directional confusion matrix visualization (Actual Up/Down vs. Predicted Up/Down) is generated.
- [ ] Training and validation loss curves across epochs are plotted and saved for all deep learning models.
- [ ] Full experiment manifest is generated, documenting data checksums, proxy availability flag statistics, PIT audit verification, canonical seed, hyperparameters, library environment, and execution time per configuration.
- [ ] Master CLI orchestrates all 33 configurations with clean logging and appropriate exit codes.
- [ ] Full test suite (Seam A and Seam B) passes with 100% green status in pytest.
