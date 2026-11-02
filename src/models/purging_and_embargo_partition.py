# -*- coding: utf-8 -*-
"""Pedagogical Demonstration of Purging and Embargo for Multi-Horizon Forecasting (SPAFS V5.2).

Author: SPAFS Research Team
Reference: Marcos Lopez de Prado (2018), 'Advances in Financial Machine Learning'.

Key Concept:
When predicting multi-step ahead overlapping targets:
  r_{t, h} = ln(P_{t+h} / P_t) * 100%  (e.g. h=5 for Weekly, h=21 for Monthly)
If an observation t is in the training set, its actual outcome P_{t+h} is not known until t+h.
At forecast origin tau:
1. Purging: Any training sample t where t + h > tau MUST be removed (i.e. t in [tau - h + 1, tau - 1]).
2. Embargo: Adding a safety gap E sessions before tau (i.e. t in [tau - h - E + 1, tau - h])
   to eliminate residual autoregressive contamination.
Hence, the training set at origin tau is strictly:
  t <= tau - h - Embargo.
"""

from typing import Tuple
import numpy as np
import pandas as pd


def get_purged_embargoed_train_indices(
    total_samples: int,
    forecast_origin: int,
    horizon_steps: int,
    embargo_steps: int
) -> np.ndarray:
    """Return array of valid training indices that strictly prevent lookahead leakage."""
    max_train_idx = forecast_origin - horizon_steps - embargo_steps
    if max_train_idx < 0:
        return np.array([], dtype=int)
    return np.arange(0, max_train_idx + 1)


def audit_leakage_check(train_idx: np.ndarray, forecast_origin: int, horizon_steps: int) -> bool:
    """Verify that no sample in train has its label realization date >= forecast_origin."""
    if len(train_idx) == 0:
        return True
    realization_dates = train_idx + horizon_steps
    violations = np.sum(realization_dates > forecast_origin)
    return violations == 0


if __name__ == "__main__":
    print("=== DEMONSTRATION OF PURGING & EMBARGO IN SPAFS V5.2 ===")
    tau = 1500  # Example forecast origin
    
    for name, h, embargo in [("Daily", 1, 0), ("Weekly", 5, 2), ("Monthly", 21, 5)]:
        tr_idx = get_purged_embargoed_train_indices(2255, tau, h, embargo)
        is_clean = audit_leakage_check(tr_idx, tau, h)
        purged_count = tau - len(tr_idx)
        print(f"Horizon: {name:<7} | h={h:2d} | Embargo={embargo:2d} | Train Size={len(tr_idx):4d} "
              f"| Purged Count={purged_count:2d} | No Leakage: {is_clean}")
