# 0004. Đánh giá Kép trên Hai Luồng Dữ liệu (Stream 2 & Stream 1) và Lấy mẫu Không chồng lấp cho Kiểm định Khoảng

- **Status**: accepted

## Context & Problem

1. **Bẫy thời kỳ yên ả trên Luồng 2 (2023–2025)**: Giai đoạn kiểm tra chính của Luồng 2 (28/12/2022 – 29/12/2025) diễn ra sau khi cú sốc COVID-19 (2020) và xung đột Nga–Ukraine (2022) đã đi qua. Do cửa sổ huấn luyện (2017–2022) chứa hai cuộc khủng hoảng lớn còn giai đoạn kiểm tra lại khá êm đềm, mặt bằng biến động lịch sử cao hơn thực tế 2023–2025 và chênh lệch rủi ro giữa các tháng trong 2023–2025 rất nhỏ. Nếu chỉ báo cáo Luồng 2, người đọc sẽ kết luận sai rằng mô hình không phân biệt được giai đoạn rủi ro cao/thấp ở kỳ hạn tuần và tháng.
2. **Tự tương quan cơ học của chuỗi trượt chồng lấp**: Ở kỳ hạn tuần ($h=5$) và tháng ($h=21$), hai phiên dự báo liên tiếp chia sẻ $h-1$ ngày giao dịch chung. Một cú sốc lớn đơn lẻ sẽ làm lợi suất trượt khỏi khoảng dự báo trong nhiều ngày liên tiếp, khiến kiểm định Kupiec và đặc biệt là kiểm định tính độc lập Christoffersen bác bỏ sai (false rejection) nếu chạy trên toàn bộ các mốc ngày.

## Decision

1. **Bắt buộc báo cáo song song hai bộ đánh giá trong Hướng 4**:
   - **Stream 2 (Primary Window, OOS 2023–2025, ~750 mốc)**: Dùng để so sánh đồng nhất trên cùng mặt bằng thời gian với các mô hình dự báo điểm $M0a\text{–}M5$ và RNN/LSTM.
   - **Stream 1 (Long-Horizon Robustness Window, OOS 2012–2025, ~3,500 mốc)**: Bao gồm đầy đủ các chu kỳ khủng hoảng giá dầu 2014–2015, đại dịch 2020 và cú sốc 2022 để kiểm chứng khách quan câu hỏi RQ4a (hiệu chỉnh 80.3–81.1%) và RQ4c (nhóm rủi ro cao biến động gấp $2.1\text{–}3.4\times$ nhóm rủi ro thấp).
2. **Lấy mẫu không chồng lấp (bước nhảy $h$: `hits[::horizon]`) cho bộ ba kiểm định Kupiec ($LR_{uc}$), Christoffersen độc lập ($LR_{ind}$) và Christoffersen bao phủ có điều kiện ($LR_{cc} = LR_{uc} + LR_{ind} \sim \chi^2_2$)**, trong khi vẫn tính Coverage, Width, Tail VaR ($q_{0.025}, q_{0.05}, q_{0.95}, q_{0.975}$), Mincer–Zarnowitz $R^2$ và Pinball Loss trên toàn bộ các mốc dự báo kèm kiểm định Diebold–Mariano hiệu chỉnh phương sai Newey–West HAC với $h - 1$ độ trễ.
3. **Xếp hạng nhãn rủi ro hoàn toàn tiền nghiệm (`_expanding_rank` có hỗ trợ `history_seed` và cửa sổ trượt 252 phiên)**: Ngưỡng phân vị 25% / 75% để gắn nhãn rủi ro Thấp / Cao tại mốc $\tau$ được khởi tạo từ lịch sử quá khứ trước mốc OOS đầu tiên (hoặc cửa sổ trượt 252 phiên giao dịch), giúp không bị mất nhãn ở 60 phiên OOS đầu tiên và phản ánh trung thực mặt bằng rủi ro lịch sử.
4. **Xuất Bảng Quyết định Tích hợp Đa kỳ hạn (Unified Multi-Horizon Decision Card)**: Tổng hợp dự báo điểm/hướng ngắn hạn ($M2$) với khoảng 80%/95%, $P(\text{tăng})$, Upside/Downside Tail Risk và Nhãn chế độ rủi ro cho cả 3 kỳ hạn (1 ngày, 1 tuần, 1 tháng).

## Consequences

- Bảo vệ tính chặt chẽ thống kê của các kiểm định khoảng ở kỳ hạn dài trước phản biện học thuật.
- Cung cấp bức tranh trung thực về hành vi của mô hình trong cả chế độ thị trường bình lặng (2023–2025) lẫn chế độ khủng hoảng (2012–2025).
