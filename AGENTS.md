# AGENTS.md — Pipeline Dự báo Điểm & Chiều hướng Xăng Platts Singapore Mogas 95

Repository chính thức của dự án **Pipeline Dự báo Điểm & Chiều hướng Xăng Platts Singapore Mogas 95 (Naive, XGBoost, LSTM, GRU)** theo đặc tả học thuật tại `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`.

## 1. Mục tiêu & 3 Câu hỏi Nghiên cứu (Research Questions)
Dự án nhằm giải quyết 3 câu hỏi nghiên cứu thực nghiệm cốt lõi theo tinh thần khách quan, không giả định trước kết quả:
- **RQ1 (Target Representation)**: So sánh biến động tương đối (Relative Change) $R_{o,h} = (P^M_{o+h} - P^M_o)/P^M_o$ với dự báo trực tiếp mức giá (Price Level) $y_{o,h} = P^M_{o+h}$.
- **RQ2 (Exogenous Information)**: So sánh mô hình Đa biến (Multivariate: Mogas 95 + Brent) với mô hình Đơn biến (Univariate: chỉ Mogas 95) để đánh giá đóng góp thông tin của Brent.
- **RQ3 (Model Comparison)**: So sánh hiệu năng của các mô hình học máy và học sâu (XGBoost, LSTM, GRU) với baseline bắt buộc **Naive Persistence** theo từng kỳ hạn ($h \in \{1, 5, 21\}$).

## 2. Dữ liệu nguồn bất biến (Immutable Dataset)
- **Đường dẫn**: `data/interim/canonical_market_panel.parquet`
- **Nguyên tắc**: Tuyệt đối chỉ đọc (Read-only), không chỉnh sửa, thêm bớt, ghi đè hay làm sai lệch file dữ liệu gốc.
- **Hiện trạng snapshot**: 4,428 phiên giao dịch liên tục (02/05/2008 – 30/12/2025), 0 giá trị thiếu trên 2 chuỗi giá `MG95` và `brent_close`.

## 3. Thư mục lưu trữ các tập chia vật lý (Physical Splits by Year)
- **Thư mục chuyên biệt**: `data/splits/`
- **Các tập phân chia tuần tự (Chronological Splits)**:
  - `data/splits/train_2008_2020.parquet` (và `.csv`): 70% Train (2008–2020, 3,099 dòng).
  - `data/splits/val_2021_2023.parquet` (và `.csv`): 15% Validation (2021–2023, 664 dòng).
  - `data/splits/test_2024_2025.parquet` (và `.csv`): 15% Test (2024–2025, 665 dòng).
  - `data/splits/splits_manifest.json`: Báo cáo audit xác nhận mốc thời gian, SHA-256 checksum và kết quả kiểm toán PIT.

## 4. Ràng buộc học thuật & Phương pháp luận cốt lõi (REVISED)
- **Quy tắc Point-in-Time (PIT) bắt buộc**:
  $$\text{feature\_available\_at} \leq \text{forecast\_origin}$$
  Forecast origin dự kiến lúc **08:30 Asia/Singapore**. Mọi feature đầu vào phải thực sự khả dụng trước mốc này; target Mogas nằm sau mốc này theo đúng kỳ hạn $h$. Chỉ báo cáo "Zero Lookahead Bias" khi pipeline vượt qua automated PIT check.
- **Phương pháp mục tiêu**:
  1. *Phương pháp chính (Primary)*: Relative Change $R_{o,h} = (P^M_{o+h} - P^M_o)/P^M_o$, chuẩn hóa cục bộ từng biến theo giá trị mới nhất khả dụng trong cửa sổ $L=30$: $z^{(j)}_{o,k} = P^{(j)}_{o-k}/P^{(j)}_o - 1$. Tái lập giá: $\hat{P}^M_{o+h} = P^M_o(1 + \hat{R}_{o,h})$.
  2. *Ablation phụ (Secondary)*: Price Level $y_{o,h} = P^M_{o+h}$ với scaler fit DUY NHẤT trên tập Train, không clipping tập Test.
- **Chiến lược đa kỳ hạn**: Bắt buộc dùng **Direct Multi-Horizon Strategy** (huấn luyện mô hình độc lập cho từng $h \in \{1, 5, 21\}$, không dùng Joint/MIMO đa đầu ra trong phạm vi MVP).
- **Mô hình MVP**: **Naive Persistence** (baseline bắt buộc), **XGBoost Regressor**, **LSTM**, **GRU**. *(CNN-LSTM được xác định là mở rộng sau MVP, không nằm trong phạm vi MVP)*.
- **Ma trận 33 cấu hình thực nghiệm MVP**:
  - *21 cấu hình Relative Change*: 18 cấu hình học máy/học sâu (3 mô hình XGBoost, LSTM, GRU × 2 kịch bản Univariate/Multivariate × 3 kỳ hạn $h \in \{1, 5, 21\}$) + 3 cấu hình Naive Persistence baseline.
  - *12 cấu hình Price Level ablation*: 2 mô hình đại diện (XGBoost & LSTM) × 2 kịch bản Univariate/Multivariate × 3 kỳ hạn $h \in \{1, 5, 21\}$.
- **Thước đo đánh giá**: MAE, MSE, RMSE, MAPE, $R^2$, Directional Accuracy (DA). Tất cả tính toán sau khi tái lập về đơn vị **USD/thùng**. Không đặt chỉ tiêu DA chủ quan 60–70%; so sánh khách quan với Naive baseline và phân phối Up/Down thực tế.

## 5. Thư mục đầu ra kết xuất (Outputs)
Toàn bộ kết quả thực nghiệm được chuẩn hóa kết xuất vào thư mục `outputs/`:
```text
outputs/
├── checkpoints/                    # Checkpoint tốt nhất của LSTM, GRU
├── predictions/
│   ├── predictions_h1.csv
│   ├── predictions_h5.csv
│   └── predictions_h21.csv
├── figures/
│   ├── actual_vs_predicted_h1.png
│   ├── actual_vs_predicted_h5.png
│   ├── actual_vs_predicted_h21.png
│   ├── directional_confusion_matrix.png
│   └── loss_curves.png
├── benchmark_leaderboard.csv       # Tổng hợp đầy đủ 33 cấu hình
└── experiment_manifest.json        # Metadata chi tiết để tái lập toàn bộ thí nghiệm
```

## Agent skills

### Issue tracker

Issues, specs, and implementation tasks are tracked as local markdown files under `.scratch/traditional-pipeline/issues/`. Ticket naming convention: `NN-<slug>.md` (e.g., `01-data-audit-and-dataset.md`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical triage role labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout with core problem specification at `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`. Note that root `GLOSSARY.md` and `docs/adr/0001–0005` belong to the legacy SPAFS V5.2 project and do not govern this pipeline. See `docs/agents/domain.md`.
