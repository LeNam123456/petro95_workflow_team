# 0003. Ưu tiên FHS + GARCH/Quantile Tuyến tính hơn Học máy ở Kỳ hạn dài và Đóng băng Trạng thái Phương sai sau Fit

- **Status**: accepted

## Context & Problem

Khi xây dựng các mô hình dự báo khoảng $Q0\text{–}Q4$, có ba thách thức kỹ thuật và phương pháp luận lớn:
1. Lợi suất xăng MG95 có phân phối đuôi dày (fat tails) và tự tương quan âm nhẹ ở tần suất ngày, khiến công thức nhân $\sqrt{h}$ dưới giả định phân phối chuẩn Gaussian bị lệch tỷ lệ bao phủ ở kỳ hạn 5 và 21 phiên, đặc biệt ở khoảng 95%.
2. Khi chỉ ước lượng lại tham số (`refit`) mỗi 20 phiên để đảm bảo tốc độ tính toán, nếu phương thức dự báo cập nhật và ghi đè trực tiếp trạng thái phương sai nội tại (`self.state`) qua từng bước dự báo, các lần gọi dự báo tiếp theo trong cùng chu kỳ 20 phiên sẽ chạy đệ quy lặp lại trên cùng những dòng dữ liệu cũ, làm phóng đại hoặc bóp méo $\hat{\sigma}$ tới ~50%.
3. Mô hình học máy phi tuyến LightGBM Quantile + Conformal ($Q4$) cần tách 20% cuối cửa sổ huấn luyện (kèm khoảng purge $h$) làm tập hiệu chỉnh conformal, làm giảm số lượng mẫu độc lập ở kỳ hạn tháng và dễ học nhiễu.

## Decision

1. **Chuẩn hóa Filtered Historical Simulation (FHS) có trọng số thời gian (Time-Decayed / Adaptive FHS) qua lớp cơ sở `_ScaleFHS`** cho $Q0, Q1, Q2$: Chuẩn hóa lợi suất $h$ bước trong tập huấn luyện bằng độ biến động dự báo $z_t = y_t / \hat{\sigma}_{h,t}$ (sau giai đoạn burn-in 63 phiên), rồi nhân phân vị thực nghiệm của $z$ với $\hat{\sigma}_{h,\tau}$. Hỗ trợ trọng số suy giảm theo thời gian để thích ứng mượt với giai đoạn yên ả (như Luồng 2: 2023–2025) mà vẫn bảo toàn đuôi dày.
2. **Đóng băng trạng thái phương sai sau `fit` (Immutable Post-Fit State) & Bộ ước lượng GARCH(1,1)-t tự chủ**: Trong `_EwmaVariance` ($Q1$) và `GarchFHS` ($Q2$), bước `.fit()` lưu cứng trạng thái cuối cửa sổ huấn luyện (`fit_state`). Mọi lệnh gọi `.predict_quantiles(X)` đều khởi động lại phép đệ quy từ `fit_state` đã đóng băng mà không bao giờ ghi đè trạng thái này, đảm bảo tính lũy đẳng (idempotency) 100%. Khi thư viện `arch` không có sẵn trong môi trường, hệ thống tự động ước lượng hợp lý cực đại (MLE) GARCH(1,1) phân phối Student-t qua `scipy.optimize.minimize`.
3. **Phân rã Vị trí – Quy mô Có điều kiện (Conditional Location–Scale Decomposition) cho `Q3`**: Nâng cấp `LinearQuantileRegression` (`Q3`) sử dụng căn bậc hai phương sai dự báo $h$ bước của GARCH(1,1)-t làm biến tỷ lệ (Scale) kết hợp với truyền dẫn dầu Brent (cả dấu lẫn độ lớn) và biên lọc dầu làm biến dịch chuyển vị trí (Location), giúp giữ nguyên lợi thế thu hẹp khoảng $-25\%$ ở kỳ hạn ngày đồng thời giảm thiểu hiện tượng trượt dồn cục trong khủng hoảng.
4. **Chọn mô hình vận hành theo kỳ hạn dựa trên bằng chứng thực nghiệm**:
   - Kỳ hạn **1 ngày ($h=1$)** và **1 tuần ($h=5$)**: Dùng **$Q3$ (Location–Scale Linear Quantile Regression)** kết hợp cảnh báo chế độ rủi ro từ **$Q2$ (GARCH(1,1)-t + FHS)**.
   - Kỳ hạn **1 tháng ($h=21$)**: Dùng **$Q2$ (GARCH(1,1)-t + FHS)** làm mô hình chính (bao phủ 80.3%, Kupiec $p = 0.94$, phân biệt rủi ro $2.56\times$), giữ $Q4$ (LightGBM + CQR) làm đối chứng học thuật.

## Consequences

- Triệt tiêu hoàn toàn lỗi tích lũy trạng thái phương sai giữa các kỳ refit (được bảo vệ bởi unit test hồi quy trong `tests/`).
- Giữ mã nguồn `src/models/risk/quantile_models.py` làm một **deep module** duy nhất: bên ngoài chỉ cần gọi `make_risk_model(model_id, horizon)` với 2 phương thức `.fit(X, y)` và `.predict_quantiles(X)`.
