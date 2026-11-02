# -*- coding: utf-8 -*-
"""
Organize the 5 requested components of SPAFS V5.2 into structured subfolders.
"""

import os
import sys
import shutil
import json
import pandas as pd
import nbformat as nbf

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = r"D:\Petro_95"
DELIV_DIR = os.path.join(ROOT_DIR, "SPAFS_DELIVERABLES_PACKAGE")
DOWNLOADS_DIR = r"C:\Users\LeeNam\Downloads\SPAFS_DELIVERABLES_PACKAGE"

os.makedirs(DELIV_DIR, exist_ok=True)

# 5 subfolders
subfolders = [
    "01_parquet_datasets",
    "02_data_creation_scripts",
    "03_m3_econometric_script",
    "04_m4_m5_machine_learning_scripts",
    "05_configuration_and_audit_logs"
]

for sf in subfolders:
    os.makedirs(os.path.join(DELIV_DIR, sf), exist_ok=True)

print("Created 5 structured subfolders.")

# ==============================================================================
# 1. PARQUET DATASETS
# ==============================================================================
print("Populating 01_parquet_datasets...")
p1_src = os.path.join(ROOT_DIR, "data/processed/stream1_econometric_2008_2025.parquet")
p2_src = os.path.join(ROOT_DIR, "data/processed/stream2_aligned_nlp_2017_2025.parquet")

shutil.copy2(p1_src, os.path.join(DELIV_DIR, "01_parquet_datasets", "stream1_econometric_2008_2025.parquet"))
shutil.copy2(p2_src, os.path.join(DELIV_DIR, "01_parquet_datasets", "stream2_aligned_nlp_2017_2025.parquet"))


# ==============================================================================
# 2. DATA CREATION SCRIPTS & NOTEBOOK
# ==============================================================================
print("Populating 02_data_creation_scripts...")
dp_dir = os.path.join(DELIV_DIR, "02_data_creation_scripts")
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/data_handling/market_features.py"), os.path.join(dp_dir, "market_features.py"))
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/data_handling/target.py"), os.path.join(dp_dir, "target.py"))
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/data_handling/alignment.py"), os.path.join(dp_dir, "alignment.py"))
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/data_handling/patrition.py"), os.path.join(dp_dir, "patrition.py"))
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/pipeline.py"), os.path.join(dp_dir, "master_pipeline_orchestrator.py"))

# Create dedicated data creation and feature engineering notebook
nb_data = nbf.v4.new_notebook()
nb_data.cells = [
    nbf.v4.new_markdown_cell("""# SPAFS V5.2: Pipeline Tạo Dữ Liệu và Kỹ Nghệ Đặc Trưng (Feature Engineering)
## Quy trình tạo mg95_return_pct, target_return_pct, Lags, Rolling Volatility và Biến Kinh Tế Lọc Dầu
**Tác giả:** Lê Nam (LeNam123456)  
**Repository:** [petro95_workflow_team](https://github.com/LeNam123456/petro95_workflow_team.git)
"""),
    nbf.v4.new_code_cell("""import pandas as pd
import numpy as np

# 1. Load canonical market panel (Đã đồng bộ Point-in-Time 08:30 SGT)
df = pd.read_parquet("../../data/interim/canonical_market_panel.parquet")
df['market_date'] = pd.to_datetime(df['market_date'])
df = df.sort_values('market_date').reset_index(drop=True)
print(f"Số dòng bảng chuẩn: {len(df)} ngày ({df['market_date'].min().date()} đến {df['market_date'].max().date()})")
df[['market_date', 'MG95', 'MG92', 'DO_005', 'brent_close']].head()
"""),
    nbf.v4.new_markdown_cell("""### 2. Tạo Biến Tỷ Suất Sinh Lợi Nội Sinh & Biến Mục Tiêu Dự Báo
- **Lợi suất hôm nay (Predictor):** $r_{MG95, t} = \ln(P_t / P_{t-1}) \times 100\%$
- **Biến mục tiêu ngày tiếp theo (Primary Target):** $r_{MG95, t+1} = \ln(P_{t+1} / P_t) \times 100\%$
- **Biến phân loại hướng nhị phân (Secondary Target):** $y_{t+1} = \mathbb{I}[r_{MG95, t+1} > 0] \in \{0, 1\}$
"""),
    nbf.v4.new_code_cell("""# Tính log return hiện tại
df['mg95_return_pct'] = np.log(df['MG95'] / df['MG95'].shift(1)) * 100.0

# Tính target 1-bước-tới (forward-looking target)
df['target_return_pct'] = np.log(df['MG95'].shift(-1) / df['MG95']) * 100.0
df['target_direction'] = (df['target_return_pct'] > 0).astype(int)

print("Mẫu dữ liệu sau khi tạo target:")
df[['market_date', 'MG95', 'mg95_return_pct', 'target_return_pct', 'target_direction']].head()
"""),
    nbf.v4.new_markdown_cell("""### 3. Kỹ Nghệ Đặc Trưng Động Lượng Trễ (Lag Features)
Tạo các bậc trễ từ lag 1 đến lag 3 của tỷ suất sinh lợi Mogas 95 và dầu thô Brent:
"""),
    nbf.v4.new_code_cell("""for lag in [1, 2, 3]:
    df[f'mg95_return_lag{lag}'] = df['mg95_return_pct'].shift(lag)
    df[f'brent_return_lag{lag}'] = df['brent_return_pct_aligned'].shift(lag)

print("Các cột trễ động lượng đã sinh:")
print([c for c in df.columns if 'lag' in c])
"""),
    nbf.v4.new_markdown_cell("""### 4. Kỹ Nghệ Đặc Trưng Kinh Tế Học Lọc Dầu (Downstream Refining Spreads)
1. **Gasoline Crack Spread:** $Spread_{MG95-Brent, t} = P_{MG95, t} - P_{Brent, t}$
2. **Mỏ neo cân bằng trễ:** $Spread_{MG95-Brent, t-1}$ (Lagged Crack Margin)
3. **Phí chất lượng Octane:** $Spread_{MG95-MG92, t} = P_{MG95, t} - P_{MG92, t}$
4. **Biên thay thế Xăng - Diesel:** $Spread_{MG95-DO, t} = P_{MG95, t} - P_{DO005, t}$
"""),
    nbf.v4.new_code_cell("""df['spread_mg95_brent'] = df['MG95'] - df['brent_close']
df['spread_mg95_brent_lag1'] = df['spread_mg95_brent'].shift(1)
df['spread_mg95_mg92'] = df['MG95'] - df['MG92']
df['spread_mg95_do005'] = df['MG95'] - df['DO_005']
df['octane_spread_nonpositive_flag'] = (df['spread_mg95_mg92'] <= 0).astype(int)

df[['market_date', 'spread_mg95_brent', 'spread_mg95_brent_lag1', 'spread_mg95_mg92', 'spread_mg95_do005']].head()
"""),
    nbf.v4.new_markdown_cell("""### 5. Độ Biến Động Lịch Sử 30 Ngày & Phân Tách Cú Sốc Brent Bất Đối Xứng
- **Độ biến động quá khứ 30 ngày (Trailing Volatility):** $\text{VOL\_30D}_t = \text{std}(r_{MG95}, \text{window}=30)$
- **Phân tách cú sốc dầu Brent:** $r_{Brent, t}^+ = \max(r_{Brent}, 0)$, $r_{Brent, t}^- = \min(r_{Brent}, 0)$
"""),
    nbf.v4.new_code_cell("""# Rolling Volatility 30 phiên
df['vol_mg95_30d'] = df['mg95_return_pct'].rolling(window=30, min_periods=30).std()

# Asymmetric Brent Shocks
df['brent_return_pos'] = np.maximum(df['brent_return_pct_aligned'], 0.0)
df['brent_return_neg'] = np.minimum(df['brent_return_pct_aligned'], 0.0)
df['brent_return_pos_lag1'] = df['brent_return_pos'].shift(1)
df['brent_return_neg_lag1'] = df['brent_return_neg'].shift(1)

print("Đặc trưng hoàn tất. Kích thước DataFrame:", df.shape)
""")
]

with open(os.path.join(dp_dir, "data_creation_and_feature_engineering.ipynb"), "w", encoding="utf-8") as f:
    nbf.write(nb_data, f)


# ==============================================================================
# 3. M3 ECONOMETRIC SCRIPTS
# ==============================================================================
print("Populating 03_m3_econometric_script...")
m3_dir = os.path.join(DELIV_DIR, "03_m3_econometric_script")
shutil.copy2(os.path.join(DELIV_DIR, "01_run_m3_asymmetric_adl_and_wald_test.py"), os.path.join(m3_dir, "01_run_m3_asymmetric_adl_and_wald_test.py"))
shutil.copy2(os.path.join(DELIV_DIR, "01_M3_Asymmetric_ADL_and_Wald_Test.ipynb"), os.path.join(m3_dir, "01_M3_Asymmetric_ADL_and_Wald_Test.ipynb"))
shutil.copy2(os.path.join(DELIV_DIR, "rq1_wald_tests_output.json"), os.path.join(m3_dir, "rq1_wald_tests_output.json"))


# ==============================================================================
# 4. M4/M5 MACHINE LEARNING SCRIPTS & PREDICTIONS
# ==============================================================================
print("Populating 04_m4_m5_machine_learning_scripts...")
ml_dir = os.path.join(DELIV_DIR, "04_m4_m5_machine_learning_scripts")
shutil.copy2(os.path.join(DELIV_DIR, "02_train_predict_evaluate_m4_m5.py"), os.path.join(ml_dir, "02_train_predict_evaluate_m4_m5.py"))
shutil.copy2(os.path.join(ROOT_DIR, "src/models/ml/lgbm.py"), os.path.join(ml_dir, "lgbm.py"))
shutil.copy2(os.path.join(ROOT_DIR, "artifacts/metrics/stream2_ml_leaderboard.json"), os.path.join(ml_dir, "stream2_ml_leaderboard.json"))
shutil.copy2(os.path.join(ROOT_DIR, "artifacts/metrics/stream2_pairwise_tests.json"), os.path.join(ml_dir, "stream2_pairwise_tests.json"))
shutil.copy2(os.path.join(DELIV_DIR, "03_out_of_sample_predictions_and_targets.csv"), os.path.join(ml_dir, "out_of_sample_predictions_and_targets.csv"))
shutil.copy2(os.path.join(DELIV_DIR, "03_out_of_sample_predictions_and_targets.parquet"), os.path.join(ml_dir, "out_of_sample_predictions_and_targets.parquet"))


# ==============================================================================
# 5. CONFIGURATION AND AUDIT LOGS
# ==============================================================================
print("Populating 05_configuration_and_audit_logs...")
cfg_dir = os.path.join(DELIV_DIR, "05_configuration_and_audit_logs")
shutil.copy2(os.path.join(ROOT_DIR, "src/data_proccessing/config.py"), os.path.join(cfg_dir, "config.py"))
shutil.copy2(os.path.join(DELIV_DIR, "04_train_test_config.json"), os.path.join(cfg_dir, "04_train_test_config.json"))
shutil.copy2(os.path.join(DELIV_DIR, "04_data_quality_pit_audit_and_config.md"), os.path.join(cfg_dir, "04_data_quality_pit_audit_and_config.md"))
shutil.copy2(os.path.join(ROOT_DIR, "reports/data_quality/canonical_panel_audit.json"), os.path.join(cfg_dir, "canonical_panel_audit.json"))
shutil.copy2(os.path.join(ROOT_DIR, "reports/data_quality/partition_audit.json"), os.path.join(cfg_dir, "partition_audit.json"))
shutil.copy2(os.path.join(ROOT_DIR, "reports/data_quality/pipeline_manifest.json"), os.path.join(cfg_dir, "pipeline_manifest.json"))
shutil.copy2(os.path.join(ROOT_DIR, "artifacts/manifests/stream1_econometric_execution_manifest.json"), os.path.join(cfg_dir, "stream1_econometric_execution_manifest.json"))
shutil.copy2(os.path.join(ROOT_DIR, "artifacts/manifests/stream2_ml_m4_execution_manifest.json"), os.path.join(cfg_dir, "stream2_ml_m4_execution_manifest.json"))
shutil.copy2(os.path.join(ROOT_DIR, "artifacts/manifests/stream2_ml_m5_execution_manifest.json"), os.path.join(cfg_dir, "stream2_ml_m5_execution_manifest.json"))


# ==============================================================================
# MIRROR TO DOWNLOADS FOLDER & CREATE ARCHIVE
# ==============================================================================
print(f"Syncing all files to {DOWNLOADS_DIR}...")
if os.path.exists(DOWNLOADS_DIR):
    shutil.rmtree(DOWNLOADS_DIR)
shutil.copytree(DELIV_DIR, DOWNLOADS_DIR)

print("Creating ZIP archives...")
shutil.make_archive(DELIV_DIR, 'zip', DELIV_DIR)
shutil.make_archive(DOWNLOADS_DIR, 'zip', DOWNLOADS_DIR)

print("\nSuccessfully organized all 5 deliverable packages!")
