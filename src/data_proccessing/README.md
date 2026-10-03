# GÓI XỬ LÝ DỮ LIỆU & QUẢN TRỊ THỜI GIAN SPAFS V5.2 (`src/data_proccessing`)

Package này là tầng nền tảng kỹ nghệ dữ liệu (**Layer 1 – Layer 4**) của hệ thống **SPAFS V5.2**, phụ trách toàn bộ quy trình từ nạp dữ liệu thô (Ingestion), xác thực hợp đồng dữ liệu (Data Contract Validation), quản trị thời gian thực **Point-in-Time (PIT) Control Plane**, kỹ thuật đặc trưng kinh tế lọc dầu (Refining Features), cho đến phân luồng hai mẫu nghiên cứu độc lập.

---

## 📂 1. Cấu Trúc Gói Mã Nguồn & Chức Năng Từng File

```text
src/data_proccessing/
├── __init__.py                 # Khởi tạo package
├── config.py                   # Cấu hình đóng băng, đường dẫn file, mốc thời gian PIT, ngưỡng kiểm toán
├── aliases.py                  # Từ điển ánh xạ tên cột nguồn & tập phân loại biến số (Target vs Feature)
├── model_schemas.py            # Khai báo cấu trúc Schema và danh sách Features Whitelist cho từng mô hình M0 -> M6
├── exceptions.py               # Hệ thống ngoại lệ tùy biến (DataContractViolationError)
├── helpers.py                  # Các hàm tiện ích: làm sạch header, phân giải alias, ép kiểu an toàn, tạo timestamp SGT
├── io.py                       # Các wrapper đọc/ghi an toàn: CSV, Parquet (PyArrow), JSON
├── pipeline.py                 # Bộ điều phối toàn diện (End-to-End Orchestrator) chạy từ Step 01 -> Step 08
├── README.md                   # Tài liệu hướng dẫn gói chính
│
└── data_handling/              # Gói con chứa các bước xử lý dữ liệu chi tiết
    ├── __init__.py
    ├── validate_plats.py       # Gate 1.1: Kiểm toán dữ liệu Platts Mogas 95/92 và Gasoil
    ├── validate_brent.py       # Gate 1.2: Kiểm toán hợp đồng tương lai dầu thô Brent (BZ=F)
    ├── alignment.py            # Gate 1.3: Ghép nối thời gian As-Of Cutoff 08:30 SGT (Canonical Panel)
    ├── target.py               # Step 04: Xây dựng biến mục tiêu lợi suất (r_{t+1}) và hướng giá (y_{t+1})
    ├── market_features.py      # Step 05: Kỹ thuật đặc trưng Spreads, Volatility 30D và Ngưỡng động theta_t
    ├── news_pit.py             # Step 06: Tổng hợp tin tức GDELT / FinBERT theo cửa sổ nhân quả PIT
    ├── patrition.py            # Step 07: Phân chia hai luồng nghiên cứu (Stream 1 Econometrics vs Stream 2 ML)
    ├── weekly.py               # Step 08: Tổng hợp dữ liệu tuần kiểm định tính bền vững theo tần suất
    └── README.md               # Tài liệu chi tiết các bước trong data_handling
```

---

## 📋 2. Chi Tiết Chức Năng Các File Module Cốt Lõi

| Tên File | Chức năng chính | Vai trò trong hệ thống |
| :--- | :--- | :--- |
| [**`config.py`**](file:///D:/Petro_95/src/data_proccessing/config.py) | Định nghĩa dataclass `Config` bất biến (`frozen=True`) và hàm khởi tạo `build_config`. Tự động kiểm tra định dạng ngày (`YYYY-MM-DD`), mốc giờ Cutoff (`08:30 SGT`), giờ đóng phiên Platts (`16:30 SGT`) và giờ sẵn sàng của Brent (`03:30 SGT`). | Loại bỏ hoàn toàn các hằng số ma thuật (magic numbers/strings) rải rác trong code. |
| [**`aliases.py`**](file:///D:/Petro_95/src/data_proccessing/aliases.py) | Đăng ký bảng ánh xạ `ALIASES` cho tất cả các biến thể tên cột từ nhà cung cấp dữ liệu (`Ngày`, `Date`, `Close`, `MG95`, v.v.) và định nghĩa các tập hợp `TARGET_COLUMNS`, `IDENTIFIER_COLUMNS`, `NON_FEATURE_COLUMNS`. | Đảm bảo tính linh hoạt khi định dạng file raw thay đổi mà không cần sửa logic xử lý. |
| [**`model_schemas.py`**](file:///D:/Petro_95/src/data_proccessing/model_schemas.py) | Khai báo cấu trúc Schema chuẩn mực cho từng mô hình $M0a \to M6$ với **Whitelist đặc trưng bất biến**, đảm bảo triệt tiêu rò rỉ biến mục tiêu và loại bỏ hoàn toàn các cột giá danh nghĩa không dừng hoặc cột ngày giờ. Cung cấp hàm `extract_model_matrix(df, model_id)` trích xuất sạch ma trận $(X, y)$. | Đóng vai trò là Single Source of Truth (SSOT) cho toàn bộ Phase 3 (Huấn luyện mô hình) và Phase 4 (Kiểm định thống kê). |
| [**`exceptions.py`**](file:///D:/Petro_95/src/data_proccessing/exceptions.py) | Định nghĩa lớp ngoại lệ chuyên biệt `DataContractViolationError`. | Bắt buộc hệ thống dừng lại ngay lập tức khi phát hiện rò rỉ thông tin hoặc vi phạm dữ liệu (Fail-Fast). |
| [**`helpers.py`**](file:///D:/Petro_95/src/data_proccessing/helpers.py) | Cung cấp các hàm phi trạng thái: `sanitize_column_names` (xóa BOM, chuẩn hóa khoảng trắng), `resolve_column` (tra cứu alias 2 lượt case-insensitive và fuzzy), `parse_numeric`, `parse_timestamp_sgt`, `make_sgt_timestamp` và `save_json`. | Đảm bảo an toàn kiểu dữ liệu, ngăn ngừa lỗi so sánh múi giờ (tz-naive vs tz-aware). |
| [**`io.py`**](file:///D:/Petro_95/src/data_proccessing/io.py) | Cung cấp các hàm wrapper `read_csv`, `write_parquet`, `write_csv` với cơ chế tự động ép kiểu `Path`, tự động tạo thư mục cha và ghi nhật ký logging. | Quản trị lưu trữ có phiên bản cho tầng dữ liệu `interim/` và `processed/`. |
| [**`pipeline.py`**](file:///D:/Petro_95/src/data_proccessing/pipeline.py) | Hàm `run_pipeline(cfg)` kết nối toàn bộ 8 bước từ kiểm toán đến phân chia tập mẫu, xuất file master manifest `pipeline_manifest.json` và `pipeline_manifest.csv`. | Điểm thực thi chính (Entry Point) của toàn bộ quy trình tiền xử lý dữ liệu. |

---

## ⚡ 3. Hướng Dẫn Cách Chạy Toàn Bộ Pipeline (End-to-End)

### Cách 1: Chạy trực tiếp qua Python script hoặc Jupyter Notebook

Chạy toàn bộ pipeline từ đầu đến cuối chỉ với 3 dòng lệnh:

```python
import sys
sys.path.insert(0, r"D:\Petro_95")

from src.data_proccessing.config import build_config
from src.data_proccessing.pipeline import run_pipeline

# 1. Khởi tạo cấu hình mặc định tại thư mục gốc dự án
cfg = build_config(r"D:\Petro_95")

# 2. Thực thi toàn bộ pipeline 8 bước
manifest = run_pipeline(cfg)

# 3. Xem báo cáo tóm tắt
print("Trạng thái pipeline:", manifest["status"])
print("Số dòng các tập dữ liệu:", manifest["row_counts"])
```

### Cách 2: Chạy trực tiếp từ dòng lệnh PowerShell

```powershell
python -X utf8 -c "import sys; sys.path.insert(0, 'D:/Petro_95'); from src.data_proccessing.config import build_config; from src.data_proccessing.pipeline import run_pipeline; manifest = run_pipeline(build_config('D:/Petro_95')); print('Trạng thái:', manifest['status']); print('Kết quả:', manifest['row_counts'])"
```

### Kết quả đầu ra sau khi chạy hoàn tất:
- **Dữ liệu trung gian (`data/interim/`):**
  - `platts_validated.parquet` (4,429 dòng)
  - `brent_continuous.parquet` (4,476 dòng)
  - `canonical_market_panel.parquet` (4,428 dòng)
- **Dữ liệu huấn luyện mô hình (`data/processed/`):**
  - `spafs_full_features_daily.parquet` (4,428 dòng, 47 cột đặc trưng)
  - `stream1_econometric_2008_2025.parquet` (4,428 dòng dành cho RQ1 / M0–M3)
  - `stream2_aligned_nlp_2017_2025.parquet` (2,255 dòng dành cho RQ2 / M4–M6)
  - `weekly_price_robustness.parquet` (922 dòng dành cho kiểm định độ bền vững)
- **Hồ sơ kiểm toán chất lượng (`reports/data_quality/`):**
  - Báo cáo JSON & CSV đầy đủ cho từng bước kiểm toán và file tổng kết `pipeline_manifest.json`.
