# THƯ MỤC `data_handling` — CÁC BƯỚC XỬ LÝ DỮ LIỆU & ĐẶC TRƯNG SPAFS V5.2

Thư mục này chứa toàn bộ 8 bước xử lý dữ liệu lõi, kỹ thuật đặc trưng và quản trị thời gian **Point-in-Time (PIT)** của hệ thống **SPAFS V5.2**. Mỗi file `.py` đảm nhận một bước chuyên biệt theo nguyên tắc trách nhiệm đơn nhất (Single Responsibility Principle).

---

## 📋 1. Danh mục & Chức năng Từng File Python

| File `.py` | Tên Bước | Chức năng chính | Output sinh ra |
| :--- | :--- | :--- | :--- |
| [**`validate_plats.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/validate_plats.py) | **Gate 1.1** | Kiểm toán hợp đồng dữ liệu Platts Mogas 95/92 và Gasoil; lọc 129 ngày nghỉ lễ có cấu trúc; kiểm tra tính đơn điệu, giá dương; gắn timestamp MOC (16:30 SGT). | `platts_validated.parquet`<br>`platts_audit.csv / .json` |
| [**`validate_brent.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/validate_brent.py) | **Gate 1.2** | Chuẩn hóa hợp đồng tương lai dầu thô Brent (`BZ=F`); tự động nhận diện header Yahoo Finance; tính log return; phát hiện và bảo tồn cú sốc thị trường 2020; khóa mốc sẵn sàng 03:30 SGT. | `brent_continuous.parquet`<br>`brent_audit.csv / .json` |
| [**`alignment.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/alignment.py) | **Gate 1.3** | Thực hiện ghép chuỗi có chiều thời gian **Temporal As-Of Join** (theo Mục 4.6 Blueprint); khóa cứng mốc Cutoff `08:30 SGT`; kiểm tra bất biến `availability <= forecast_origin`. | `canonical_market_panel.parquet`<br>`canonical_panel_audit.csv / .json` |
| [**`target.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/target.py) | **Step 04** | Tính tỷ suất sinh lời logarit trong ngày $r_{t}$ và thiết lập 2 biến mục tiêu phiên tiếp theo: Primary Return $r_{t+1} = \ln(P_{t+1}/P_t) \times 100\%$ và Secondary Direction $y_{t+1} \in \{0, 1\}$. | Bổ sung cột Target vào DataFrame |
| [**`market_features.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/market_features.py) | **Step 05** | Tạo các đặc trưng kinh tế lọc dầu: Octane Spread ($95-92$), Diesel Spread ($95-DO$), Crack Margin ($95-Brent$), mỏ neo trễ $(95-Brent)_{t-1}$, cú sốc bất đối xứng ($r^+, r^-$), biến động 30 ngày và ngưỡng động $\theta_t$. | Bổ sung 47 cột đặc trưng thị trường |
| [**`news_pit.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/news_pit.py) | **Step 06** | Gom tin tức tài chính (GDELT, FinBERT, Native Tone, Goldstein) vào đúng cửa sổ nhân quả $(t_{origin, t-1}, t_{origin, t}]$, ngăn chặn $100\%$ rò rỉ tin sau 08:30 SGT. | Bổ sung các biến News Sentiment |
| [**`patrition.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/patrition.py) | **Step 07** | Thực thi khung nghiên cứu hai mẫu: Luồng 1 kinh tế lượng (2008–2025, $N=4,428$) và Luồng 2 học máy (2017–2025, chia Train $N=748$ và OOS Test $N=1,507$). Kiểm tra Feature Contract. | `stream1_econometric_2008_2025.parquet`<br>`stream2_aligned_nlp_2017_2025.parquet`<br>`partition_audit.csv / .json` |
| [**`weekly.py`**](file:///D:/Petro_95/src/data_proccessing/data_handling/weekly.py) | **Step 08** | Tổng hợp chuỗi dữ liệu theo tần suất tuần (kết thúc Chủ Nhật, $N \approx 900$) phục vụ kiểm định độ bền vững theo tần suất thời gian (Temporal Aggregation Robustness). | `weekly_price_robustness.parquet`<br>`weekly_audit.csv / .json` |

---

## 🚀 2. Hướng Dẫn Cách Chạy (Execution Guide)

### Cách 1: Chạy từng bước độc lập (Unit / Debug Execution)

Bạn có thể mở PowerShell hoặc terminal tại thư mục gốc `D:\Petro_95` và chạy từng bước kiểm thử bằng Python:

```python
import sys
sys.path.insert(0, r"D:\Petro_95")

from src.data_proccessing.config import build_config
from src.data_proccessing.data_handling.validate_plats import validate_platts
from src.data_proccessing.data_handling.validate_brent import validate_brent
from src.data_proccessing.data_handling.alignment import build_canonical_panel
from src.data_proccessing.data_handling.target import add_returns_and_targets
from src.data_proccessing.data_handling.market_features import build_market_features

cfg = build_config(r"D:\Petro_95")

# 1. Chạy Gate 1.1 Platts
platts, audit_platts = validate_platts(cfg)

# 2. Chạy Gate 1.2 Brent
brent, audit_brent = validate_brent(cfg)

# 3. Chạy Gate 1.3 As-Of Alignment
canonical, audit_canonical = build_canonical_panel(platts, brent, cfg)

# 4. Chạy Step 04 Targets
df_targets = add_returns_and_targets(canonical, cfg)

# 5. Chạy Step 05 Market Features
df_features = build_market_features(df_targets, cfg)
```

### Cách 2: Chạy kiểm tra nhanh qua dòng lệnh PowerShell

```powershell
# Chạy kiểm thử Gate 1.1 Platts
python -c "import sys; sys.path.insert(0, 'D:/Petro_95'); from src.data_proccessing.config import build_config; from src.data_proccessing.data_handling.validate_plats import validate_platts; print(validate_platts(build_config('D:/Petro_95'))[1])"

# Chạy kiểm thử Gate 1.2 Brent
python -c "import sys; sys.path.insert(0, 'D:/Petro_95'); from src.data_proccessing.config import build_config; from src.data_proccessing.data_handling.validate_brent import validate_brent; print(validate_brent(build_config('D:/Petro_95'))[1])"

# Chạy kiểm thử Gate 1.3 As-Of Alignment
python -c "import sys; sys.path.insert(0, 'D:/Petro_95'); import pandas as pd; from src.data_proccessing.config import build_config; from src.data_proccessing.data_handling.alignment import build_canonical_panel; cfg = build_config('D:/Petro_95'); print(build_canonical_panel(pd.read_parquet(cfg.interim_dir / 'platts_validated.parquet'), pd.read_parquet(cfg.interim_dir / 'brent_continuous.parquet'), cfg)[1])"
```
