# SPAFS V5.2 — Singapore Petroleum Asymmetric & Risk Forecasting System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-81%2F81%20Passing-brightgreen)]()
[![Governance](https://img.shields.io/badge/Point--in--Time-08%3A30%20SGT%20Strict-blue)]()

Hệ thống nghiên cứu định lượng và dự báo giá xăng thành phẩm bán buôn **Platts FOB Singapore Mogas 95 (MG95)** — chuỗi giá cơ sở tham chiếu cho điều hành giá xăng dầu tại Việt Nam — kết hợp dữ liệu dầu thô **ICE Brent (`BZ=F`)** và biên lợi nhuận lọc dầu giai đoạn **2008–2025**.

Dự án được tổ chức thành **3 luồng thực thi độc lập, tái lập 100%** (điều phối qua [`run_pipeline.py`](run_pipeline.py)):

1. **Luồng 1 (`--flow data`) — Kỹ nghệ dữ liệu & Quản trị Point-in-Time (08:30 SGT):** Làm sạch, kiểm toán 8 cổng dữ liệu, căn chỉnh múi giờ London/New York → Singapore và tạo mục tiêu đa kỳ hạn ($h \in \{1, 5, 21\}$ phiên).
2. **Luồng 2 (`--flow point`) — Dự báo điểm & hướng giá ($M0a \to M5$, RNN, LSTM):** Kiểm định truyền dẫn bất đối xứng (RQ1), giá trị kinh tế lọc dầu (RQ2) và giới hạn dự báo đa kỳ hạn.
3. **Luồng 3 (`--flow risk`) — Dự báo khoảng dao động & rủi ro giá ($Q0 \to Q4$, Hướng 4):** Dự báo 9 phân vị có điều kiện, khoảng dự báo 80%/95%, xác suất tăng và phân tầng chế độ rủi ro bằng mô phỏng lịch sử có lọc (FHS), GARCH(1,1)-$t$, hồi quy phân vị và Conformal LightGBM (CQR).

---

## 1. Cấu trúc thư mục dự án (Đã tinh gọn & chuẩn hóa theo luồng)

```text
Petro_95/
├── run_pipeline.py                              # Bộ điều phối tổng (CLI) cho cả 3 luồng + kiểm thử
├── README.md                                    # Tài liệu tổng quan và hướng dẫn vận hành
│
├── data/                                        # Kiến trúc dữ liệu 3 tầng
│   ├── raw/                                     # Dữ liệu gốc bất biến (Platts 2008–2025, ICE Brent)
│   ├── interim/                                 # Dữ liệu trung gian đã qua kiểm toán Data Contract
│   └── processed/                               # Dữ liệu sẵn sàng cho mô hình (Stream 1, Stream 2, Multi-horizon)
│
├── src/                                         # Toàn bộ mã nguồn cốt lõi (27 module Python)
│   ├── data_proccessing/                        # [LUỒNG 1] Kỹ nghệ dữ liệu & Quản trị Point-in-Time
│   │   ├── config.py                            # Cấu hình đóng băng, đường dẫn, quy tắc 08:30 SGT
│   │   ├── aliases.py                           # Ánh xạ tên cột & danh sách đặc trưng hợp lệ
│   │   ├── model_schemas.py                     # Khai báo schema đầu vào/đầu ra cho các mô hình
│   │   ├── exceptions.py                        # Ngoại lệ DataContractViolationError
│   │   ├── helpers.py                           # Chuẩn hóa tên cột, xử lý thời gian SGT & JSON
│   │   ├── io.py                                # Đọc/ghi Parquet & CSV an toàn
│   │   ├── pipeline.py                          # Điều phối 8 cổng xử lý dữ liệu (Step 01 -> Step 08)
│   │   └── data_handling/                       # Các module xử lý và kiểm toán chuyên biệt
│   │       ├── validate_plats.py                # Gate 1.1: Kiểm toán Platts Mogas 95/92 & Gasoil
│   │       ├── validate_brent.py                # Gate 1.2: Kiểm toán hợp đồng tương lai Brent
│   │       ├── alignment.py                     # Gate 1.3: Ghép nối As-Of trước 08:30 SGT
│   │       ├── target.py                        # Step 04A: Mục tiêu lợi suất & hướng 1 ngày
│   │       ├── multi_horizon_targets.py         # Step 04B: Mục tiêu đa kỳ hạn (h = 1, 5, 21 phiên)
│   │       ├── market_features.py               # Step 05: Crack spread, volatility 30D, cú sốc
│   │       ├── news_pit.py                      # Step 06: Khung tổng hợp tin tức theo PIT
│   │       ├── patrition.py                     # Step 07: Chia Luồng 1 (2008–2025) & Luồng 2 (2017–2025)
│   │       ├── weekly.py                        # Step 08: Dữ liệu tần suất tuần (robustness)
│   │       ├── audit_record_level_pit.py        # Kiểm toán bất biến thời gian từng bản ghi
│   │       └── stationarity_audit.py            # Kiểm định nghiệm đơn vị ADF & tính dừng KPSS
│   │
│   └── models/                                  # [LUỒNG 2 & 3] Hệ thống mô hình, kiểm định & đánh giá
│       ├── base.py                              # Lớp cơ sở BaseForecastingModel
│       ├── diagnostics.py                       # Kiểm định đa cộng tuyến (VIF) & phần dư
│       ├── persistence.py                       # Quản lý lưu trữ mô hình và manifest SHA-256
│       ├── validation/
│       │   └── walk_forward.py                  # Engine walk-forward dùng chung (purge = h, embargo E)
│       ├── evaluation/
│       │   ├── forecast_tests.py                # Metric dự báo điểm & kiểm định DM-HLN, CW, PT
│       │   ├── interval_tests.py                # Metric phân vị/khoảng: Pinball, Kupiec, Christoffersen, QLIKE
│       │   ├── hypothesis.py                    # Kiểm định Wald HAC cho giả thuyết đối xứng RQ1
│       │   ├── consolidate_multi_horizon_analysis.py # Tổng hợp bảng xếp hạng & kiểm định đa kỳ hạn
│       │   └── reproducible_pairwise_audit.py   # Đối soát thống kê trên cửa sổ OOS chung (754 phiên)
│       ├── econometric/                         # Mô hình kinh tế lượng (M0a, M0b, M1, M2, M3)
│       │   ├── naive.py                         # M0a (Random Walk) & M0b (Momentum/Persistence)
│       │   ├── arma.py                          # M1: ARMA(1,1) đa bước
│       │   └── dynamic_adl.py                   # M2 (ADL đối xứng) & M3 (ADL bất đối xứng)
│       ├── ml/
│       │   └── lgbm.py                          # M4 (LightGBM kỹ thuật) & M5 (LightGBM kinh tế lọc dầu)
│       ├── dl/
│       │   └── sequence_models.py               # Ensemble 5 seed cho RNN & LSTM đa kỳ hạn
│       ├── risk/                                # [LUỒNG 3 - HƯỚNG 4] Dự báo khoảng & rủi ro giá
│       │   ├── quantile_models.py               # 5 mô hình phân vị Q0, Q1 (EWMA), Q2 (GARCH-t), Q3 (QR), Q4 (CQR)
│       │   └── figures.py                       # Sinh biểu đồ quạt (fan chart), độ bao phủ & tỷ số rủi ro
│       ├── runner_econometric.py                # Runner Luồng 2A: M0a–M3 trên Stream 1 & Wald RQ1
│       ├── runner_ml.py                         # Runner Luồng 2B: M4–M5 trên Stream 2 & CW/DM RQ2
│       ├── runner_multi_horizon_traditional.py  # Runner Luồng 2C: M0a–M5 đa kỳ hạn (h = 1, 5, 21)
│       └── runner_risk_multi_horizon.py         # Runner Luồng 3: Q0–Q4 đa kỳ hạn trên Stream 1 & Stream 2
│
├── reports/                                     # Báo cáo phân tách rõ theo từng nhánh nghiên cứu
│   ├── data_quality/                            # [Luồng 1] Báo cáo kiểm toán dữ liệu, PIT & tính dừng (.csv/.json)
│   ├── 01_point_forecasting/                    # [Luồng 2] Báo cáo dự báo điểm & hướng (M0a–M5, RNN/LSTM)
│   │   ├── 01_TRINH_BAY_DE_HIEU.md              # Bản trình bày trực quan cho giảng viên
│   │   └── 02_BAO_CAO_KY_THUAT_M0_M5_DL.md      # Đặc tả kỹ thuật, sửa lỗi & bảng số đầy đủ
│   ├── 02_risk_forecasting/                     # [Luồng 3 - Hướng 4] Báo cáo dự báo khoảng & rủi ro (Q0–Q4)
│   │   ├── 01_TRINH_BAY_DE_HIEU.md              # Bản trình bày trực quan, dễ hiểu cho giảng viên
│   │   ├── 02_DAC_TA_KY_THUAT_VA_KET_QUA.md     # Đặc tả pipeline, công thức metric, DM & so sánh tài liệu
│   │   └── 03_KE_HOACH_NGHIEN_CUU_HUONG_4.md    # Đề cương thiết kế ban đầu của Hướng 4
│   └── 03_future_directions/                    # Định hướng mở rộng tiếp theo
│       └── HUONG_1_DU_BAO_TUAN_THANG_BANG_GIA_KY_HAN.md # Kế hoạch tích hợp dữ liệu kỳ hạn (swap/futures)
│
├── artifacts/                                   # Kết quả đầu ra từ thực nghiệm (đồng bộ 100% với code)
│   ├── models/                                  # Trọng số & hệ số M0a..M5 (.joblib, .json)
│   ├── predictions/                             # Dự báo OOS từng phiên của Stream 1 & Stream 2 (.parquet)
│   ├── metrics/                                 # Bảng xếp hạng, Wald test, VIF, kiểm định cặp (.csv, .json)
│   ├── multi_horizon/                           # Dự báo & bảng xếp hạng đa kỳ hạn M0a..M5
│   ├── deep_learning/                           # Dự báo OOS & checkpoint 30 mô hình RNN/LSTM
│   ├── master_consolidation/                    # Bảng tổng hợp đa kỳ hạn, kiểm định HAC & phân tích cú sốc
│   ├── manifests/                               # Hồ sơ truy vết thực thi & kiểm toán PIT (.json)
│   └── risk/                                    # Đầu ra Hướng 4 (stream1/, stream2/, figures/)
│
├── notebooks/                                   # Sổ tay khám phá dữ liệu (EDA) & thu thập dữ liệu
│   ├── 01_crawl_data.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_platts_and_brent.ipynb
│   ├── 04_eda_cross_market_interaction.ipynb
│   └── 05_eda_thuyet_trinh_mg95_brent.ipynb
│
├── docs/                                        # Quản trị kiến trúc (ADR 0001–0005) & Từ điển thuật ngữ (GLOSSARY)
│   ├── GLOSSARY.md
│   ├── adr/
│   └── agents/
│
└── tests/                                       # Bộ 81 kiểm thử tự động (Unit & Integration Tests)
    ├── test_model_schemas.py
    ├── test_hypothesis_and_guards.py
    ├── test_models.py
    ├── test_forecast_tests_and_walk_forward.py
    └── test_risk_models_and_interval_tests.py
```

---

## 2. Hướng dẫn chạy theo từng luồng

Môi trường Python chuẩn của dự án: `D:\Test\env_prj\Scripts\python.exe` (Python 3.11, đã cài đặt đầy đủ `pandas`, `numpy`, `scipy`, `statsmodels`, `arch`, `lightgbm`, `torch`, `pytest`).

### Cách 1: Chạy qua bộ điều phối tổng `run_pipeline.py` (Khuyên dùng)

```powershell
# 1. Chạy toàn bộ 81 test kiểm tra công thức, chống rò rỉ dữ liệu & mô hình (~50 giây)
D:\Test\env_prj\Scripts\python.exe run_pipeline.py --flow test

# 2. Chạy Luồng 1: Kỹ nghệ dữ liệu Point-in-Time & kiểm toán tính dừng
D:\Test\env_prj\Scripts\python.exe run_pipeline.py --flow data

# 3. Chạy Luồng 2: Dự báo điểm & hướng giá (M0a-M5, RNN, LSTM + kiểm định DM/CW/PT/Wald)
D:\Test\env_prj\Scripts\python.exe run_pipeline.py --flow point

# 4. Chạy Luồng 3 (Hướng 4): Dự báo khoảng dao động & rủi ro giá (Q0-Q4 + vẽ biểu đồ)
D:\Test\env_prj\Scripts\python.exe run_pipeline.py --flow risk

# Hoặc chạy toàn bộ từ đầu đến cuối (test -> data -> point -> risk)
D:\Test\env_prj\Scripts\python.exe run_pipeline.py --flow all
```

### Cách 2: Chạy riêng lẻ từng bước trong từng luồng

```powershell
# --- LUỒNG 1: DỮ LIỆU ---
D:\Test\env_prj\Scripts\python.exe -m src.data_proccessing.pipeline
D:\Test\env_prj\Scripts\python.exe -m src.data_proccessing.data_handling.multi_horizon_targets
D:\Test\env_prj\Scripts\python.exe -m src.data_proccessing.data_handling.audit_record_level_pit
D:\Test\env_prj\Scripts\python.exe -m src.data_proccessing.data_handling.stationarity_audit

# --- LUỒNG 2: DỰ BÁO ĐIỂM & HƯỚNG (M0a-M5, RNN, LSTM) ---
D:\Test\env_prj\Scripts\python.exe src/models/runner_econometric.py
D:\Test\env_prj\Scripts\python.exe src/models/dl/sequence_models.py
D:\Test\env_prj\Scripts\python.exe src/models/runner_multi_horizon_traditional.py
D:\Test\env_prj\Scripts\python.exe src/models/runner_ml.py --model all
D:\Test\env_prj\Scripts\python.exe src/models/evaluation/consolidate_multi_horizon_analysis.py
D:\Test\env_prj\Scripts\python.exe src/models/evaluation/reproducible_pairwise_audit.py

# --- LUỒNG 3 (HƯỚNG 4): DỰ BÁO KHOẢNG & RỦI RO (Q0-Q4) ---
D:\Test\env_prj\Scripts\python.exe src/models/runner_risk_multi_horizon.py --dataset all
D:\Test\env_prj\Scripts\python.exe src/models/risk/figures.py
```

---

## 3. Tóm tắt kết quả cốt lõi của dự án

| Nhánh nghiên cứu | Kỳ hạn 1 ngày ($h=1$) | Kỳ hạn 1 tuần ($h=5$) | Kỳ hạn 1 tháng ($h=21$) |
|---|---|---|---|
| **Luồng 2: Dự báo điểm & hướng** (`M0a..M5`, `RNN`, `LSTM`) | **Dự báo tốt:** `M2` (ADL) giảm **39,8%** MSE so với Random Walk; đoán đúng hướng **69–71%** nhờ độ trễ múi giờ từ giá dầu Brent đêm qua. Truyền dẫn giá bán buôn là **đối xứng** (Wald $p = 0,95$). | **Cải thiện nhỏ:** `M4` (LightGBM) giảm **4,6%** MSE; đúng hướng ~56%. | **Không dự báo được hướng:** Mọi mô hình điểm đều có $R^2_{\text{OOS}} < 0$ (thông tin quá khứ đã phản ánh hết vào giá). |
| **Luồng 3 (Hướng 4): Dự báo khoảng & rủi ro** (`Q0..Q4`) | **Dự báo cả hướng lẫn biên độ:** `Q3` (Hồi quy phân vị) giảm **25–26%** pinball loss, thu hẹp khoảng 80% từ 17–32%, Brier skill **+25%**. | **Khoảng hiệu chỉnh chuẩn:** `Q3` đạt độ bao phủ **80,1%** (mục tiêu 80%), giảm **5,5–9,1%** pinball loss ($p < 0,001$). | **Dự báo tốt mức độ rủi ro dài hạn:** Trên chuỗi 2012–2025, `Q2` (GARCH-t + FHS) đạt độ bao phủ **80,3%** (Kupiec $p = 0,94$), và phân biệt được thời kỳ rủi ro cao với độ biến động thực tế gấp **2,56–3,03 lần** thời kỳ rủi ro thấp. |

---

## 4. Danh mục báo cáo chính thức

* **Nhánh dự báo điểm & hướng (Luồng 2):**
  * [Bản trình bày dễ hiểu cho giảng viên](reports/01_point_forecasting/01_TRINH_BAY_DE_HIEU.md)
  * [Báo cáo kỹ thuật & kết quả thực nghiệm M0a–M5, RNN/LSTM](reports/01_point_forecasting/02_BAO_CAO_KY_THUAT_M0_M5_DL.md)
* **Nhánh dự báo khoảng dao động & rủi ro giá (Luồng 3 — Hướng 4):**
  * [Bản trình bày dễ hiểu cho giảng viên (Hướng 4)](reports/02_risk_forecasting/01_TRINH_BAY_DE_HIEU.md)
  * [Bản đặc tả kỹ thuật, pipeline, metric & kết quả đầy đủ (Hướng 4)](reports/02_risk_forecasting/02_DAC_TA_KY_THUAT_VA_KET_QUA.md)
  * [Kế hoạch nghiên cứu Hướng 4](reports/02_risk_forecasting/03_KE_HOACH_NGHIEN_CUU_HUONG_4.md)
* **Định hướng mở rộng:**
  * [Hướng 1: Dự báo tuần/tháng bằng giá kỳ hạn (Swap/Futures)](reports/03_future_directions/HUONG_1_DU_BAO_TUAN_THANG_BANG_GIA_KY_HAN.md)
