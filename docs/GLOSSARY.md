# GLOSSARY.md — Thuật ngữ Dự án Mogas 95

Tài liệu định nghĩa từ vựng chuẩn (Ubiquitous Language) của repository `Petro_95`. Phần 1 là ngôn ngữ chuẩn mực của nhánh hiện tại `feature/traditional-deep-learning-pipeline`. Phần 2 là di sản của dự án cũ SPAFS V5.2 để tham chiếu lịch sử.

---

# PHẦN 1: TRADITIONAL FORECASTING PIPELINE (REVISED MVP — ACTIVE)
*Tài liệu đặc tả chi phối: `docs/PROBLEM_DEFINITION_AND_METHODOLOGY_REVISED.md`*

## 1. Dữ liệu & Quản trị Thời gian (Data & Point-in-Time Governance)

**Forecast Origin ($o$ / 08:30 SGT Cutoff)**:
Mốc thời gian phát lệnh dự báo chuẩn lúc 08:30 sáng giờ Singapore (`Asia/Singapore`, UTC+8). Mọi thông tin đầu vào phải được công bố và khả dụng trước mốc này ($\text{feature\_available\_at} \le \text{forecast\_origin}$).
_Avoid_: Giờ chốt phiên Mogas (16:30 SGT), giờ đóng cửa cuối ngày, thời điểm chạy script thực tế.

**Point-in-Time (PIT) Rule**:
Ràng buộc thời gian bắt buộc: chỉ sử dụng thông tin đã thực sự khả dụng tại thời điểm phát sinh dự báo. Pipeline chỉ được công nhận Zero Lookahead Bias khi vượt qua automated PIT check có lưu metadata.
_Avoid_: Ghép dữ liệu chỉ dựa trên ngày lịch mà bỏ qua độ trễ công bố (Calendar-only alignment).

**Canonical Market Panel**:
Tệp dữ liệu sạch nguồn bất biến (`data/interim/canonical_market_panel.parquet`, 4,428 phiên giao dịch từ 2008–2025, 0 missing values), kết hợp giá Platts Mogas 95 (`MG95`) và Dầu thô Brent (`brent_close`).
_Avoid_: Tự ý sửa đổi, ghi đè hoặc xáo trộn thứ tự thời gian của tệp dữ liệu gốc.

**Sequential 70/15/15 Split**:
Phương thức phân chia chuỗi thời gian tuần tự không xáo trộn: 70% Train (3,099 dòng, 2008–2020), 15% Validation (664 dòng, 2021–2023), 15% Test (665 dòng, 2023–2025) theo ADR-0006. Tên tệp mang tính đại diện giai đoạn thị trường.
_Avoid_: Random K-fold CV, Shuffled Split.

**Lookback Window ($L=30$)**:
Cửa sổ lịch sử gồm đúng 30 phiên giao dịch gần nhất khả dụng tính đến thời điểm $o$. Cho phép lấy tối đa 29 phiên của cuối partition trước làm context lịch sử cho các mẫu đầu của Validation và Test mà không vi phạm PIT.
_Avoid_: Cắt bỏ máy móc 29 dòng đầu của Val/Test, Lookback linh hoạt không cố định trong MVP.

## 2. Mục tiêu Dự báo & Biểu diễn (Target Representation)

**Relative Change ($R_{o,h}$ — Phương pháp chính)**:
Tỷ lệ biến động tương đối tích lũy từ mức giá Mogas gần nhất tại forecast origin đến mức giá ở kỳ hạn $h$:
$$R_{o,h} = \frac{P^M_{o+h} - P^M_o}{P^M_o}$$
_Avoid_: Log-return ($\ln(P_{t+h}/P_t)$), chênh lệch giá tuyệt đối thô ($P_{t+h} - P_t$).

**Local Window Normalization ($z^{(j)}_{o,k}$)**:
Phương pháp chuẩn hóa cục bộ từng chuỗi đầu vào theo chính giá trị gần nhất khả dụng của nó tại origin:
$$z^{(j)}_{o,k} = \frac{P^{(j)}_{o-k}}{P^{(j)}_o} - 1 \quad (k=0, \dots, L-1)$$
Giúp triệt tiêu xu thế trôi giá, ngăn ngừa hoàn toàn bão hòa đạo hàm tại các cổng Tanh/Sigmoid của LSTM/GRU.
_Avoid_: Global MinMaxScaler tính trên toàn tập mà không có cơ chế thích ứng biến động ngoài Train.

**Price Level ($y_{o,h} = P^M_{o+h}$ — Ablation đối chứng)**:
Dự báo trực tiếp mức giá danh nghĩa trong tương lai, sử dụng scaler fit độc quyền trên tập Train, không clipping tập Test.
_Avoid_: Coi Price Level là phương pháp chính của đề tài.

**Target Reconstruction (Tái lập mức giá)**:
Công thức khôi phục giá dự báo về đơn vị chuẩn USD/thùng từ tỷ lệ biến động tương đối:
$$\hat{P}^M_{o+h} = P^M_o (1 + \hat{R}_{o,h})$$
_Avoid_: Tính toán sai số MAE/RMSE trực tiếp trên không gian phần trăm mà chưa tái lập về USD/thùng.

## 3. Kiến trúc Đa kỳ hạn & Mô hình (Strategy & Models)

**Direct Multi-Horizon Strategy**:
Chiến lược dự báo trực tiếp: huấn luyện mô hình độc lập cho từng kỳ hạn riêng rẽ ($h \in \{1, 5, 21\}$).
_Avoid_: Mô hình Joint/MIMO đa đầu ra trong phạm vi MVP (tránh nhiễu kỳ hạn dài $h=21$ chi phối loss của $h=1$).

**Naive Persistence Baseline**:
Mô hình đường cơ sở bắt buộc: dự báo mức giá tương lai tại $o+h$ bằng chính mức giá gần nhất khả dụng tại $o$: $\hat{P}^M_{o+h} = P^M_o$. Mọi mô hình ML/DL đều phải so sánh trực tiếp với benchmark này.
_Avoid_: Moving Average đơn giản, Random Walk không mốc neo.

**Directional Accuracy (DA)**:
Tỷ lệ phần trăm dự báo đúng chiều hướng tăng/giảm so với phiên $t$ hiện tại, tính theo hàm dấu 3 trạng thái $\operatorname{sgn}(\Delta P) \in \{-1, 0, 1\}$. Nếu thực tế đứng giá ($\Delta P = 0$), dự báo chỉ đúng khi mô hình cũng dự báo đứng giá.
_Avoid_: Giả định ngầm ngưỡng 50% là ngẫu nhiên đối với phân phối không cân bằng, thay đổi quy tắc tính sau khi xem tập Test.

---

# PHẦN 2: SPAFS V5.2 (LEGACY — CHỈ ĐỂ THAM CHIẾU LỊCH SỬ)
> [!CAUTION] Cảnh báo Di sản
> Các thuật ngữ dưới đây thuộc về dự án cũ **SPAFS V5.2 (Hướng 4: Multi-Horizon Interval & Risk Forecasting)** theo ADR 0001–0005. **Không áp dụng các thuật ngữ và ràng buộc này cho pipeline truyền thống hiện tại.**

- **Horizon Return ($r_{t,h}$)**: Lợi suất logarit cộng dồn $\ln(P_{t+h}/P_t)$ cho bài toán phân vị. *(Thay thế bởi Relative Change $R_{o,h}$ trong REVISED)*.
- **Purged Walk-Forward & Embargo**: Cơ chế cross-validation loại trừ mẫu chồng lấn cho phân vị rủi ro. *(Thay thế bởi Sequential Split 70/15/15 trong REVISED)*.
- **Quantile Forecast ($Q0\text{–}Q4$)**: Bộ 9 mức phân vị điều kiện cho dự báo khoảng dao động. *(Không thuộc phạm vi dự báo điểm của REVISED)*.
- **Stream 1 / Stream 2**: Các mẫu đánh giá phụ hồi cứu khủng hoảng của SPAFS V5.2.
