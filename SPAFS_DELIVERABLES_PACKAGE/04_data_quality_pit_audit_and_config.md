# BÁO CÁO KIỂM TOÁN CHẤT LƯỢNG DỮ LIỆU, QUẢN TRỊ POINT-IN-TIME (PIT) VÀ CẤU HÌNH HUẤN LUYỆN / KIỂM ĐỊNH
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)

- **Dự án:** Dự báo Tỷ suất Thay đổi & Hướng Biến động Chuẩn giá Platts FOB Singapore Mogas 95
- **Tác giả:** Lê Nam (LeNam123456)
- **Repository:** https://github.com/LeNam123456/petro95_workflow_team.git
- **Tiêu chuẩn kiểm toán:** Point-in-Time Governance, Data Contract 8 Cổng (Fail-Fast), Expanding Walk-Forward OOS.

---

## 1. BÁO CÁO KIỂM TOÁN HỢP ĐỒNG DỮ LIỆU & QUẢN TRỊ POINT-IN-TIME (DATA CONTRACT AUDIT)

### 1.1. Cổng Gate 1.1: Kiểm toán Dữ liệu Chuẩn Platts FOB Singapore (`validate_plats.py`)
- **Tập tin nguồn:** `data/raw/price_petroleum_platts.csv` (4,559 dòng dữ liệu thô từ 02/05/2008 đến 31/12/2025).
- **Kết quả rà soát cấu trúc lịch giao dịch:**
  - Nhận diện chính xác **129 ngày nghỉ lễ giao dịch có cấu trúc** của thị trường Singapore (Tết Nguyên Đán, Deepavali, Quốc khánh, Giáng sinh).
  - Tách bạch hoàn toàn giữa "ngày nghỉ lễ chính thức" và "ngày mất dữ liệu bất thường".
  - **Số ngày giao dịch hợp lệ:** **4,430 ngày giao dịch**.
- **Chỉ số toàn vẹn:**
  - Số bản ghi giá âm hoặc bằng 0: **0 (Passed)**.
  - Số bản ghi trùng lặp khóa ngày (`market_date`): **0 (Passed)**.
  - Chuỗi ngày không giảm đơn điệu (Strictly Monotonic Ascending): **100% Passed**.
- **Tệp lưu trữ:** `data/interim/platts_validated.parquet` (SHA-256 Verified).

### 1.2. Cổng Gate 1.2: Kiểm toán Dữ liệu Hợp đồng Tương lai Dầu thô Brent (`validate_brent.py`)
- **Tập tin nguồn:** `data/raw/brent_crude_daily.csv` (4,478 dòng dữ liệu thô liên tục `BZ=F`).
- **Nghiệp vụ chuyển tháng (Contract Roll):** Loại bỏ hoàn toàn bước nhảy cơ học do chênh lệch giữa hai hợp đồng kỳ hạn liền kề, bảo đảm tỷ suất sinh lợi trong hợp đồng (*Within-Contract Return*) phản ánh đúng biến động giá thị trường.
- **Bảo tồn cú sốc kinh tế thực:**
  - Áp dụng triết lý *"Outlier Detection != Outlier Removal"*.
  - Toàn bộ các cú sốc lịch sử cực đoan (Khủng hoảng Tài chính 2008, Cú sốc Nga - Saudi Arabia và đại dịch COVID-19 tháng 03–04/2020) được **bảo tồn trọn vẹn 100%**, không bị cắt gọt cơ học bằng Z-score trimming hay Winsorization.
- **Tệp lưu trữ:** `data/interim/brent_continuous.parquet`.

### 1.3. Cổng Gate 1.3: Căn chỉnh Point-in-Time Cutoff & Đồng bộ Đa Thị trường (`alignment.py`)
- **Bản chất bài toán lệch múi giờ (Temporal Geometry):**
  - Platts Singapore chốt phiên định giá Market-on-Close (MOC) lúc **16:30 SGT (UTC+8)**.
  - Sàn ICE Brent London tiếp tục giao dịch suốt đêm tới **02:30–03:30 SGT sáng hôm sau**.
- **Mốc Cutoff đóng băng thông tin cứng:** **$t_{origin} = \text{08:30 SGT sáng ngày } t+1$**.
- **Kết quả kiểm toán Point-in-Time:**
  - Số lượng bản ghi bảng chuẩn (`canonical_panel`): **4,428 ngày giao dịch** (2008-05-02 đến 2025-12-30).
  - Số bản ghi trùng khớp lịch tuyệt đối: 4,262 ngày.
  - Số ngày chuyển tiếp do lệch ngày nghỉ lễ: 166 ngày.
  - **Số bản ghi vi phạm Point-in-Time (PIT Violations):** **0 / 4,428 bản ghi (0.00% - Tuyệt đối không rò rỉ dữ liệu tương lai)**.
- **Tệp lưu trữ:** `data/interim/canonical_market_panel.parquet`.

---

## 2. BÁO CÁO KIỂM TOÁN TÍNH DỪNG & PHÂN MẪU (STATIONARITY & PARTITION AUDIT)

### 2.1. Kiểm toán Tính Dừng Augmented Dickey-Fuller (ADF Test)
Nhằm triệt tiêu rủi ro "Hồi quy giả mạo" (Spurious Regression):
- **Chuỗi Tỷ suất sinh lợi Mogas 95 ($r_{MG95, t}$):** $\text{ADF-stat} = -63.50, p < 10^{-20} \implies$ Dừng chặt $I(0)$.
- **Chuỗi Tỷ suất sinh lợi dầu Brent ($r_{Brent, t}$):** $\text{ADF-stat} = -67.89, p < 10^{-20} \implies$ Dừng chặt $I(0)$.
- **Chuỗi Gasoline Crack Spread ($Spread_{t-1} = P_{MG95, t-1} - P_{Brent, t-1}$):**
  - $\text{ADF-stat} = -6.4541, p\text{-value} = 1.49 \times 10^{-8} < 10^{-7} \implies$ **Dừng chặt $I(0)$**.
  - Xác nhận Crack Spread đóng vai trò là mỏ neo hoàn nguyên cân bằng dài hạn (Mean-Reverting Anchor) mà không làm phát sinh hồi quy giả mạo.

### 2.2. Kiểm toán Khung Thiết Kế Hai Mẫu Độc lập (Two-Sample Framework)
- **Stream 1 (Econometric Stream: 2008 – 2025):**
  - Tổng số dòng: 4,428 quan sát; **4,425 dòng hữu dụng** sau khi tính các bậc trễ động lực học.
  - Cửa sổ In-sample khởi động: 3,500 phiên (2008 – 2021).
  - Cửa sổ Out-of-Sample (OOS): **925 phiên giao dịch** (2022-04-22 đến 2025-12-29).
  - Phục vụ kiểm định truyền dẫn phi đối xứng **RQ1** ($M0a \to M3$).
- **Stream 2 (Machine Learning Stream: 2017 – 2025):**
  - Tổng số dòng: 2,255 quan sát (tránh lỗi thiên lệch "Zero Ambiguity" giai đoạn thiếu tin tức).
  - Cửa sổ khởi tạo huấn luyện ban đầu: $\tau_0 = 1,500$ phiên (2017 đến 2022).
  - Cửa sổ Out-of-Sample (OOS): **754 phiên giao dịch** (2022-12-28 đến 2025-12-29).
  - Chu kỳ tái ước lượng tham số (Refit Frequency): Cố định 20 phiên giao dịch (1 tháng).
  - Phục vụ kiểm định giá trị gia tăng kinh tế lọc dầu **RQ2** ($M4 \to M5$).

---

## 3. BẢNG THÔNG SỐ CẤU HÌNH HUẤN LUYỆN VÀ KIỂM ĐỊNH (TRAIN/TEST CONFIG MATRIX)

Dưới đây là cấu hình tham số chính thức của toàn bộ hệ thống (được xuất đồng bộ trong tệp `04_train_test_config.json`):

```json
{
  "system_version": "SPAFS V5.2 Production & Temporal Governance",
  "temporal_cutoffs": {
    "platts_singapore_moc": "16:30:00 SGT (UTC+8)",
    "ice_brent_london_close": "03:30:00 SGT (next day, UTC+8)",
    "point_in_time_freeze": "08:30:00 SGT (forecast origin t_origin)"
  },
  "stream1_econometric_config": {
    "sample_range": "2008-05-02 -> 2025-12-30",
    "effective_sample_n": 4425,
    "in_sample_warmup": 3500,
    "out_of_sample_n": 925,
    "hac_covariance_maxlags": 5,
    "models": ["M0a", "M0b", "M1", "M2", "M3"]
  },
  "stream2_machine_learning_config": {
    "sample_range": "2017-01-03 -> 2025-12-30",
    "effective_sample_n": 2254,
    "initial_window_tau_0": 1500,
    "refit_cadence_days": 20,
    "out_of_sample_n": 754,
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
  "feature_spaces": {
    "M0a": [],
    "M0b": ["mg95_return_pct (sign)"],
    "M1": ["mg95_return_pct"],
    "M2": ["mg95_return_pct", "mg95_return_lag1", "brent_return_pct_aligned", "brent_return_lag1", "spread_mg95_brent_lag1"],
    "M3": ["mg95_return_pct", "mg95_return_lag1", "brent_return_pos", "brent_return_neg", "brent_return_pos_lag1", "brent_return_neg_lag1", "spread_mg95_brent_lag1"],
    "M4": ["mg95_return_pct", "mg95_return_lag1", "mg95_return_lag2", "mg95_return_lag3", "brent_return_pct_aligned", "brent_return_lag1", "brent_return_lag2", "brent_return_lag3", "vol_mg95_30d", "economic_shock_flag"],
    "M5": ["M4_features (10)", "spread_mg95_brent", "spread_mg95_brent_lag1", "spread_mg95_mg92", "spread_mg95_do005", "octane_spread_nonpositive_flag"]
  }
}
```
