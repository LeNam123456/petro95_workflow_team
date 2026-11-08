# Danh Mục Báo Cáo Dự Án SPAFS V5.2 (Trọng Tâm Hướng 4)

Thư mục này lưu trữ các báo cáo phân tích thực nghiệm, đặc tả phương pháp luận và biên bản kiểm toán chất lượng dữ liệu của dự án **SPAFS V5.2**, được phân chia thành 3 nhánh rõ ràng.

## 1. Trọng Tâm Nghiên Cứu: Hướng 4 — Dự Báo Khoảng Dao Động & Rủi Ro Đa Kỳ Hạn (`02_risk_forecasting/`)

1. **[`02_risk_forecasting/01_TRINH_BAY_DE_HIEU.md`](./02_risk_forecasting/01_TRINH_BAY_DE_HIEU.md)** *(Bản trình bày trực quan cho giảng viên & hội đồng)*:
   - Tóm tắt toàn bộ câu chuyện nghiên cứu của Hướng 4 ($Q0\text{–}Q4$) bằng ngôn ngữ dễ hiểu, trực quan kèm biểu đồ quạt (Fan Chart), biểu đồ hiệu chỉnh (Coverage 80%) và khả năng báo trước giai đoạn rủi ro cao ($2.1\text{–}3.4\times$).
2. **[`02_risk_forecasting/02_DAC_TA_KY_THUAT_VA_KET_QUA.md`](./02_risk_forecasting/02_DAC_TA_KY_THUAT_VA_KET_QUA.md)** *(Bản đặc tả kỹ thuật, công thức & kết quả đầy đủ)*:
   - Toàn bộ công thức toán học của 5 mô hình $Q0\text{–}Q4$, bộ kiểm định Kupiec ($LR_{uc}$), Christoffersen ($LR_{ind}$), Conditional Coverage ($LR_{cc}$), Pinball Loss, Diebold–Mariano (HLN HAC) và đối chiếu học thuật quốc tế.
3. **[`02_risk_forecasting/03_KE_HOACH_NGHIEN_CUU_HUONG_4.md`](./02_risk_forecasting/03_KE_HOACH_NGHIEN_CUU_HUONG_4.md)** *(Đề cương thiết kế Hướng 4)*:
   - Động cơ chuyển dịch từ dự báo điểm sang dự báo khoảng ở kỳ hạn tuần/tháng và hệ thống câu hỏi nghiên cứu `RQ4a`–`RQ4d`.

## 2. Báo Cáo Dự Báo Điểm & Hướng Giá (`01_point_forecasting/`)

- **[`01_point_forecasting/01_TRINH_BAY_DE_HIEU.md`](./01_point_forecasting/01_TRINH_BAY_DE_HIEU.md)**: Bản giải thích trực quan về hệ thống mô hình điểm $M0a \to M5$ và mạng nơ-ron sâu RNN/LSTM.
- **[`01_point_forecasting/02_BAO_CAO_KY_THUAT_M0_M5_DL.md`](./01_point_forecasting/02_BAO_CAO_KY_THUAT_M0_M5_DL.md)**: Đặc tả kỹ thuật, kiểm định Wald bất đối xứng (RQ1), Clark–West / Diebold–Mariano (RQ2) và bảng kết quả đa kỳ hạn.

## 3. Định Hướng Mở Rộng & Kiểm Toán Chất Lượng Dữ Liệu

- **[`03_future_directions/HUONG_1_DU_BAO_TUAN_THANG_BANG_GIA_KY_HAN.md`](./03_future_directions/HUONG_1_DU_BAO_TUAN_THANG_BANG_GIA_KY_HAN.md)**: Định hướng tích hợp dữ liệu đường cong kỳ hạn (Futures/Swaps) cho dự báo hướng trung hạn.
- **[`data_quality/`](./data_quality/)**: Hồ sơ kiểm toán hợp đồng dữ liệu (Data Contract Gates 1.1–1.3), kiểm toán Point-in-Time từng bản ghi và kiểm định tính dừng ADF/KPSS định dạng JSON/CSV.
