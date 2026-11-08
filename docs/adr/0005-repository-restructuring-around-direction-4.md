# 0005. Tái cấu trúc Kho mã nguồn (Repository Layout) xoay quanh Hướng 4 và Kiến trúc Deep Modules

- **Status**: accepted

## Context & Problem

Qua nhiều giai đoạn phát triển từ Phase 1 đến mở rộng đa kỳ hạn và Hướng 4, thư mục gốc của dự án (`d:\Petro_95`) từng bị phân mảnh bởi nhiều tệp script tiện ích một lần, nhiều tệp notebook rời, và các báo cáo nằm rải rác. Đồng thời, các tệp đánh giá cũ trùng lặp (`src/models/evaluation/metrics.py`, `pairwise.py`, `src/models/purging_and_embargo_partition.py`) cần được loại bỏ hoàn toàn.

## Decision

Tổ chức lại dự án theo cấu trúc 3 luồng thực thi chuẩn hóa (điều phối qua [`run_pipeline.py`](../../run_pipeline.py)), lấy **Hướng 4 (Multi-Horizon Interval & Risk Forecasting)** kết hợp nền tảng dữ liệu PIT SPAFS V5.2 làm trục chính:

1. **`docs/` (Tầng Quản trị Kiến trúc & Ngữ nghĩa Miền)**:
   - `docs/GLOSSARY.md` (đồng bộ tại `GLOSSARY.md` ở gốc): Từ điển thuật ngữ miền chuẩn hóa duy nhất.
   - `docs/adr/`: Lưu trữ toàn bộ các quyết định kiến trúc (`0001`–`0005`).
   - `docs/agents/`: Cấu hình cho hệ thống kỹ năng AI (`issue-tracker.md`, `domain.md`, `triage-labels.md`), được liên kết từ `AGENTS.md` ở thư mục gốc.
2. **`src/` (Tầng Mã nguồn Sản xuất theo nguyên lý Deep Modules)**:
   - `src/data_proccessing/`: Pipeline dữ liệu 8 bước, kiểm toán tính dừng (`stationarity_audit.py`) và kiểm soát Point-in-Time 08:30 SGT (`audit_record_level_pit.py`).
   - `src/models/validation/walk_forward.py`: Engine Walk-Forward duy nhất cho cả dự báo điểm và phân vị (`Purge = h`, `Embargo = E`).
   - `src/models/risk/`: Trọng tâm Hướng 4 (`quantile_models.py` cho $Q0\text{–}Q4$, `figures.py` cho biểu đồ quạt và hiệu chỉnh).
   - `src/models/evaluation/`: Hợp nhất kiểm định dự báo điểm (`forecast_tests.py`, `hypothesis.py`) và kiểm định khoảng/rủi ro (`interval_tests.py` gồm Kupiec, Christoffersen, Conditional Coverage $LR_{cc}$, Mincer–Zarnowitz $R^2$, Tail VaR và Unified Multi-Horizon Decision Card).
   - `src/models/runner_risk_multi_horizon.py`: Điểm vào chuẩn để tái lập toàn bộ kết quả Hướng 4.
3. **`reports/` & `artifacts/risk/` (Tầng Báo cáo Phân nhánh & Kết quả Thực nghiệm)**:
   - `reports/README.md`: Mục lục trung tâm điều hướng toàn bộ báo cáo.
   - `reports/01_point_forecasting/`: Báo cáo nhánh dự báo điểm & hướng ($M0a\text{–}M5$, RNN/LSTM).
   - `reports/02_risk_forecasting/`: Báo cáo trung tâm của Hướng 4 (`01_TRINH_BAY_DE_HIEU.md`, `02_DAC_TA_KY_THUAT_VA_KET_QUA.md`, `03_KE_HOACH_NGHIEN_CUU_HUONG_4.md`), liên kết trực tiếp với `artifacts/risk/{stream1,stream2,figures}/`.
   - `reports/03_future_directions/`: Định hướng mở rộng dữ liệu kỳ hạn (`HUONG_1_DU_BAO_TUAN_THANG_BANG_GIA_KY_HAN.md`).
4. **`notebooks/` (Tầng Khám phá Dữ liệu)**:
   - Quy hoạch 5 tệp `.ipynb` đánh số thứ tự `01` đến `05` trong `notebooks/`.

## Consequences

- Thư mục gốc (`root`) tối giản và sạch sẽ, chỉ giữ lại `run_pipeline.py`, `README.md`, `AGENTS.md`, `GLOSSARY.md` và các thư mục cấp cao (`data/`, `src/`, `reports/`, `artifacts/`, `notebooks/`, `docs/`, `tests/`).
- Toàn bộ 83/83 kiểm thử tự động trong `tests/` chạy xanh 100%, đảm bảo tính toàn vẹn toán học và khả năng tái lập.
