"""Price reconstruction utilities.

Restores target representation to physical price levels in USD/barrel:
- Relative change: P_hat_{o+h} = P_o * (1 + R_hat_{o,h})
- Price level: P_hat_{o+h} = y_hat_{o,h}
"""

from __future__ import annotations

import numpy as np


def reconstruct_price(
    origin_price: np.ndarray | float,
    relative_change: np.ndarray | float,
) -> np.ndarray | float:
    """Reconstruct predicted price level from relative change: P_o * (1 + R_hat)."""
    orig = np.asarray(origin_price, dtype=np.float64)
    rel = np.asarray(relative_change, dtype=np.float64)
    return orig * (1.0 + rel)


def reconstruct_from_price_level(
    predicted_level: np.ndarray | float,
) -> np.ndarray | float:
    """Pass-through reconstruction for direct price level predictions."""
    return np.asarray(predicted_level, dtype=np.float64)
