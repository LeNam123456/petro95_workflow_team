"""Validation and backtesting suite for SPAFS V5.2.

Provides:
- run_walk_forward_evaluation: Sequential expanding window out-of-sample simulation.
- WalkForwardResult: Container holding OOS predictions and metadata.
"""

from .walk_forward import WalkForwardResult, run_walk_forward_evaluation

__all__ = ["WalkForwardResult", "run_walk_forward_evaluation"]
