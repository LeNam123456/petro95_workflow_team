# SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)
## Dự Báo Tỷ Suất Thay Đổi & Hướng Biến Động Chuẩn Giá Platts FOB Singapore Mogas 95

Hệ thống mã nguồn thực nghiệm và tầng dữ liệu chuẩn mực cho đề tài dự báo giá xăng thành phẩm bán buôn Singapore (**Platts FOB Singapore MG95**) kết hợp mô hình kinh tế lượng phân tách cú sốc bất đối xứng (**RQ1 - Asymmetric ADL**) và học máy bảng ngoài mẫu (**RQ2 - Walk-Forward LightGBM & NLP Tín hiệu Thông tin**).

---

### 📂 1. Cấu Trúc Thư Mục Dự Án

```text
Petroleum_95/
├── data/
│   ├── raw/                                 # Dữ liệu gốc bất biến
│   │   ├── price_petroleum_platts.csv       # Chuỗi Platts 2008-2025 gốc (4,559 dòng)
│   │   └── brent_crude_daily.csv            # Chuỗi ICE Brent Futures (BZ=F) gốc (4,476 dòng)
│   ├── interim/                             # Tầng dữ liệu trung gian chuẩn hóa (Parquet artifacts)
│   │   ├── platts_validated.parquet         # Platts sạch đã vượt qua Data Contract Gate 1.1
│   │   ├── brent_continuous.parquet         # Brent đã xử lý roll hợp đồng
│   │   └── canonical_market_panel.parquet   # Bảng dữ liệu hợp nhất 5-timestamp PIT
│   └── processed/                           # Tầng dữ liệu phục vụ trực tiếp downstream
│       ├── spafs_full_features_daily.parquet# Bộ đặc trưng 4,428 ngày giao dịch hoàn chỉnh
│       ├── stream1_econometric_2008_2025.parquet # Mẫu toàn vẹn cho M0-M3 & RQ1 (N = 4,428)
│       ├── stream2_aligned_nlp_2017_2025.parquet # Mẫu đối chứng cho M4-M6 & RQ2 (N = 2,255)
│       └── weekly_price_robustness.parquet  # Dữ liệu tuần kiểm tra độ bền vững tần suất
│
├── reports/
│   └── data_quality/                        # Hồ sơ kiểm toán chất lượng dữ liệu
│       ├── platts_audit.json / .csv         # Báo cáo kiểm toán Data Contract Gate 1.1
│       ├── brent_audit.json / .csv          # Báo cáo kiểm toán dữ liệu Brent Gate 1.2
│       ├── canonical_panel_audit.json / .csv# Báo cáo kiểm toán ghép nối PIT Gate 1.3
│       ├── partition_audit.json / .csv      # Báo cáo kiểm toán phân chia hai luồng mẫu
│       ├── weekly_audit.json / .csv         # Báo cáo kiểm toán dữ liệu tuần
│       └── pipeline_manifest.json / .csv    # Báo cáo tổng thể toàn bộ pipeline
│
├── src/
│   └── data_proccessing/                    # Gói kỹ nghệ dữ liệu & quản trị PIT
│       ├── config.py                        # Cấu hình đóng băng, đường dẫn, mốc giờ PIT
│       ├── aliases.py                       # Bảng ánh xạ tên cột & whitelist đặc trưng
│       ├── model_schemas.py                 # Khai báo schema chuẩn mực cho M0 -> M6
│       ├── exceptions.py                    # Ngoại lệ DataContractViolationError
│       ├── helpers.py                       # Tiện ích chuẩn hóa tên, parsing, timestamp SGT
│       ├── io.py                            # Wrapper đọc/ghi Parquet/CSV an toàn
│       ├── pipeline.py                      # Bộ điều phối toàn diện Step 01 -> Step 08
│       ├── README.md                        # Hướng dẫn chi tiết package data_proccessing
│       └── data_handling/                   # Các module xử lý dữ liệu chi tiết
│           ├── validate_plats.py            # Kiểm toán Platts Mogas 95/92 và Gasoil
│           ├── validate_brent.py            # Kiểm toán hợp đồng tương lai Brent
│           ├── alignment.py                 # Ghép nối As-Of Cutoff 08:30 SGT
│           ├── target.py                    # Xây dựng biến mục tiêu r_{t+1} và y_{t+1}
│           ├── market_features.py           # Spreads, Volatility 30D, Ngưỡng động
│           ├── news_pit.py                  # Tổng hợp tin tức theo cửa sổ PIT
│           ├── patrition.py                 # Phân chia hai luồng nghiên cứu
│           └── weekly.py                    # Tổng hợp chuỗi tuần robustness
│
├── SPAFS_V5_2_BLUEPRINT_AND_SYSTEM_SPECIFICATION.md # Bản đặc tả kiến trúc toàn diện V5.2
└── .gitignore                               # Loại trừ file notebook (.ipynb) và cache
```

---

### ⚡ 2. Hướng Dẫn Chạy Pipeline Dữ Liệu

Chạy toàn bộ pipeline kiểm toán dữ liệu từ đầu đến cuối:

```powershell
python -X utf8 -c "import sys; sys.path.insert(0, '.'); from src.data_proccessing.config import build_config; from src.data_proccessing.pipeline import run_pipeline; manifest = run_pipeline(build_config('.')); print('Trạng thái:', manifest['status']); print('Kết quả:', manifest['row_counts'])"
```

Hoặc qua Python:

```python
from src.data_proccessing.config import build_config
from src.data_proccessing.pipeline import run_pipeline

cfg = build_config(".")
manifest = run_pipeline(cfg)
print(manifest["status"])
```

---

### 📑 3. Tài Liệu Chi Tiết

Xem bản đặc tả chi tiết toàn diện về phương pháp luận, kinh tế lượng, mô hình máy học và kết quả kiểm định tại:
👉 [SPAFS_V5_2_BLUEPRINT_AND_SYSTEM_SPECIFICATION.md](SPAFS_V5_2_BLUEPRINT_AND_SYSTEM_SPECIFICATION.md)
