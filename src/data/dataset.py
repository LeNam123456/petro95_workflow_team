"""Supervised sample builder and sliding window generator (Seam B).

Enforces:
1. Context borrowing: up to L-1 observations borrowed from immediately prior partition.
2. Boundary truncation: samples whose target extends past partition boundary are dropped.
3. Target representation:
   - Relative change: R_{o,h} = (P_{o+h} - P_o) / P_o, local normalization z^{(j)}_{o,k} = P_{o-k}/P_o - 1.
   - Price level: y_{o,h} = P_{o+h}.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SupervisedBatch:
    """A batch of supervised samples with lookback windows, targets, and Point-in-Time metadata."""

    features: np.ndarray  # shape: (N, lookback, n_features)
    targets: np.ndarray  # shape: (N,)
    origin_prices: np.ndarray  # shape: (N,) - P_o in USD/bbl
    actual_prices: np.ndarray  # shape: (N,) - P_{o+h} in USD/bbl
    forecast_origins: list[Any]  # list of Timestamps
    target_timestamps: list[Any]  # list of Timestamps
    feature_available_ats: list[Any]  # list of Timestamps
    horizon: int
    scenario: str
    target_representation: str

    def __len__(self) -> int:
        return len(self.targets)


def build_supervised_samples(
    partition_df: pd.DataFrame,
    prior_df: pd.DataFrame | None = None,
    lookback: int = 30,
    horizon: int = 1,
    scenario: str = "univariate",
    target_representation: str = "relative_change",
    target_col: str = "MG95",
    brent_col: str = "brent_close",
    origin_col: str = "forecast_origin_datetime",
    avail_col: str = "availability_datetime",
    obs_col: str = "observation_datetime",
) -> SupervisedBatch:
    """Build supervised sliding window samples across partition boundaries.

    Parameters:
    - partition_df: The active partition (Train, Validation, or Test).
    - prior_df: Preceding partition to borrow context history from.
    - lookback: Number of past sessions (L = 30).
    - horizon: Forecast step (h in {1, 5, 21}).
    - scenario: 'univariate' (MG95 only) or 'multivariate' (MG95 + brent_close).
    - target_representation: 'relative_change' or 'price_level'.
    """
    if scenario == "univariate":
        feature_cols = [target_col]
    elif scenario == "multivariate":
        feature_cols = [target_col, brent_col]
    else:
        raise ValueError(f"Unknown scenario '{scenario}'. Must be 'univariate' or 'multivariate'.")

    # Combine prior context if available
    if prior_df is not None and len(prior_df) > 0:
        borrow_len = min(lookback - 1, len(prior_df))
        context_rows = prior_df.iloc[-borrow_len:]
        combined_df = pd.concat([context_rows, partition_df], ignore_index=True)
        start_k = borrow_len
    else:
        combined_df = partition_df.reset_index(drop=True)
        start_k = lookback - 1

    # End origin index must ensure target k + horizon is within combined_df
    end_k = len(combined_df) - 1 - horizon

    if end_k < start_k:
        # No samples possible
        empty_feat = np.empty((0, lookback, len(feature_cols)), dtype=np.float64)
        empty_arr = np.empty((0,), dtype=np.float64)
        return SupervisedBatch(
            features=empty_feat,
            targets=empty_arr,
            origin_prices=empty_arr,
            actual_prices=empty_arr,
            forecast_origins=[],
            target_timestamps=[],
            feature_available_ats=[],
            horizon=horizon,
            scenario=scenario,
            target_representation=target_representation,
        )

    num_samples = end_k - start_k + 1
    features_arr = np.zeros((num_samples, lookback, len(feature_cols)), dtype=np.float64)
    targets_arr = np.zeros(num_samples, dtype=np.float64)
    origin_prices_arr = np.zeros(num_samples, dtype=np.float64)
    actual_prices_arr = np.zeros(num_samples, dtype=np.float64)
    forecast_origins: list[Any] = []
    target_timestamps: list[Any] = []
    feature_available_ats: list[Any] = []

    # Extract numpy blocks for speed
    feat_matrix = combined_df[feature_cols].to_numpy(dtype=np.float64)
    target_series = combined_df[target_col].to_numpy(dtype=np.float64)
    origins_raw = combined_df[origin_col].to_list() if origin_col in combined_df.columns else [None] * len(combined_df)
    obs_raw = combined_df[obs_col].to_list() if obs_col in combined_df.columns else [None] * len(combined_df)
    avail_raw = combined_df[avail_col].to_list() if avail_col in combined_df.columns else [None] * len(combined_df)

    for i, k in enumerate(range(start_k, end_k + 1)):
        window = feat_matrix[k - lookback + 1 : k + 1]  # shape: (lookback, n_features)
        p_origin = target_series[k]
        p_target = target_series[k + horizon]

        origin_prices_arr[i] = p_origin
        actual_prices_arr[i] = p_target
        forecast_origins.append(origins_raw[k])
        target_timestamps.append(obs_raw[k + horizon])
        feature_available_ats.append(avail_raw[k])

        if target_representation == "relative_change":
            # R_{o,h} = (P_{o+h} - P_o) / P_o
            targets_arr[i] = (p_target - p_origin) / p_origin
            # Normalize each feature by its origin value at index -1
            # z^{(j)}_{o,k} = P^{(j)}_{o-k} / P^{(j)}_o - 1
            origin_feats = window[-1, :]
            # Avoid division by zero
            safe_denom = np.where(origin_feats != 0, origin_feats, 1.0)
            norm_window = (window / safe_denom) - 1.0
            features_arr[i] = norm_window
        elif target_representation == "price_level":
            targets_arr[i] = p_target
            features_arr[i] = window
        else:
            raise ValueError(
                f"Unknown target_representation '{target_representation}'. "
                "Must be 'relative_change' or 'price_level'."
            )

    return SupervisedBatch(
        features=features_arr,
        targets=targets_arr,
        origin_prices=origin_prices_arr,
        actual_prices=actual_prices_arr,
        forecast_origins=forecast_origins,
        target_timestamps=target_timestamps,
        feature_available_ats=feature_available_ats,
        horizon=horizon,
        scenario=scenario,
        target_representation=target_representation,
    )
