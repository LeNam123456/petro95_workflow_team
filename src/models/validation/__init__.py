"""Validation suite for SPAFS V5.2: expanding-window walk-forward with purging/embargo."""

from .walk_forward import (
    WalkForwardResult,
    purged_train_end,
    run_walk_forward_evaluation,
    run_walk_forward_quantiles,
)

__all__ = ["WalkForwardResult", "purged_train_end", "run_walk_forward_evaluation", "run_walk_forward_quantiles"]
