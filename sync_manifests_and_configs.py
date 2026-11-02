# -*- coding: utf-8 -*-
"""Synchronize all manifest, configuration, and audit JSON files with SPAFS V5.2 final state."""

import json
from pathlib import Path

# 1. Update 04_train_test_config.json
config_data = {
    "system_version": "SPAFS V5.2 Production & Temporal Governance",
    "status": "FROZEN_FINAL",
    "temporal_cutoffs": {
        "platts_singapore_moc": "16:30:00 SGT (UTC+8)",
        "ice_brent_london_close": "03:30:00 SGT (next day, UTC+8)",
        "point_in_time_freeze": "08:30:00 SGT (forecast origin t_origin)",
        "safety_buffer_hours": 5.0,
        "lead_time_to_target_hours": 8.0,
        "timestamp_type": "Rule-Based Market Convention Proxy (No claim of raw tick-level server logs)"
    },
    "stream1_econometric_config": {
        "sample_range": "2008-05-06 -> 2025-12-29",
        "effective_sample_n": 4425,
        "in_sample_warmup_tau_0": 3500,
        "in_sample_warmup_dates": "2008-05-06 -> 2022-04-21",
        "out_of_sample_n": 925,
        "out_of_sample_dates": "2022-04-22 -> 2025-12-29",
        "hac_covariance_maxlags": 5,
        "refit_cadence_days": 1,
        "models": ["M0a", "M0b", "M1", "M2", "M3"]
    },
    "stream2_machine_learning_config": {
        "sample_range": "2017-01-03 -> 2025-12-29",
        "effective_sample_n": 2254,
        "initial_window_tau_0": 1500,
        "in_sample_warmup_dates": "2017-01-03 -> 2022-12-27",
        "refit_cadence_days": 20,
        "out_of_sample_n": 754,
        "out_of_sample_dates": "2022-12-28 -> 2025-12-29",
        "ensemble_seeds": [42, 101, 202, 303, 404, 505, 606, 707, 808, 909],
        "lightgbm_hyperparameters": {
            "objective": "regression",
            "metric": "rmse",
            "learning_rate": 0.03,
            "num_leaves": 15,
            "min_child_samples": 20,
            "n_estimators": 100,
            "subsample": 0.8,
            "subsample_freq": 1,
            "colsample_bytree": 0.8
        },
        "models": ["M4", "M5"]
    },
    "common_cross_stream_comparison": {
        "sample_dates": "2022-12-28 -> 2025-12-29",
        "sample_size": 754,
        "models_evaluated": ["M0a", "M0b", "M1", "M2", "M3", "M4", "M5"]
    },
    "feature_spaces": {
        "M0a": [],
        "M0b": ["mg95_return_pct (sign)"],
        "M1": ["mg95_return_pct"],
        "M2": [
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "spread_mg95_brent_lag1"
        ],
        "M3": [
            "mg95_return_pct",
            "mg95_return_lag1",
            "brent_return_pos",
            "brent_return_neg",
            "brent_return_pos_lag1",
            "brent_return_neg_lag1",
            "spread_mg95_brent_lag1"
        ],
        "M4": [
            "mg95_return_pct",
            "mg95_return_lag1",
            "mg95_return_lag2",
            "mg95_return_lag3",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "brent_return_lag2",
            "brent_return_lag3",
            "vol_mg95_30d",
            "economic_shock_flag"
        ],
        "M5": [
            "mg95_return_pct",
            "mg95_return_lag1",
            "mg95_return_lag2",
            "mg95_return_lag3",
            "brent_return_pct_aligned",
            "brent_return_lag1",
            "brent_return_lag2",
            "brent_return_lag3",
            "vol_mg95_30d",
            "economic_shock_flag",
            "spread_mg95_brent",
            "spread_mg95_brent_lag1",
            "spread_mg95_mg92",
            "spread_mg95_do005",
            "octane_spread_nonpositive_flag"
        ]
    }
}

for p in [
    Path("SPAFS_DELIVERABLES_PACKAGE/05_configuration_and_audit_logs/04_train_test_config.json"),
    Path("SPAFS_DELIVERABLES_PACKAGE/04_train_test_config.json"),
]:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

print("Synchronized 04_train_test_config.json")

# 2. Update pipeline_manifest.json
manifest_data = {
    "pipeline": "SPAFS_V5.2",
    "status": "PASSED_FINAL_AUDITED",
    "governance_rule": "Strict Point-in-Time 08:30 SGT Cutoff with Market Proxy Timestamps",
    "config": {
        "root": "D:\\Petro_95",
        "platts_csv": "data/raw/price_petroleum_platts.csv",
        "brent_csv": "data/raw/brent_crude_daily.csv",
        "interim_dir": "data/interim",
        "processed_dir": "data/processed",
        "report_dir": "reports/data_quality",
        "min_date": "2008-01-01",
        "max_date": "2025-12-31",
        "nlp_start_date": "2017-01-01",
        "stream1_warmup_end_date": "2022-04-21",
        "stream1_oos_start_date": "2022-04-22",
        "stream1_oos_end_date": "2025-12-29",
        "stream2_warmup_end_date": "2022-12-27",
        "stream2_oos_start_date": "2022-12-28",
        "stream2_oos_end_date": "2025-12-29",
        "platts_moc_time_sgt": "16:30",
        "forecast_cutoff_time_sgt": "08:30",
        "brent_settlement_available_time_sgt": "03:30",
        "volatility_window": 30,
        "max_return_lag": 3,
        "outlier_abs_return_pct": 20.0,
        "walk_forward_evaluation": True,
        "stream2_refit_frequency": 20,
        "models_active": ["M0a", "M0b", "M1", "M2", "M3", "M4", "M5"]
    },
    "row_counts": {
        "stream1_raw": 4428,
        "stream1_effective_n": 4425,
        "stream1_warmup": 3500,
        "stream1_oos": 925,
        "stream2_raw": 2255,
        "stream2_effective_n": 2254,
        "stream2_warmup": 1500,
        "stream2_oos": 754,
        "common_cross_stream_oos": 754
    },
    "audits": {
        "zero_lookahead_verified_on_proxies": True,
        "proxy_timestamps_count": 2255,
        "realtime_feed_arrival_ticks": 0,
        "temporal_rules_violations": 0
    }
}

for p in [
    Path("SPAFS_DELIVERABLES_PACKAGE/05_configuration_and_audit_logs/pipeline_manifest.json"),
    Path("reports/data_quality/pipeline_manifest.json"),
]:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

print("Synchronized pipeline_manifest.json")

# 3. Update partition_audit.json
partition_data = {
    "system_name": "SPAFS V5.2 Partition & Sample Split Audit",
    "stream1": {
        "raw_rows": 4428,
        "date_range": "2008-05-02 -> 2025-12-30",
        "effective_sample_n": 4425,
        "warmup_rows": 3500,
        "warmup_date_range": "2008-05-06 -> 2022-04-21",
        "oos_rows": 925,
        "oos_date_range": "2022-04-22 -> 2025-12-29"
    },
    "stream2": {
        "raw_rows": 2255,
        "date_range": "2017-01-03 -> 2025-12-30",
        "effective_sample_n": 2254,
        "warmup_rows": 1500,
        "warmup_date_range": "2017-01-03 -> 2022-12-27",
        "oos_rows": 754,
        "oos_date_range": "2022-12-28 -> 2025-12-29"
    },
    "common_cross_stream_evaluation": {
        "sample_size": 754,
        "date_range": "2022-12-28 -> 2025-12-29",
        "matching_dates_all_models": 754,
        "missing_target_count": 0
    },
    "feature_spaces_count": {
        "M0a": 0,
        "M0b": 1,
        "M1": 1,
        "M2": 5,
        "M3": 7,
        "M4": 10,
        "M5": 15
    }
}

for p in [
    Path("SPAFS_DELIVERABLES_PACKAGE/05_configuration_and_audit_logs/partition_audit.json"),
    Path("reports/data_quality/partition_audit.json"),
]:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(partition_data, f, indent=2)

print("Synchronized partition_audit.json")
