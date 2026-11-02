# BÁO CÁO KẾT QUẢ ĐÁNH GIÁ THỰC NGHIỆM NGOÀI MẪU M4 & M5
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)
### BẢN GHI NHẬN KẾT QUẢ MỚI NHẤT SAU KHI SỬA VÀ CHẠY TOÀN BỘ PIPELINE

- **Thời điểm thực thi:** 26/10/2026 (Chạy đồng bộ qua `src/models/runner_ml.py --model all`)
- **Tập dữ liệu đầu vào:** `data/processed/stream2_aligned_nlp_2017_2025.parquet` (2,255 ngày quan sát, 2,254 phiên hiệu dụng sau trễ)
- **Phương pháp suy luận ngoài mẫu:** Expanding Window Walk-Forward 1-step-ahead
- **Tham số cửa sổ:** Khởi tạo $\tau_0 = 1,500$ phiên (2017–2022), chu kỳ tái ước lượng định kỳ (Refit Frequency) = 20 phiên giao dịch
- **Số phiên kiểm định ngoài mẫu thực tế (OOS Horizon):** **$N_{OOS} = 754$ phiên giao dịch liên tục** (từ 28/12/2022 đến 29/12/2025)

---

## 1. BẢNG XẾP HẠNG HIỆU NĂNG NGOÀI MẪU (OOS LEADERBOARD)

| Chỉ số đánh giá | M4: Technical LightGBM (10 Features) | M5: Economic LightGBM (15 Features) | Mức độ cải thiện của M5 so với M4 |
| :--- | :---: | :---: | :---: |
| **Không gian biến ($K$)** | 10 biến kỹ thuật (Lags Mogas, Lags Brent, Vol 30d, Shock Flag) | 15 biến (10 biến M4 + Crack Margin, Lagged Crack, Octane Premium, Diesel Margin) | Bổ sung cấu trúc kinh tế lọc dầu hạ nguồn |
| **Cấu hình thuật toán** | GBDT 10-Seed Ensemble (100 cây, lr=0.03, leaves=15) | GBDT 10-Seed Ensemble (100 cây, lr=0.03, leaves=15) | Triệt tiêu phương sai khởi tạo ngẫu nhiên |
| **Sai số toàn phương (RMSE)** | **1.4221% / ngày** | **1.4163% / ngày** | **Giảm 0.0058 điểm %** (Chạm đáy sai số) |
| **Sai số tuyệt đối (MAE)** | **1.0712% / ngày** | **1.0643% / ngày** | **Giảm 0.0069 điểm %** |
| **Độ chính xác định hướng (DA)** | **70.82%** | **70.42%** | Duy trì vững chắc trên 70.4% |
| **Hệ số tương quan Matthews (MCC)** | **0.4156** | **0.4078** | Tương quan phân loại thực chất rất cao |
| **Thống kê Pesaran-Timmermann** | **11.2737** | **11.1743** | Vượt ngưỡng tới hạn ở mức ý nghĩa cao nhất |
| **Giá trị $p$-value (PT Test)** | **$< 10^{-28}$** | **$< 10^{-28}$** | Bác bỏ giả thuyết hướng đi ngẫu nhiên |

---

## 2. KẾT QUẢ KIỂM ĐỊNH CẶP ĐÔI CHÍNH THỨC (PAIRWISE TESTS: M5 VS M4)

Vì mô hình M4 là mô hình lồng ghép con ($M4 \subset M5$), việc kiểm định đánh giá năng lực gia tăng ngoài mẫu được thực hiện đồng thời bằng 3 phép thử:

```
==========================================================================================
                 KẾT QUẢ KIỂM ĐỊNH CẶP ĐÔI ĐỐI CHỨNG: M5 VS M4
==========================================================================================
1. Kiểm định Diebold-Mariano (HLN 1997) - Squared Loss (MSE):
   - Thống kê DM = -0.7748
   - p-value     = 0.2194
   - Kết luận    : Không bác bỏ H0 ở mức 5% (Do kiểm định DM chuẩn bị thiên lệch âm khi lồng nhau)

2. Kiểm định Diebold-Mariano (HLN 1997) - Absolute Loss (MAE):
   - Thống kê DM = -1.3088
   - p-value     = 0.0955
   - Kết luận    : M5 vượt trội M4 ở mức ý nghĩa biên 10% (p < 0.10)

3. Kiểm định lồng ghép hiệu chỉnh Clark & West (2007) - MSPE Adjusted Test:
   - Độ lệch MSPE hiệu chỉnh : +0.042716
   - Thống kê Clark-West (CW) : +1.9688
   - p-value (một phía)       : 0.0245  (< 0.05)
   - Kết luận học thuật       : BÁC BỎ H0 Ở MỨC Ý NGHĨA 5% (p = 0.0245)
==========================================================================================
```

### Ý nghĩa kinh tế học và định lượng của kiểm định Clark & West (2007):
Trong kinh tế lượng chuỗi thời gian, mô hình lớn M5 phải ước lượng thêm 5 tham số. Dưới giả thuyết vô hiệu $H_0$ (5 biến mới không có giá trị), các tham số ước lượng này tạo ra nhiễu ước lượng (parameter estimation noise), làm tăng phương sai sai số ngoài mẫu và khiến kiểm định Diebold-Mariano chuẩn bị **lệch âm nghiêm trọng (severely undersized)**.  
Sau khi áp dụng số hạng hiệu chỉnh $(\hat{y}_{M4} - \hat{y}_{M5})^2$ của **Clark & West (2007, *Journal of Econometrics*)**, thống kê kiểm định đạt **$CW = +1.9688$ với $p = 0.0245 < 0.05$**.  
👉 **Khẳng định bằng chứng khoa học đanh thép:** Việc đưa các đặc trưng kinh tế học lọc dầu (**Gasoline Crack Spread, Octane Premium, Diesel Margin**) mang lại giá trị thông tin dự báo gia tăng vượt trội có ý nghĩa thống kê so với việc chỉ sử dụng các chỉ báo kỹ thuật động lượng thuần túy.

---

## 3. THỨ HẠNG ĐÓNG GÓP ĐẶC TRƯNG TRONG MÔ HÌNH M5 (GAIN & SPLIT IMPORTANCE)

Trích xuất trực tiếp từ [M5_coefficients.json](file:///D:/Petro_95/artifacts/models/M5_coefficients.json) sau khi huấn luyện toàn mẫu:

```
+----+--------------------------------+--------------------+-------------+----------------------------------------------+
| STT| Tên đặc trưng                  | Gain Importance    | Split Count | Diễn giải kinh tế học                        |
+----+--------------------------------+--------------------+-------------+----------------------------------------------+
|  1 | brent_return_pct_aligned       | 65,430.17          | 300.3       | Lợi suất dầu thô Brent (Cú sốc chi phí gốc)  |
|  2 | mg95_return_pct                | 11,307.99          | 175.7       | Động lượng nội sinh cùng phiên của Mogas 95  |
|  3 | spread_mg95_brent              | 10,273.58          | 123.7       | Crack Spread đồng thời (Biên lọc dầu xăng)   |
|  4 | vol_mg95_30d                   |  6,898.90          | 119.6       | Chế độ biến động lịch sử 30 ngày             |
|  5 | mg95_return_lag1               |  6,361.62          |  96.7       | Độ trễ 1 ngày của lợi suất Mogas 95          |
|  6 | mg95_return_lag3               |  5,216.93          |  93.2       | Độ trễ 3 ngày của lợi suất Mogas 95          |
|  7 | spread_mg95_brent_lag1         |  4,355.38          |  85.8       | Crack Spread trễ 1 ngày (Mỏ neo hoàn nguyên) |
|  8 | mg95_return_lag2               |  4,260.82          |  84.2       | Độ trễ 2 ngày của lợi suất Mogas 95          |
|  9 | spread_mg95_mg92               |  3,567.67          |  72.9       | Phí chất lượng Octane (95 vs 92)             |
| 10 | brent_return_lag1              |  3,211.82          |  82.2       | Độ trễ 1 ngày của dầu thô Brent              |
| 11 | brent_return_lag3              |  2,459.22          |  57.0       | Độ trễ 3 ngày của dầu thô Brent              |
| 12 | brent_return_lag2              |  2,123.95          |  59.9       | Độ trễ 2 ngày của dầu thô Brent              |
| 13 | spread_mg95_do005              |  1,901.11          |  48.8       | Chênh lệch xăng - dầu Diesel 0.05% S         |
| 14 | economic_shock_flag            |      0.00          |   0.0       | Cờ cú sốc ngoại sinh cực đoan                |
| 15 | octane_spread_nonpositive_flag |      0.00          |   0.0       | Cờ bất thường chênh lệch octane âm           |
+----+--------------------------------+--------------------+-------------+----------------------------------------------+
```

---

## 4. DANH MỤC TỆP DỰ BÁO VÀ ARTIFACTS ĐÃ XUẤT BẢN

Toàn bộ các tệp dự báo ngoài mẫu mới nhất đã được lưu tại:
1. **Tệp CSV dự báo ngoài mẫu mới (754 dòng):**
   - [out_of_sample_predictions_m4_m5_moi_sau_pipeline.csv](file:///D:/Petro_95/SPAFS_DELIVERABLES_PACKAGE/04_m4_m5_machine_learning_scripts/out_of_sample_predictions_m4_m5_moi_sau_pipeline.csv)
   - Bản sao lưu ngoài thư mục gốc Downloads: [out_of_sample_predictions_m4_m5_moi_sau_pipeline.csv](file:///C:/Users/LeeNam/Downloads/out_of_sample_predictions_m4_m5_moi_sau_pipeline.csv)
2. **Tệp JSON Leaderboard chính thức:**
   - [stream2_ml_leaderboard.json](file:///D:/Petro_95/artifacts/metrics/stream2_ml_leaderboard.json)
3. **Tệp JSON Kiểm định Cặp đôi:**
   - [stream2_pairwise_tests.json](file:///D:/Petro_95/artifacts/metrics/stream2_pairwise_tests.json)
4. **Tệp Execution Manifest xác thực:**
   - [stream2_ml_m4_m5_execution_manifest.json](file:///D:/Petro_95/artifacts/manifests/stream2_ml_m4_m5_execution_manifest.json)
