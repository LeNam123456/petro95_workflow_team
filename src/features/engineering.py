"""Feature engineering for tabular gradient boosting models (XGBoost).

Conforms to ADR-0007:
1. Univariate (32 features):
   - 30 locally-normalized relative lags of Mogas (z^{(M)}_{o,k} for k=0..29)
   - 2 momentum returns: R1 = (P^M_o - P^M_{o-1}) / P^M_{o-1}, R5 = (P^M_o - P^M_{o-5}) / P^M_{o-5}
2. Multivariate (64 features):
   - 32 Mogas features
   - 32 corresponding Brent features (z^{(B)}_{o,k} for k=0..29, R1^{(B)}, R5^{(B)})
3. Non-stationary raw price spread (P^M - P^B) is strictly excluded.
"""

from __future__ import annotations

import numpy as np

from src.data.dataset import SupervisedBatch


def get_feature_names(scenario: str = "univariate") -> list[str]:
    """Return canonical feature names for XGBoost tabular features.

    Parameters:
    - scenario: 'univariate' (32 features) or 'multivariate' (64 features).
    """
    names: list[str] = []
    # Mogas 95 features (32)
    names.extend([f"mg95_lag_{k}" for k in range(30)])
    names.extend(["mg95_r1", "mg95_r5"])

    if scenario == "multivariate":
        # Brent features (32)
        names.extend([f"brent_lag_{k}" for k in range(30)])
        names.extend(["brent_r1", "brent_r5"])
    elif scenario != "univariate":
        raise ValueError(f"Unknown scenario '{scenario}'. Must be 'univariate' or 'multivariate'.")

    return names


def extract_xgboost_features(batch: SupervisedBatch) -> tuple[np.ndarray, list[str]]:
    """Transform sliding window SupervisedBatch into 2D tabular features for XGBoost.

    Parameters:
    - batch: SupervisedBatch from Seam B (dataset.py)

    Returns:
    - features: 2D array of shape (N, 32) for univariate or (N, 64) for multivariate.
    - feature_names: list of feature names matching column dimensions.
    """
    n_samples = len(batch)
    scenario = batch.scenario
    feature_names = get_feature_names(scenario=scenario)
    n_feats_total = len(feature_names)

    if n_samples == 0:
        return np.empty((0, n_feats_total), dtype=np.float64), feature_names

    # batch.features shape: (N, lookback, n_channels)
    # where n_channels == 1 (Mogas) or 2 (Mogas, Brent)
    feat_window = batch.features
    lookback = feat_window.shape[1]

    if lookback < 30:
        raise ValueError(f"Lookback window must be at least 30 sessions, got {lookback}")

    # Determine whether batch.features are already locally-normalized or raw prices
    is_relative = batch.target_representation == "relative_change"

    cols_list: list[np.ndarray] = []

    # Process each channel (channel 0: Mogas, channel 1: Brent if multivariate)
    n_channels = 2 if scenario == "multivariate" else 1

    for ch in range(n_channels):
        ch_window = feat_window[:, :, ch]  # shape: (N, lookback)

        if is_relative:
            # When target_representation is relative_change:
            # ch_window is already z^{(j)}_{o, k} where:
            # ch_window[:, -1 - k] is z_{o, k} = P_{o-k} / P_o - 1
            # For k in 0..29:
            lags = [ch_window[:, -1 - k] for k in range(30)]

            # Momentum returns:
            # z_{o,1} = P_{o-1}/P_o - 1  =>  P_o / P_{o-1} = 1 / (1 + z_{o,1})
            # R1 = (P_o - P_{o-1}) / P_{o-1} = 1 / (1 + z_{o,1}) - 1
            z1 = ch_window[:, -2]  # k = 1
            z5 = ch_window[:, -6]  # k = 5

            denom1 = np.where(1.0 + z1 != 0, 1.0 + z1, 1.0)
            denom5 = np.where(1.0 + z5 != 0, 1.0 + z5, 1.0)

            r1 = (1.0 / denom1) - 1.0
            r5 = (1.0 / denom5) - 1.0

        else:
            # When target_representation is price_level:
            # ch_window contains raw price levels P_{o-k}
            p_origin = ch_window[:, -1]
            safe_p_origin = np.where(p_origin != 0, p_origin, 1.0)

            # z_{o,k} = P_{o-k} / P_o - 1
            lags = [(ch_window[:, -1 - k] / safe_p_origin) - 1.0 for k in range(30)]

            p_lag1 = ch_window[:, -2]
            p_lag5 = ch_window[:, -6]
            safe_p_lag1 = np.where(p_lag1 != 0, p_lag1, 1.0)
            safe_p_lag5 = np.where(p_lag5 != 0, p_lag5, 1.0)

            r1 = (p_origin - p_lag1) / safe_p_lag1
            r5 = (p_origin - p_lag5) / safe_p_lag5

        # Stack channel features: 30 lags + R1 + R5 = 32 features
        cols_list.extend(lags)
        cols_list.append(r1)
        cols_list.append(r5)

    features = np.column_stack(cols_list).astype(np.float64)
    return features, feature_names
