# BIÊN BẢN KIỂM TOÁN RANDOM SEEDS VÀ ĐỘ ỔN ĐỊNH HUẤN LUYỆN DEEP LEARNING (SPAFS V5.2)

## 1. Danh sách Random Seeds Sử dụng
- **Danh sách hạt giống ngẫu nhiên (5 independent seeds):** `[42, 101, 202, 303, 404]`
- **Lý do lựa chọn:** Tránh thiên lệch chọn seed thuận lợi (*seed snooping*), đảm bảo bao quát các điểm xuất phát không gian trọng số khác nhau.
- **Nguyên tắc Quản trị Dữ liệu (Point-in-Time Data Governance):**
  1. `StandardScaler` được `.fit()` **DUY NHẤT** trên tập huấn luyện (Train sequences). Tuyệt đối không fit trên tập Validation hoặc Test.
  2. Cơ chế **Purging & Embargo**: Ranh giới Train và Validation được cách ly đúng bằng $h + \text{Embargo}$ quan sát.
  3. Cửa sổ trượt lookback: $L = 20$ phiên giao dịch (~1 tháng lịch sử).

## 2. Bảng Tổng Hợp Độ Ổn Định Đa Hạt Giống (Mean ± Standard Deviation)

| Khung thời gian | Mô hình | Cỡ mẫu OOS | Ensemble RMSE | Ensemble MAE | Ensemble DA (%) | Seed Mean ± Std RMSE | Seed Mean ± Std DA (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | **RNN** | 754 | 1.4403% | 1.0810% | 68.83% | 1.4705% ± 0.0241% | 68.38% ± 0.86% |
| Daily | **LSTM** | 754 | 1.4681% | 1.1003% | 67.90% | 1.4968% ± 0.0379% | 67.82% ± 0.91% |
| Weekly | **RNN** | 750 | 4.0148% | 3.0938% | 54.93% | 4.0493% ± 0.0602% | 52.56% ± 3.45% |
| Weekly | **LSTM** | 750 | 4.1283% | 3.1880% | 48.93% | 4.1396% ± 0.0441% | 47.68% ± 0.88% |
| Monthly | **RNN** | 734 | 7.3374% | 5.9615% | 49.73% | 7.4887% ± 0.1795% | 50.25% ± 1.01% |
| Monthly | **LSTM** | 734 | 9.4405% | 7.1487% | 51.23% | 10.5629% ± 3.9486% | 49.81% ± 2.03% |

## 3. Lịch Sử Huấn Luyện Từng Lần Chạy (Epochs & Runtime Summary)

| Khung | Mô hình | Random Seed | Số Epochs Đã Chạy | Best Epoch | Best Val Loss (MSE) | Runtime (giây) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | **RNN** | 42 | 8 | 2 | 6.7557 | 1.49s |
| Daily | **RNN** | 101 | 11 | 5 | 6.5392 | 0.93s |
| Daily | **RNN** | 202 | 7 | 1 | 6.9473 | 0.59s |
| Daily | **RNN** | 303 | 8 | 2 | 6.7309 | 0.66s |
| Daily | **RNN** | 404 | 8 | 2 | 6.9119 | 0.7s |
| Daily | **LSTM** | 42 | 22 | 16 | 6.6423 | 1.93s |
| Daily | **LSTM** | 101 | 9 | 3 | 6.7860 | 0.78s |
| Daily | **LSTM** | 202 | 9 | 3 | 7.1808 | 0.79s |
| Daily | **LSTM** | 303 | 9 | 3 | 6.9138 | 0.78s |
| Daily | **LSTM** | 404 | 10 | 4 | 6.9104 | 0.87s |
| Weekly | **RNN** | 42 | 7 | 1 | 39.6976 | 0.57s |
| Weekly | **RNN** | 101 | 14 | 8 | 39.5412 | 1.23s |
| Weekly | **RNN** | 202 | 11 | 5 | 38.5016 | 0.95s |
| Weekly | **RNN** | 303 | 10 | 4 | 38.9018 | 0.85s |
| Weekly | **RNN** | 404 | 8 | 2 | 39.7302 | 0.7s |
| Weekly | **LSTM** | 42 | 7 | 1 | 40.0697 | 0.63s |
| Weekly | **LSTM** | 101 | 7 | 1 | 40.6288 | 0.63s |
| Weekly | **LSTM** | 202 | 7 | 1 | 40.7977 | 0.67s |
| Weekly | **LSTM** | 303 | 7 | 1 | 41.2407 | 0.67s |
| Weekly | **LSTM** | 404 | 7 | 1 | 40.4798 | 0.63s |
| Monthly | **RNN** | 42 | 8 | 2 | 191.6601 | 0.7s |
| Monthly | **RNN** | 101 | 13 | 7 | 185.0705 | 1.21s |
| Monthly | **RNN** | 202 | 8 | 2 | 203.4573 | 0.8s |
| Monthly | **RNN** | 303 | 10 | 4 | 193.7463 | 0.94s |
| Monthly | **RNN** | 404 | 12 | 6 | 212.2414 | 1.13s |
| Monthly | **LSTM** | 42 | 22 | 16 | 190.9632 | 2.34s |
| Monthly | **LSTM** | 101 | 14 | 8 | 203.0414 | 1.41s |
| Monthly | **LSTM** | 202 | 10 | 4 | 200.3082 | 0.98s |
| Monthly | **LSTM** | 303 | 18 | 12 | 189.0545 | 1.73s |
| Monthly | **LSTM** | 404 | 7 | 1 | 205.1219 | 0.64s |