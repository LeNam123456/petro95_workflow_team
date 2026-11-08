# 0001. Chuyển trọng tâm đa kỳ hạn sang Dự báo Khoảng dao động và Rủi ro (Hướng 4)

- **Status**: accepted

## Context & Problem

Kết quả thực nghiệm ngoài mẫu (OOS) nghiêm ngặt của hệ thống dự báo điểm ($M0a\text{–}M5$ và RNN/LSTM) cho thấy:
1. Ở kỳ hạn **1 ngày ($h = 1$)**, mô hình hồi quy động tuyến tính có biến dầu thô Brent dẫn dắt qua đêm ($M2, M3$) dự báo tốt cả biên độ lẫn hướng biến động (giảm ~39.8% sai số so với mốc ngây thơ, đúng hướng ~70–71.5%).
2. Tuy nhiên, ở kỳ hạn **1 tuần ($h = 5$)** và **1 tháng ($h = 21$)**, lợi suất kỳ vọng có điều kiện gần như không thể dự báo bằng dữ liệu giá giao ngay và tin tức hiện có (cải thiện ở kỳ hạn tuần chỉ ~4.6% và âm ở kỳ hạn tháng do nhiễu tích lũy và thiếu dữ liệu đường cong kỳ hạn futures/swaps).

Nếu tiếp tục ép các mô hình học máy phức tạp dự báo hướng giá ở kỳ hạn tuần/tháng, dự án sẽ rơi vào bẫy học nhiễu (overfitting) mà không mang lại giá trị sử dụng thực tế.

## Decision

Tái định hình kiến trúc nghiên cứu và sản phẩm dự báo của dự án theo **Hướng 4 (Multi-Horizon Interval & Risk Forecasting)**:
1. **Giữ nguyên dự báo điểm/hướng ở kỳ hạn 1 ngày ($h = 1$)** nơi tín hiệu truyền dẫn từ ICE Brent sang Platts Mogas 95 có ý nghĩa thống kê và kinh tế mạnh mẽ.
2. **Chuyển mục tiêu chính ở cả 3 kỳ hạn ($h \in \{1, 5, 21\}$) sang dự báo phân phối có điều kiện (9 phân vị)** với 3 đầu ra vận hành:
   - **Prediction Interval (Khoảng dự báo 80% và 95%)**
   - **Probability of Increase ($P(\text{tăng})$)**
   - **Ex-Ante Risk Regime (Nhãn mức rủi ro Thấp / Trung bình / Cao)**
3. Xây dựng thang 5 mô hình định lượng rủi ro từ cơ sở đến nâng cao: $Q0$ (Historical Simulation), $Q1$ (EWMA + FHS), $Q2$ (GARCH(1,1)-t + FHS), $Q3$ (Linear Quantile Regression với biến Brent & Spread), và $Q4$ (LightGBM Quantile Regression + Conformal Calibration).

## Consequences

- Giải quyết trọn vẹn bài toán thực tiễn cho doanh nghiệp nhập khẩu xăng dầu (lập ngân sách phòng vệ theo kịch bản xấu 95%) và cơ quan điều hành (cảnh báo sớm thời kỳ biến động cao để chuẩn bị Quỹ bình ổn giá) mà không cần mua thêm dữ liệu phái sinh đắt đỏ.
- Thống nhất câu chuyện khoa học xuyên suốt toàn dự án: *Ngắn hạn (1 ngày) dự báo được cả hướng lẫn biên độ nhờ độ trễ múi giờ Brent–Singapore; trung hạn (1 tuần, 1 tháng) hướng giá là bước đi ngẫu nhiên nhưng phương sai và biên độ rủi ro có tính dồn cục (volatility clustering) nên dự báo chính xác được.*
