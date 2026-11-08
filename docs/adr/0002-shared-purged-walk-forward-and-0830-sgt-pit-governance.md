# 0002. Khóa cứng Cutoff 08:30 SGT và Dùng chung Engine Walk-Forward có Purge/Embargo

- **Status**: accepted

## Context & Problem

Dự báo tài chính đa thị trường (London/New York ICE Brent và Singapore Platts MOC) và đa kỳ hạn ($h \in \{1, 5, 21\}$) rất dễ mắc hai lỗi rò rỉ dữ liệu tương lai (lookahead bias) nghiêm trọng:
1. Ghép nhầm giá đóng cửa Brent cùng ngày lịch dương $D_{t+1}$ (chốt lúc 02:30–03:30 SGT sáng ngày $D_{t+2}$) vào dự báo phiên chiều Singapore $D_{t+1}$ (16:30 SGT).
2. Khi đánh giá Walk-Forward cho kỳ hạn $h > 1$, nếu huấn luyện mô hình tại mốc $\tau$ trên các dòng $t > \tau - h$, nhãn mục tiêu $r_{t,h} = \sum_{j=1}^h r_{t+j}$ sẽ chứa thông tin giá sau thời điểm $\tau$. Ngoài ra, nếu tách rời vòng lặp đánh giá giữa mô hình dự báo điểm và mô hình dự báo khoảng, quy tắc cắt mẫu rất dễ bị lệch nhau.

## Decision

1. **Point-in-Time Cutoff bất biến tại $\tau = \text{08:30 SGT}$ sáng ngày dự báo**: Mọi đặc trưng đầu vào (bao gồm lợi suất Brent đêm qua, các Refining Spreads và độ biến động trượt) phải khả dụng trước 08:30 SGT. Vi phạm quy tắc này trong pipeline dữ liệu sẽ kích hoạt `DataContractViolationError` dừng hệ thống ngay lập tức.
2. **Dùng chung một vòng lặp Walk-Forward (`_walk_forward` trong `src/models/validation/walk_forward.py`)** cho cả `run_walk_forward_evaluation` (dự báo điểm $M0a\text{–}M5$) và `run_walk_forward_quantiles` (dự báo phân vị $Q0\text{–}Q4$).
3. **Bắt buộc Purge $h$ phiên và Embargo $E$ phiên ($E \in \{0, 2, 5\}$ cho $h \in \{1, 5, 21\}$)**: Tại mốc dự báo $\tau$, mô hình chỉ được phép `fit` trên các dòng $t \le \tau - h - E$. Giữa hai lần `refit` (mỗi 20 phiên), hàm dự báo nhận toàn bộ chuỗi đặc trưng $X$ từ `train_end + 1` đến $\tau$ (vì đặc trưng tại $t \le \tau$ đã biết, chỉ có nhãn $h$ bước là chưa hiện thực hóa) để các mô hình có trạng thái (ARMA, EWMA, GARCH) cập nhật bộ lọc phương sai/trạng thái hợp lệ mà không rò rỉ nhãn.

## Consequences

- Đảm bảo tính công bằng và khả năng so sánh 1-1 tuyệt đối giữa các nhánh mô hình điểm và mô hình khoảng trên cùng một giao thức thời gian thực.
- Mọi mô hình phân vị mới đều phải tuân thủ giao diện `.fit(X, y)` và `.predict_quantiles(X)` nhận các dòng nối tiếp ngay sau cửa sổ huấn luyện.
