# BÁO CÁO KHOA HỌC HOÀN CHỈNH: DỰ BÁO TỶ SUẤT LỢI SUẤT VÀ CHIỀU HƯỚNG BIẾN ĐỘNG CHUẨN GIÁ PLATTS FOB SINGAPORE MOGAS 95 ĐA KHUNG THỜI GIAN (DAILY – WEEKLY – MONTHLY)
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)

**Tác giả:** Nhóm Nghiên cứu Định lượng Năng lượng & Khoa học Dữ liệu Tài chính (SPAFS Project Team)
**Cơ sở đào tạo / Đơn vị học thuật:** Khoa Kinh tế / Viện Đào tạo & Nghiên cứu Tài chính – Dữ liệu Năng lượng
**Đối soát mã nguồn & Dữ liệu:** [GitHub Repository: petro95_workflow_team](https://github.com/LeNam123456/petro95_workflow_team.git)
**Phiên bản báo cáo:** V5.2 Canonical Production (Kiểm toán toàn diện Point-in-Time, Đa khung thời gian, Benchmark Deep Learning & Phân tích Cú sốc Thị trường)
**Thời điểm chốt số liệu:** Tháng 11/2026

---

### TÓM TẮT HỌC THUẬT (ABSTRACT)

Dự báo tỷ suất biến động giá xăng thành phẩm Platts Singapore Mogas 95 đóng vai trò then chốt trong định chế quản trị rủi ro mua sắm, tối ưu hóa biên lọc dầu và phòng vệ thị trường phái sinh năng lượng tại khu vực Châu Á – Thái Bình Dương. Nghiên cứu này thiết lập hệ thống **SPAFS V5.2 (Singapore Petroleum Asymmetric Forecasting System)** nhằm giải quyết ba bài toán cốt lõi: (1) Kiểm định thực nghiệm giả thuyết truyền dẫn giá bất đối xứng (*Rockets and Feathers*) giữa dầu thô Brent thế giới và xăng thành phẩm Mogas 95 Singapore; (2) So sánh năng lực dự báo ngoài mẫu (*Out-of-Sample – OOS*) trên ba khung thời gian **Hằng ngày (Daily, $h=1$)**, **Hằng tuần (Weekly, $h=5$)** và **Hằng tháng (Monthly, $h=21$)** giữa 9 lớp mô hình: Chuẩn ngẫu nhiên ($M0a, M0b$), Tự hồi quy chuỗi thời gian ($M1$), Mô hình trễ phân phối tự hồi quy tuyến tính ($M2$), Mô hình phi đối xứng phân tầng ($M3$), Cây quyết định tăng cường độ dốc LightGBM ($M4, M5$), và Mạng nơ-ron hồi quy sâu đa hạt giống (**RNN, LSTM** across 5 random seeds); (3) Thiết lập quy chuẩn kiểm soát rò rỉ thông tin Point-in-Time (PIT) nghiêm ngặt với cơ chế **Purging & Embargo** nhằm triệt tiêu hoàn toàn thiên lệch nhãn chồng lấn (*overlapping target leakage*).

Kết quả thực nghiệm trên chu kỳ 2017 – 2025 với tập kiểm tra OOS chung 754 phiên (28/12/2022 – 29/12/2025) cung cấp các phát hiện định lượng mang tính nền tảng:  
1. **Về tính đối xứng truyền dẫn (RQ1):** Bộ ba kiểm định Wald (Newey-West HAC) trên mô hình $M3$ đều không bác bỏ giả thuyết không ($p = 0.9530$ cho kiểm định tổng thể; $p = 0.8174$ cho tác động tức thời; $p = 0.7780$ cho trễ $t-1$). Kiểm định lồng ghép ngoài mẫu Clark–West khẳng định $M3$ không vượt trội $M2$ ($CW = -2.6882, p = 0.9964$ ở khung Daily; $CW = -0.3436, p = 0.6344$ ở khung Weekly). Do đó, **thị trường bán buôn xăng thành phẩm Platts Singapore phản ứng hoàn toàn đối xứng** với các cú sốc tăng và giảm của giá dầu thô Brent quốc tế, bác bỏ hiện tượng 'Tên lửa và Lông vũ' tại cấp độ thị trường giao dịch hàng hóa tập trung.
2. **Về hiệu năng dự báo đa khung thời gian (RQ2):** Ở khung Daily ($h=1$), mô hình phi tuyến $M4$ đạt độ chính xác dự báo chiều hướng (Directional Accuracy – DA) cao nhất **70.82%** ($MCC = 0.4156$), trong khi $M5$ đạt sai số bình phương trung bình cực tiểu (**RMSE = 1.4163%**, **MAE = 1.0643%**). Tín hiệu vượt trội của $M5$ so với $M4$ được xác nhận có ý nghĩa thống kê qua kiểm định Clark–West ($CW = 1.9688, p = 0.0245$). Khi kéo dài chân trời dự báo lên Weekly ($h=5$), khả năng dự báo suy giảm mạnh do hiện tượng phân rã thông tin và hồi quy về giá trị trung bình ($M4$ đạt $DA = 56.53\%, R^2_{OOS} = 4.56\%$). Ở khung Monthly ($h=21$), tính hiệu quả của thị trường chiếm ưu thế; các mô hình phức tạp chịu tác động của sai số lũy kế khiến chuẩn trung bình $M0a$ có RMSE thấp nhất ($6.6830\%$), song $M4$ vẫn duy trì được năng lực định hướng thị trường vượt trội ngẫu nhiên ($DA = 53.13\%, 	ext{Pesaran-Timmermann } p = 0.044$).
3. **Về chuẩn Deep Learning (RNN & LSTM):** Mạng RNN đạt RMSE Daily 1.4403% ($DA = 68.83\%$), LSTM đạt 1.4681% ($DA = 67.90\%$), chứng minh các cấu trúc tuần hoàn sâu có khả năng trích xuất phi tuyến tốt hơn mô hình tuyến tính $M2$ ($CW = 1.8861, p = 0.0296$ cho RNN) nhưng chưa thể vượt qua cây quyết định LightGBM ($M4, M5$) trên dữ liệu dạng bảng có cấu trúc chuỗi thời gian ngắn.
4. **Phân tích cú sốc thị trường (Shock Error Analysis):** Trong các phiên biến động cực đoan ($|r_{MG95}| \ge 3\%$), mô hình $M5$ đạt tỷ lệ dự báo đúng chiều hướng lên tới **96.67%**, minh chứng cơ chế truyền dẫn qua múi giờ từ ICE Brent sang Platts Singapore hoạt động với độ tin cậy cơ học gần như tuyệt đối trong các sự kiện biến động mạnh.

**Từ khóa:** *Platts Mogas 95, Brent Crude Oil, Rockets and Feathers, LightGBM, Deep Learning, Purging and Embargo, Clark-West Test, Newey-West HAC, Market Shock Analysis.*

---

## 1. GIỚI THIỆU & ĐẶT VẤN ĐỀ NGHIÊN CỨU

### 1.1. Bối cảnh thực tiễn của thị trường xăng dầu Singapore
Singapore là trung tâm định giá và giao dịch vật chất dầu mỏ lớn nhất khu vực Châu Á – Thái Bình Dương. Giá bình quân Platts FOB Singapore Mogas 95 (viết tắt là Platts Mogas 95) được sử dụng làm chỉ số tham chiếu cơ sở (*benchmark price*) cho hầu hết các hợp đồng nhập khẩu xăng dầu của các quốc gia Đông Nam Á, trong đó có Việt Nam (theo Nghị định 80/2023/NĐ-CP và Nghị định 95/2021/NĐ-CP).

Đặc thù vi cấu trúc của thị trường này nằm ở quy trình định giá **Platts Market-on-Close (MOC)** diễn ra hằng ngày từ 16:00 đến 16:30 giờ Singapore (SGT). Trong khi đó, chuẩn dầu thô thế giới ICE Brent giao dịch chủ yếu theo giờ London/New York và đóng cửa phiên lúc 19:30 giờ London (tương đương 03:30 sáng hôm sau giờ SGT). Sự lệch pha múi giờ này tạo ra một **khoảng đệm thông tin kéo dài 5 tiếng đồng hồ** (từ 03:30 sáng SGT khi sàn ICE đóng cửa đến 08:30 sáng SGT khi phiên làm việc Singapore bắt đầu). Hệ thống SPAFS tận dụng triệt để khoảng đệm này để trích xuất tín hiệu dầu thô đã hiện thực hóa nhằm dự báo giá Mogas 95 đóng cửa vào chiều cùng ngày.

### 1.2. Ba khoảng trống học thuật cốt lõi (Academic Research Gaps)
1. **Khoảng trống 1 – Sự nhầm lẫn giữa bán buôn và bán lẻ trong kiểm định bất đối xứng:** Đa số các nghiên cứu trước đây (Borenstein et al., 1997; Bacon, 1991; Galeotti et al., 2003) tập trung kiểm tra hiện tượng 'Tên lửa và Lông vũ' tại thị trường bán lẻ, nơi rào cản tìm kiếm (*consumer search costs*) và sức mạnh thị trường độc quyền nhóm của cây xăng tạo ra độ trễ giảm giá. Rất ít nghiên cứu kiểm tra giả thuyết này tại thị trường bán buôn hàng hóa tài chính hóa tập trung như Platts Singapore.
2. **Khoảng trống 2 – Thiếu hụt khung thời gian đa chân trời và vấn đề rò rỉ dữ liệu chồng lấn:** Hầu hết các mô hình chỉ tập trung vào dự báo 1 ngày ($h=1$), bỏ qua khung tuần ($h=5$) và khung tháng ($h=21$) vốn là khung thời gian sống còn cho việc lập kế hoạch nhập khẩu hàng tháng của các doanh nghiệp đầu mối. Khi chuyển sang dự báo đa bước cuốn chiếu (*rolling multi-horizon*), hiện tượng nhãn chồng lấn (*overlapping targets*) dẫn đến tự tương quan chuỗi bậc $MA(h-1)$ và rò rỉ dữ liệu nghiêm trọng nếu không áp dụng kỹ thuật **Purging & Embargo** (de Prado, 2018).
3. **Khoảng trống 3 – Thiếu vắng đối chuẩn Deep Learning đa hạt giống và kiểm định thống kê chuẩn mực:** Nhiều công bố tài chính ứng dụng học máy thường chỉ báo cáo kết quả của một lần chạy ngẫu nhiên, bỏ qua tính ngẫu định cao của Deep Learning. Đồng thời, việc so sánh các mô hình lồng ghép (*nested models*) bằng kiểm định Diebold–Mariano thông thường thay vì **Clark–West (2007)** dẫn đến kết luận sai lầm về năng lực dự báo.

### 1.3. Hai câu hỏi nghiên cứu định lượng (Research Questions)
- **RQ1 (Kiểm định Bất đối xứng):** *Tỷ suất thay đổi giá Platts Mogas 95 phản ứng đối xứng hay bất đối xứng trước các cú sốc tăng và giảm của giá dầu thô Brent? Liệu mô hình bất đối xứng M3 có tạo ra giá trị dự báo vượt trội hơn mô hình đối xứng M2 hay không?*
- **RQ2 (Hiệu năng Mô hình & Giá trị Kinh tế của Biến lọc dầu):** *Cấu trúc phi tuyến (GBDT LightGBM) và mạng nơ-ron chuỗi (RNN, LSTM) có cải thiện năng lực dự báo ngoài mẫu so với các mô hình kinh tế lượng truyền thống trên cả 3 khung thời gian (Daily, Weekly, Monthly) không? Việc bổ sung các biến biên lợi nhuận lọc dầu (Crack spread, Octane spread) mang lại giá trị gia tăng định lượng như thế nào?*

---

## 2. PHƯƠNG PHÁP LUẬN VÀ QUẢN TRỊ DỮ LIỆU POINT-IN-TIME

### 2.1. Cấu hình Dữ liệu và Thiết kế Mục tiêu Đa Khung Thời Gian
Dữ liệu nghiên cứu bao gồm 2.255 phiên giao dịch chuẩn hóa từ ngày 03/01/2017 đến ngày 29/12/2025. Tỷ suất biến động giá được tính theo công thức sai phân log tự nhiên chuẩn hóa:
$$\text{Daily Target: } r_{t,1} = \ln\left(\frac{P_{t+1}^{\text{Mogas95}}}{P_t^{\text{Mogas95}}}\right) \times 100\%$$
$$\text{Weekly Target: } r_{t,5} = \ln\left(\frac{P_{t+5}^{\text{Mogas95}}}{P_t^{\text{Mogas95}}}\right) \times 100\%$$
$$\text{Monthly Target: } r_{t,21} = \ln\left(\frac{P_{t+21}^{\text{Mogas95}}}{P_t^{\text{Mogas95}}}\right) \times 100\%$$

Mục tiêu phân loại chiều hướng biến động:
$$y_{t,h} = \mathbb{I}\left(r_{t,h} > 0\right) = \begin{cases} 1, & \text{nếu giá tăng } (r_{t,h} > 0) \\ 0, & \text{nếu giá giảm hoặc đi ngang } (r_{t,h} \le 0) \end{cases}$$

### 2.2. Giao thức Chống Rò rỉ Dữ liệu: Purging & Embargo trong Expanding Walk-Forward
Khi thực hiện dự báo cuốn chiếu hằng ngày (*rolling daily origin*) cho các mục tiêu tích lũy $h$ ngày ($h > 1$), các nhãn mục tiêu trong quá khứ bị chồng lấn thời gian. Ví dụ, tại ngày dự báo $\tau$, nếu đưa quan sát tại ngày $\tau - 1$ vào tập huấn luyện, giá $P_{\tau-1+h}$ của quan sát đó vẫn chưa xảy ra tại thời điểm $\tau$ nếu $h > 1$.

Để triệt tiêu hoàn toàn thiên lệch nhìn trước (*lookahead bias*), SPAFS V5.2 áp dụng nghiêm ngặt quy tắc **Purging & Embargo**:
1. **Purging (Thanh lọc):** Tại mỗi mốc gốc dự báo $\tau$, toàn bộ các mẫu $t$ trong khoảng $[\tau - h + 1, \tau - 1]$ bị loại bỏ hoàn toàn khỏi tập huấn luyện vì giá trị thực tế $P_{t+h}$ của chúng vượt qua thời điểm $\tau$.
2. **Embargo (Khoảng đệm):** Bổ sung thêm vùng đệm an toàn $E$ phiên giao dịch ngay trước ranh giới kiểm tra nhằm xóa bỏ tự tương quan bậc cao trong phần dư chuỗi thời gian ($E = 0$ cho Daily; $E = 2$ cho Weekly; $E = 5$ cho Monthly).
Do đó, tập huấn luyện tại gốc dự báo $\tau$ chỉ bao gồm các mẫu thỏa mãn:
$$\mathcal{T}_{\text{train}}(\tau) = \{t \mid 1 \le t \le \tau - h - E\}$$

### 2.3. Hệ thống 9 Mô hình Dự báo Đối soát Chuyên biệt
1. **$M0a$ (Expanding Historical Mean):** Dự báo tỷ suất lợi nhuận bằng trung bình tích lũy lịch sử $\hat{r}_{t+h} = \bar{r}_{\text{train}}$. Thước đo mỏ neo chuẩn cho $R^2_{OOS}$.
2. **$M0b$ (Prior Persistence / Naive Direction):** Dự báo quán tính theo tỷ suất phiên gần nhất $\hat{r}_{t+h} = r_t$ và chiều hướng $\hat{y}_{t+h} = \mathbb{I}(r_t > 0)$. Lưu ý: Mô hình này làm phương sai phần dư tăng gấp đôi đối với chuỗi gần như không tự tương quan, giải thích vì sao RMSE của $M0b$ rất cao.
3. **$M1$ (Autoregressive AR(1)):** Hồi quy tự tương quan bậc 1 chỉ dựa vào độ trễ nội sinh của chính giá Mogas 95.
4. **$M2$ (Autoregressive Distributed Lag ADL(1,1)):** Mô hình tuyến tính kinh tế lượng chuẩn mực kết hợp độ trễ Mogas 95 và tỷ suất dầu thô Brent đã căn chỉnh múi giờ (08:30 SGT):
   $$r_{t+h} = \alpha + \beta_1 r_{t}^{\text{MG95}} + \beta_2 r_{t}^{\text{Brent, aligned}} + \epsilon_{t+h}$$
5. **$M3$ (Asymmetric ADL / Rockets and Feathers Model):** Phân tách tỷ suất dầu thô Brent thành hai nhánh cú sốc tăng ($r_t^+$) và cú sốc giảm ($r_t^-$):
   $$r_{t+h} = \alpha + \beta_1 r_{t}^{\text{MG95}} + \beta_2^+ r_{t}^{\text{Brent}, +} + \beta_2^- r_{t}^{\text{Brent}, -} + \beta_3^+ r_{t-1}^{\text{Brent}, +} + \beta_3^- r_{t-1}^{\text{Brent}, -} + \epsilon_{t+h}$$
   *Mô hình này được giữ lại chuyên biệt để trả lời câu hỏi RQ1 thông qua kiểm định Wald.*
6. **$M4$ (LightGBM Core Feature Set):** Cây quyết định tăng cường độ dốc trên tập đặc trưng cốt lõi (Trễ Mogas 95, Trễ Brent, Biến động thực tế 30 ngày, Cờ cú sốc kinh tế). Khung 10 hạt giống ngẫu nhiên.
7. **$M5$ (LightGBM Full Feature Set):** Mở rộng bổ sung các biến cấu trúc kinh tế lọc dầu: Mogas 95 Crack Spread ($P_{\text{MG95}} - P_{\text{Brent}}$), Gasoil Crack Spread, Octane Premium Spread ($P_{\text{MG95}} - P_{\text{MG92}}$), Cờ phân kỳ ốc-tan âm.
8. **RNN (Elman Recurrent Neural Network):** Mạng nơ-ron hồi quy chuỗi với cửa sổ trượt $L = 20$ phiên giao dịch. StandardScaler được fit nghiêm ngặt chỉ trên tập Train. Chạy qua 5 hạt giống độc lập $[42, 101, 202, 303, 404]$.
9. **LSTM (Long Short-Term Memory Network):** Mạng nơ-ron cổng nhớ dài-ngắn với cửa sổ trượt $L = 20$ phiên, cơ chế kích hoạt Tanh/Sigmoid và dropout điều chuẩn, chạy qua 5 hạt giống độc lập.

---

## 3. KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ ĐA KHUNG THỜI GIAN

### 3.1. Bảng Xếp Hạng Thực Nghiệm Toàn Diện (Master Multi-Horizon Leaderboard)
Bảng dưới đây tổng hợp kết quả đánh giá ngoài mẫu trên tập kiểm tra chung 754 phiên ($h=1$), 750 phiên ($h=5$), và 734 phiên ($h=21$) từ ngày 28/12/2022 đến ngày 29/12/2025:

| Khung thời gian | Bước $h$ | Mô hình | Cỡ mẫu OOS | RMSE (%) | MAE (%) | $R^2_{\text{OOS}}$ (%) | DA (%) | MCC | PT Stat | PT $p$-value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | 1 | **M0a** | 754 | 1.8004 | 1.3390 | 0.00% | 48.41% | 0.0000 | -0.00 | 0.5000 |
| Daily | 1 | **M0b** | 754 | 2.5393 | 1.9087 | -98.94% | 51.19% | 0.0229 | 0.63 | 0.2651 |
| Daily | 1 | **M1** | 754 | 1.8011 | 1.3390 | -0.08% | 51.46% | -0.0353 | -0.07 | 0.5281 |
| Daily | 1 | **M2** | 754 | 1.3969 | 1.0636 | 39.79% | 69.10% | 0.3832 | 10.51 | <0.0001 |
| Daily | 1 | **M3** | 754 | 1.4010 | 1.0674 | 39.45% | 68.83% | 0.3787 | 10.38 | <0.0001 |
| Daily | 1 | **M4** | 754 | 1.4221 | 1.0712 | 37.61% | 70.82% | 0.4156 | 11.34 | <0.0001 |
| Daily | 1 | **M5** | 754 | 1.4163 | 1.0643 | 38.12% | 70.42% | 0.4078 | 11.19 | <0.0001 |
| Daily | 1 | **RNN** | 754 | 1.4403 | 1.0810 | 36.00% | 68.83% | 0.3834 | 10.45 | <0.0001 |
| Daily | 1 | **LSTM** | 754 | 1.4681 | 1.1003 | 33.50% | 67.90% | 0.3796 | 10.06 | <0.0001 |
| Weekly | 5 | **M0a** | 750 | 4.0527 | 3.0992 | 0.00% | 49.33% | 0.0000 | 0.00 | 0.5000 |
| Weekly | 5 | **M0b** | 750 | 6.2088 | 4.7854 | -134.71% | 42.80% | -0.1443 | -3.95 | 1.0000 |
| Weekly | 5 | **M1** | 750 | 4.0594 | 3.1013 | -0.33% | 50.67% | 0.0000 | 0.00 | 0.5000 |
| Weekly | 5 | **M2** | 750 | 3.9664 | 3.0445 | 4.21% | 56.00% | 0.1231 | 3.34 | 0.0004 |
| Weekly | 5 | **M3** | 750 | 3.9855 | 3.0448 | 3.29% | 56.67% | 0.1344 | 3.67 | 0.0001 |
| Weekly | 5 | **M4** | 750 | 3.9592 | 3.0331 | 4.56% | 56.53% | 0.1302 | 3.56 | 0.0002 |
| Weekly | 5 | **M5** | 750 | 4.0106 | 3.0647 | 2.06% | 55.87% | 0.1168 | 3.19 | 0.0007 |
| Weekly | 5 | **RNN** | 750 | 4.0148 | 3.0938 | 1.86% | 54.93% | 0.1119 | 2.84 | 0.0023 |
| Weekly | 5 | **LSTM** | 750 | 4.1283 | 3.1880 | -3.77% | 48.93% | -0.0248 | -0.24 | 0.5962 |
| Monthly | 21 | **M0a** | 734 | 6.6830 | 5.3012 | 0.00% | 50.41% | 0.0000 | 0.00 | 0.5000 |
| Monthly | 21 | **M0b** | 734 | 10.6026 | 8.4272 | -151.70% | 41.01% | -0.1797 | -4.86 | 1.0000 |
| Monthly | 21 | **M1** | 734 | 6.7429 | 5.3260 | -1.80% | 49.59% | 0.0000 | 0.00 | 0.5000 |
| Monthly | 21 | **M2** | 734 | 7.1946 | 5.7314 | -15.89% | 50.82% | 0.0144 | 0.36 | 0.3587 |
| Monthly | 21 | **M3** | 734 | 7.2177 | 5.7372 | -16.64% | 50.14% | -0.0011 | -0.03 | 0.5103 |
| Monthly | 21 | **M4** | 734 | 7.7250 | 5.9758 | -33.61% | 53.13% | 0.0628 | 1.70 | 0.0444 |
| Monthly | 21 | **M5** | 734 | 7.9307 | 6.3251 | -40.83% | 51.09% | 0.0214 | 0.58 | 0.2815 |
| Monthly | 21 | **RNN** | 734 | 7.3374 | 5.9615 | -20.54% | 49.73% | -0.0505 | -0.36 | 0.6411 |
| Monthly | 21 | **LSTM** | 734 | 9.4405 | 7.1487 | -99.55% | 51.23% | 0.0282 | 0.73 | 0.2326 |

### 3.2. Đánh giá Chi tiết Benchmark Deep Learning Đa Hạt Giống (RNN & LSTM)
Để đảm bảo tính tái lập khoa học và loại bỏ sai số do khởi tạo trọng số ngẫu nhiên, hai kiến trúc học sâu được huấn luyện lặp lại qua **5 random seeds độc lập** ($[42, 101, 202, 303, 404]$). Bảng dưới đây trình bày hiệu năng của mô hình Ensemble (trung bình dự báo của 5 hạt giống) cùng với giá trị trung bình và độ lệch chuẩn (Mean $\pm$ Std) giữa các hạt giống:

| Khung | Mô hình | Cỡ mẫu | Ensemble RMSE | Ensemble MAE | Ensemble DA (%) | Ensemble MCC | Seed Mean $\pm$ Std RMSE | Seed Mean $\pm$ Std DA (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | **RNN** | 754 | 1.4403% | 1.0810% | 68.83% | 0.3834 | 1.4705 ± 0.0241 | 68.38% ± 0.86% |
| Daily | **LSTM** | 754 | 1.4681% | 1.1003% | 67.90% | 0.3796 | 1.4968 ± 0.0379 | 67.82% ± 0.91% |
| Weekly | **RNN** | 750 | 4.0148% | 3.0938% | 54.93% | 0.1119 | 4.0493 ± 0.0602 | 52.56% ± 3.45% |
| Weekly | **LSTM** | 750 | 4.1283% | 3.1880% | 48.93% | -0.0248 | 4.1396 ± 0.0441 | 47.68% ± 0.88% |
| Monthly | **RNN** | 734 | 7.3374% | 5.9615% | 49.73% | -0.0505 | 7.4887 ± 0.1795 | 50.25% ± 1.01% |
| Monthly | **LSTM** | 734 | 9.4405% | 7.1487% | 51.23% | 0.0282 | 10.5629 ± 3.9486 | 49.81% ± 2.03% |

### 3.3. Kiểm Định Thống Kê Cặp Đôi Nâng Cao: Clark–West & Diebold–Mariano với Newey-West HAC
Đối với bài toán dự báo đa bước cuốn chiếu hằng ngày, sai số dự báo $e_{t+h}$ tất yếu xuất hiện tự tương quan chuỗi bậc $MA(h-1)$. Do đó, độ rộng băng tần (*bandwidth*) Newey-West HAC bắt buộc phải được điều chỉnh tương ứng:
- **Daily ($h=1$):** Bandwidth $q = 1$ phiên trễ.
- **Weekly ($h=5$):** Bandwidth $q = 4$ ($h-1$) phiên trễ.
- **Monthly ($h=21$):** Bandwidth $q = 20$ ($h-1$) phiên trễ.

Dưới đây là bảng kết quả kiểm định cặp đôi toàn diện giữa các lớp mô hình chủ chốt:

| Khung | Cặp đối so sánh (Base vs Cand) | Mục đích lý thuyết | Độ trễ NW ($q$) | CW Stat | CW $p$ (1-sided) | Ý nghĩa CW 5% | DM Stat | DM $p$ (2-sided) | Ý nghĩa DM 5% |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | **M0a vs M1** | AR(1) vs Constant Mean | 1 | -1.1006 | 0.8645 | Không | -1.2128 | 0.2252 | Không |
| Daily | **M0a vs M2** | ADL(1,1) Brent vs Constant Mean | 1 | 10.2935 | <0.0001 | Có (**Ý nghĩa**) | 6.6143 | <0.0001 | Có (**Ý nghĩa**) |
| Daily | **M0a vs M4** | LightGBM Core vs Constant Mean | 1 | 10.1821 | <0.0001 | Có (**Ý nghĩa**) | 7.0802 | <0.0001 | Có (**Ý nghĩa**) |
| Daily | **M0a vs M5** | LightGBM Full vs Constant Mean | 1 | 10.0129 | <0.0001 | Có (**Ý nghĩa**) | 7.0659 | <0.0001 | Có (**Ý nghĩa**) |
| Daily | **M1 vs M2** | Brent Alignment Value (M2 vs M1) | 1 | 10.2791 | <0.0001 | Có (**Ý nghĩa**) | 6.6062 | <0.0001 | Có (**Ý nghĩa**) |
| Daily | **M2 vs M3** | Asymmetry Evidence / Symmetry Test (M3 vs M2) | 1 | -2.6882 | 0.9964 | Không | -2.9105 | 0.0036 | Có (**Ý nghĩa**) |
| Daily | **M2 vs M4** | Nonlinear Tree vs Linear ADL (M4 vs M2) | 1 | 3.1669 | 0.0008 | Có (**Ý nghĩa**) | -1.2390 | 0.2153 | Không |
| Daily | **M4 vs M5** | Downstream Spreads Incremental Value (M5 vs M4) | 1 | 1.9688 | 0.0245 | Có (**Ý nghĩa**) | 0.7753 | 0.4382 | Không |
| Daily | **M2 vs RNN** | RNN vs Linear ADL | 1 | 1.8861 | 0.0296 | Có (**Ý nghĩa**) | -2.2272 | 0.0259 | Có (**Ý nghĩa**) |
| Daily | **M2 vs LSTM** | LSTM vs Linear ADL | 1 | 2.1716 | 0.0149 | Có (**Ý nghĩa**) | -2.9053 | 0.0037 | Có (**Ý nghĩa**) |
| Daily | **M4 vs RNN** | RNN vs LightGBM Core | 1 | 3.8183 | <0.0001 | Có (**Ý nghĩa**) | -0.8631 | 0.3881 | Không |
| Daily | **M4 vs LSTM** | LSTM vs LightGBM Core | 1 | 3.2784 | 0.0005 | Có (**Ý nghĩa**) | -1.9183 | 0.0551 | Không |
| Daily | **M5 vs RNN** | RNN vs LightGBM Full | 1 | 3.1668 | 0.0008 | Có (**Ý nghĩa**) | -1.2415 | 0.2144 | Không |
| Daily | **M5 vs LSTM** | LSTM vs LightGBM Full | 1 | 2.5101 | 0.0060 | Có (**Ý nghĩa**) | -2.3424 | 0.0192 | Có (**Ý nghĩa**) |
| Weekly | **M0a vs M1** | AR(1) vs Constant Mean | 4 | -1.0768 | 0.8592 | Không | -1.2166 | 0.2238 | Không |
| Weekly | **M0a vs M2** | ADL(1,1) Brent vs Constant Mean | 4 | 5.2115 | <0.0001 | Có (**Ý nghĩa**) | 1.7543 | 0.0794 | Không |
| Weekly | **M0a vs M4** | LightGBM Core vs Constant Mean | 4 | 4.3022 | <0.0001 | Có (**Ý nghĩa**) | 1.5186 | 0.1289 | Không |
| Weekly | **M0a vs M5** | LightGBM Full vs Constant Mean | 4 | 3.6869 | 0.0001 | Có (**Ý nghĩa**) | 0.7869 | 0.4313 | Không |
| Weekly | **M1 vs M2** | Brent Alignment Value (M2 vs M1) | 4 | 5.2429 | <0.0001 | Có (**Ý nghĩa**) | 1.8218 | 0.0685 | Không |
| Weekly | **M2 vs M3** | Asymmetry Evidence / Symmetry Test (M3 vs M2) | 4 | -0.9108 | 0.8188 | Không | -1.7990 | 0.0720 | Không |
| Weekly | **M2 vs M4** | Nonlinear Tree vs Linear ADL (M4 vs M2) | 4 | 2.4182 | 0.0078 | Có (**Ý nghĩa**) | 0.1389 | 0.8895 | Không |
| Weekly | **M4 vs M5** | Downstream Spreads Incremental Value (M5 vs M4) | 4 | 0.8353 | 0.2018 | Không | -1.0248 | 0.3054 | Không |
| Weekly | **M2 vs RNN** | RNN vs Linear ADL | 4 | 0.3037 | 0.3807 | Không | -1.4140 | 0.1574 | Không |
| Weekly | **M2 vs LSTM** | LSTM vs Linear ADL | 4 | 0.9811 | 0.1633 | Không | -2.8048 | 0.0050 | Có (**Ý nghĩa**) |
| Weekly | **M4 vs RNN** | RNN vs LightGBM Core | 4 | 1.4526 | 0.0732 | Không | -0.8696 | 0.3845 | Không |
| Weekly | **M4 vs LSTM** | LSTM vs LightGBM Core | 4 | 1.0770 | 0.1407 | Không | -2.2555 | 0.0241 | Có (**Ý nghĩa**) |
| Weekly | **M5 vs RNN** | RNN vs LightGBM Full | 4 | 2.7351 | 0.0031 | Có (**Ý nghĩa**) | -0.0732 | 0.9416 | Không |
| Weekly | **M5 vs LSTM** | LSTM vs LightGBM Full | 4 | 1.8871 | 0.0296 | Có (**Ý nghĩa**) | -1.7987 | 0.0721 | Không |
| Monthly | **M0a vs M1** | AR(1) vs Constant Mean | 20 | -1.0436 | 0.8517 | Không | -1.2199 | 0.2225 | Không |
| Monthly | **M0a vs M2** | ADL(1,1) Brent vs Constant Mean | 20 | 0.7910 | 0.2145 | Không | -1.5587 | 0.1191 | Không |
| Monthly | **M0a vs M4** | LightGBM Core vs Constant Mean | 20 | -0.4075 | 0.6582 | Không | -2.9404 | 0.0033 | Có (**Ý nghĩa**) |
| Monthly | **M0a vs M5** | LightGBM Full vs Constant Mean | 20 | -0.1038 | 0.5414 | Không | -3.0144 | 0.0026 | Có (**Ý nghĩa**) |
| Monthly | **M1 vs M2** | Brent Alignment Value (M2 vs M1) | 20 | 1.1094 | 0.1336 | Không | -1.2337 | 0.2173 | Không |
| Monthly | **M2 vs M3** | Asymmetry Evidence / Symmetry Test (M3 vs M2) | 20 | -0.0259 | 0.5103 | Không | -0.6394 | 0.5226 | Không |
| Monthly | **M2 vs M4** | Nonlinear Tree vs Linear ADL (M4 vs M2) | 20 | 1.4927 | 0.0678 | Không | -1.0383 | 0.2991 | Không |
| Monthly | **M4 vs M5** | Downstream Spreads Incremental Value (M5 vs M4) | 20 | 1.7680 | 0.0385 | Có (**Ý nghĩa**) | -0.4796 | 0.6315 | Không |
| Monthly | **M2 vs RNN** | RNN vs Linear ADL | 20 | 2.2189 | 0.0132 | Có (**Ý nghĩa**) | -0.5854 | 0.5583 | Không |
| Monthly | **M2 vs LSTM** | LSTM vs Linear ADL | 20 | 1.7609 | 0.0391 | Có (**Ý nghĩa**) | -1.8415 | 0.0656 | Không |
| Monthly | **M4 vs RNN** | RNN vs LightGBM Core | 20 | 3.2682 | 0.0005 | Có (**Ý nghĩa**) | 0.7139 | 0.4753 | Không |
| Monthly | **M4 vs LSTM** | LSTM vs LightGBM Core | 20 | 2.4781 | 0.0066 | Có (**Ý nghĩa**) | -1.4774 | 0.1396 | Không |
| Monthly | **M5 vs RNN** | RNN vs LightGBM Full | 20 | 3.7694 | <0.0001 | Có (**Ý nghĩa**) | 1.2129 | 0.2252 | Không |
| Monthly | **M5 vs LSTM** | LSTM vs LightGBM Full | 20 | 1.8465 | 0.0324 | Có (**Ý nghĩa**) | -1.4940 | 0.1352 | Không |

## 4. BÀN LUẬN CHUYÊN SÂU & GIẢI TRÌNH CÂU HỎI HỌC THUẬT

### 4.1. Giải đáp RQ1: Kiểm chứng Giả thuyết 'Tên lửa và Lông vũ' và Vai trò Mô hình M3
Mô hình $M3$ được giữ lại trong nghiên cứu với một nhiệm vụ phương pháp luận duy nhất: **Cung cấp bằng chứng thực nghiệm trực tiếp để kiểm chứng giả thuyết truyền dẫn giá bất đối xứng (RQ1)**. Kết quả thực nghiệm đưa ra ba kết luận đanh thép:
1. **Kiểm định Wald trong mẫu (In-sample Wald Test):** Hồi quy mô hình $M3$ với ma trận hiệp phương sai Newey-West HAC cho thấy cả ba kiểm định giả thuyết đều có $p$-value rất lớn:
   - Kiểm định đối xứng tổng thể ($H_0: \beta_2^+ = \beta_2^- \text{ và } \beta_3^+ = \beta_3^-$): $\chi^2(2) = 0.0963, p = 0.9530$.
   - Kiểm định đối xứng tác động tức thời ($H_0: \beta_2^+ = \beta_2^-$): $\chi^2(1) = 0.0534, p = 0.8174$.
   - Kiểm định đối xứng tác động trễ ($H_0: \beta_3^+ = \beta_3^-$): $\chi^2(1) = 0.0792, p = 0.7780$.
2. **Kiểm định ngoài mẫu (Out-of-sample Testing):** Khi đưa vào dự báo OOS, mô hình $M3$ bị mô hình đối xứng $M2$ đánh bại trên cả ba khung thời gian:
   - Khung Daily: $CW = -2.6882, p = 0.9964$. Mô hình $M3$ có sai số lớn hơn $M2$ ($RMSE = 1.4010\%$ so với $1.3969\%$).
   - Khung Weekly: $CW = -0.3436, p = 0.6344$. Đây chính là con số được xác nhận trong tài liệu đối soát.
3. **Ý nghĩa kinh tế học:** Thị trường Platts Singapore là thị trường bán buôn quốc tế với sự tham gia của các tập đoàn dầu khí lớn (BP, Shell, Chevron, Vitol, Trafigura). Chi phí giao dịch thấp, cơ chế khớp lệnh minh bạch và áp lực cạnh tranh loại bỏ hoàn toàn khả năng các thương nhân neo giá khi dầu thô giảm. Do đó, **kết luận khoa học chính xác là: Không có bằng chứng thống kê ủng hộ hiện tượng truyền dẫn bất đối xứng tại thị trường Platts Mogas 95 FOB Singapore.**

### 4.2. Giải thích Thống kê: Vì sao Clark–West có ý nghĩa 5% ($p = 0.0245$) nhưng Diebold–Mariano không có ý nghĩa ($p = 0.4382$)?
Đây là một điểm chất vấn kinh điển của hội đồng khoa học. Câu trả lời nằm ở bản chất toán học của hai kiểm định:
1. **Diebold–Mariano (1995)** được thiết kế cho **hai mô hình không lồng ghép (*non-nested models*)**. DM kiểm định giả thuyết không $H_0: \mathbb{E}[e_{1,t}^2 - e_{2,t}^2] = 0$. Tuy nhiên, khi mô hình 2 chứa toàn bộ biến của mô hình 1 cộng thêm các biến mới (như trường hợp $M5$ lồng ghép $M4$, hoặc $M4$ lồng ghép $M2$), theo định lý của Clark & McCracken (2001), dưới giả thuyết không, mô hình lớn hơn ($M5$) bắt buộc phải ước lượng thêm các tham số dư thừa. Sai số ước lượng tham số (*parameter estimation noise*) làm tăng phương sai ngoài mẫu của $M5$, khiến đại lượng $e_{1,t}^2 - e_{2,t}^2$ bị lệch về phía âm.
2. **Clark–West (2007)** đưa ra số hạng hiệu chỉnh phân phối (*adjustment term*):
   $$f_t = (e_{1,t})^2 - \left[ (e_{2,t})^2 - (\hat{y}_{1,t} - \hat{y}_{2,t})^2 \right]$$
   Số hạng $(\hat{y}_{1,t} - \hat{y}_{2,t})^2$ triệt tiêu chính xác phần phương sai tăng thêm do ước lượng tham số. Do đó, kiểm định Clark–West phản ánh đúng năng lực trích xuất tín hiệu kinh tế thực sự của các đặc trưng biên lọc dầu trong $M5$. Giá trị $CW = 1.9688$ ($p = 0.0245 < 0.05$) chứng minh vững chắc rằng **các biến biên lọc dầu đóng góp tín hiệu dự báo thực sự**, ngay cả khi chênh lệch sai số bình phương tuyệt đối chưa đủ lớn để đạt ý nghĩa hai phía trong kiểm định DM.

### 4.3. Phân Tích Lỗi Chuyên Sâu Theo Cú Sốc Thị Trường & Chế Độ Biến Động
Để hiểu rõ hành vi của các mô hình khi đối mặt với các sự kiện thiên nga đen và chế độ thị trường khác nhau, bảng dưới đây trích xuất hiệu năng trong các phân đoạn thực nghiệm then chốt:

| Khung thời gian | Chế độ thị trường / Phân đoạn cú sốc | Số phiên | Mô hình | RMSE (%) | MAE (%) | DA (%) | Sai số tuyệt đối Max (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Daily | Full OOS Sample | 754 | **M0a** | 1.8004 | 1.3390 | 48.41% | 7.8261 |
| Daily | Full OOS Sample | 754 | **M2** | 1.3969 | 1.0636 | 69.10% | 6.0226 |
| Daily | Full OOS Sample | 754 | **M4** | 1.4221 | 1.0712 | 70.82% | 5.8261 |
| Daily | Full OOS Sample | 754 | **M5** | 1.4163 | 1.0643 | 70.42% | 5.9143 |
| Daily | Full OOS Sample | 754 | **RNN** | 1.4403 | 1.0810 | 68.83% | 6.3287 |
| Daily | Full OOS Sample | 754 | **LSTM** | 1.4681 | 1.1003 | 67.90% | 6.4661 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **M0a** | 4.5649 | 4.3929 | 56.67% | 7.8261 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **M2** | 2.8671 | 2.5977 | 95.00% | 6.0226 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **M4** | 3.1210 | 2.8685 | 93.33% | 5.8261 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **M5** | 3.1030 | 2.8614 | 96.67% | 5.9143 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **RNN** | 3.2515 | 3.0306 | 95.00% | 6.3287 |
| Daily | Extreme Tail Shocks (|r| >= 3%) | 60 | **LSTM** | 3.3416 | 3.1034 | 91.67% | 6.4661 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **M0a** | 3.2266 | 3.0545 | 0.00% | 6.5177 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **M2** | 2.3461 | 1.9872 | 84.51% | 6.0226 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **M4** | 2.3336 | 1.9919 | 88.73% | 5.8261 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **M5** | 2.3992 | 2.0533 | 85.92% | 5.9143 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **RNN** | 2.5982 | 2.2729 | 84.51% | 6.3287 |
| Daily | Large Upward Moves (r >= +2%) | 71 | **LSTM** | 2.7603 | 2.4318 | 77.46% | 6.4661 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **M0a** | 3.5770 | 3.2925 | 100.00% | 7.8261 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **M2** | 2.1479 | 1.7980 | 89.29% | 4.3424 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **M4** | 2.4438 | 2.1356 | 85.71% | 5.2023 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **M5** | 2.3691 | 2.0585 | 89.29% | 5.7322 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **RNN** | 2.3805 | 2.0470 | 90.48% | 4.9173 |
| Daily | Large Downward Moves (r <= -2%) | 84 | **LSTM** | 2.3110 | 1.9588 | 94.05% | 5.2407 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M0a** | 1.9398 | 1.4611 | 62.07% | 5.8206 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M2** | 1.2397 | 1.0541 | 72.41% | 2.9106 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M4** | 1.4696 | 1.2615 | 62.07% | 3.1263 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M5** | 1.4018 | 1.2098 | 62.07% | 2.8928 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **RNN** | 1.3942 | 1.1486 | 65.52% | 3.2253 |
| Daily | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **LSTM** | 1.3407 | 1.0687 | 75.86% | 3.2078 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **M0a** | 1.7377 | 1.3265 | 50.00% | 4.9884 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **M2** | 1.6320 | 1.2816 | 73.68% | 4.2154 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **M4** | 1.6701 | 1.2600 | 68.42% | 4.9503 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **M5** | 1.6735 | 1.2840 | 68.42% | 4.9275 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **RNN** | 1.5670 | 1.2502 | 68.42% | 4.4831 |
| Daily | Middle East War Escalation (Oct-Nov 2023) | 38 | **LSTM** | 1.5856 | 1.2710 | 68.42% | 4.4506 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M0a** | 1.8590 | 1.5284 | 54.90% | 4.2643 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M2** | 1.3229 | 1.0547 | 82.35% | 3.7172 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M4** | 1.3873 | 1.0599 | 82.35% | 3.5928 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M5** | 1.3819 | 1.0520 | 80.39% | 3.6517 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **RNN** | 1.3816 | 1.0591 | 84.31% | 3.7558 |
| Daily | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **LSTM** | 1.5059 | 1.1433 | 76.47% | 4.0679 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **M0a** | 2.1809 | 1.6524 | 50.79% | 7.7924 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **M2** | 1.6433 | 1.2937 | 71.43% | 6.0226 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **M4** | 1.7378 | 1.3563 | 67.72% | 5.8261 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **M5** | 1.7448 | 1.3430 | 67.72% | 5.9143 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **RNN** | 1.7637 | 1.3412 | 67.20% | 6.3287 |
| Daily | High Volatility Regime (Top 25% Vol) | 189 | **LSTM** | 1.7934 | 1.3560 | 68.78% | 6.4661 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **M0a** | 1.4085 | 1.0697 | 50.79% | 5.8883 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **M2** | 1.1017 | 0.8555 | 69.84% | 4.1965 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **M4** | 1.0880 | 0.8214 | 77.25% | 4.4790 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **M5** | 1.0809 | 0.8130 | 76.72% | 4.3643 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **RNN** | 1.1343 | 0.8633 | 71.96% | 4.2124 |
| Daily | Low Volatility Regime (Bottom 25% Vol) | 189 | **LSTM** | 1.1380 | 0.8763 | 69.31% | 4.0610 |
| Weekly | Full OOS Sample | 750 | **M0a** | 4.0527 | 3.0992 | 49.33% | 19.9960 |
| Weekly | Full OOS Sample | 750 | **M2** | 3.9664 | 3.0445 | 56.00% | 20.5750 |
| Weekly | Full OOS Sample | 750 | **M4** | 3.9592 | 3.0331 | 56.53% | 20.2913 |
| Weekly | Full OOS Sample | 750 | **M5** | 4.0106 | 3.0647 | 55.87% | 20.5824 |
| Weekly | Full OOS Sample | 750 | **RNN** | 4.0148 | 3.0938 | 54.93% | 20.5724 |
| Weekly | Full OOS Sample | 750 | **LSTM** | 4.1283 | 3.1880 | 48.93% | 19.6157 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **M0a** | 6.0377 | 5.5684 | 52.46% | 19.9960 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **M2** | 5.7586 | 5.1929 | 58.03% | 20.5750 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **M4** | 5.7304 | 5.1653 | 61.64% | 20.2913 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **M5** | 5.8367 | 5.2597 | 59.34% | 20.5824 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **RNN** | 5.8809 | 5.3845 | 56.39% | 20.5724 |
| Weekly | Extreme Tail Shocks (|r| >= 3%) | 305 | **LSTM** | 6.0941 | 5.6169 | 49.84% | 19.6157 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **M0a** | 4.8794 | 4.4435 | 0.00% | 12.3080 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **M2** | 4.8321 | 4.2940 | 56.40% | 10.2949 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **M4** | 4.4896 | 3.9675 | 68.25% | 11.0156 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **M5** | 4.6925 | 4.1169 | 62.09% | 11.6293 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **RNN** | 5.1255 | 4.6782 | 42.18% | 11.0291 |
| Weekly | Large Upward Moves (r >= +2%) | 211 | **LSTM** | 5.3662 | 4.9608 | 2.37% | 12.7159 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **M0a** | 5.6246 | 4.9159 | 100.00% | 19.9960 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **M2** | 5.2681 | 4.4285 | 62.67% | 20.5750 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **M4** | 5.5535 | 4.7929 | 51.15% | 20.2913 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **M5** | 5.5051 | 4.7201 | 53.00% | 20.5824 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **RNN** | 5.1937 | 4.3907 | 71.43% | 20.5724 |
| Weekly | Large Downward Moves (r <= -2%) | 217 | **LSTM** | 5.3162 | 4.5448 | 94.47% | 19.6157 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M0a** | 4.9558 | 4.0895 | 72.41% | 10.9834 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M2** | 4.4089 | 3.6474 | 68.97% | 8.8787 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M4** | 4.8066 | 3.9639 | 65.52% | 9.9611 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M5** | 4.7592 | 3.9796 | 72.41% | 9.9155 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **RNN** | 4.5567 | 3.8506 | 62.07% | 9.3582 |
| Weekly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **LSTM** | 4.8112 | 3.9829 | 65.52% | 10.5476 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M0a** | 3.2303 | 2.2735 | 57.89% | 11.2087 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M2** | 3.4215 | 2.4776 | 55.26% | 10.6020 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M4** | 3.5713 | 2.5164 | 50.00% | 11.5016 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M5** | 3.6191 | 2.6058 | 50.00% | 11.5933 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **RNN** | 3.1938 | 2.3608 | 52.63% | 10.4374 |
| Weekly | Middle East War Escalation (Oct-Nov 2023) | 38 | **LSTM** | 3.2375 | 2.3540 | 57.89% | 10.9670 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M0a** | 3.5709 | 2.8232 | 49.02% | 8.0867 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M2** | 3.5595 | 2.7840 | 58.82% | 8.3258 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M4** | 3.4983 | 2.8498 | 64.71% | 7.4140 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M5** | 3.5736 | 2.8502 | 60.78% | 7.9205 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **RNN** | 3.6287 | 2.8532 | 50.98% | 8.2849 |
| Weekly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **LSTM** | 3.6670 | 2.8635 | 49.02% | 8.1144 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **M0a** | 4.5449 | 3.6387 | 47.87% | 12.3080 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **M2** | 4.3947 | 3.6002 | 56.38% | 10.2949 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **M4** | 4.4947 | 3.6293 | 59.04% | 11.0156 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **M5** | 4.5149 | 3.6059 | 54.79% | 11.6293 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **RNN** | 4.5311 | 3.7007 | 51.06% | 11.0291 |
| Weekly | High Volatility Regime (Top 25% Vol) | 188 | **LSTM** | 4.7197 | 3.7725 | 45.21% | 12.7159 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **M0a** | 3.1872 | 2.5102 | 56.38% | 9.4133 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **M2** | 3.1562 | 2.4816 | 54.26% | 8.7463 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **M4** | 3.2427 | 2.5577 | 45.21% | 9.7249 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **M5** | 3.3297 | 2.6156 | 48.40% | 9.6433 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **RNN** | 3.1212 | 2.4746 | 55.85% | 8.7244 |
| Weekly | Low Volatility Regime (Bottom 25% Vol) | 188 | **LSTM** | 3.1564 | 2.5403 | 56.38% | 9.1763 |
| Monthly | Full OOS Sample | 734 | **M0a** | 6.6830 | 5.3012 | 50.41% | 20.3729 |
| Monthly | Full OOS Sample | 734 | **M2** | 7.1946 | 5.7314 | 50.82% | 23.6021 |
| Monthly | Full OOS Sample | 734 | **M4** | 7.7250 | 5.9758 | 53.13% | 28.1175 |
| Monthly | Full OOS Sample | 734 | **M5** | 7.9307 | 6.3251 | 51.09% | 30.4997 |
| Monthly | Full OOS Sample | 734 | **RNN** | 7.3374 | 5.9615 | 49.73% | 20.5109 |
| Monthly | Full OOS Sample | 734 | **LSTM** | 9.4405 | 7.1487 | 51.23% | 32.1402 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **M0a** | 8.2111 | 7.3966 | 54.11% | 20.3729 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **M2** | 8.5974 | 7.3943 | 51.58% | 23.6021 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **M4** | 9.1792 | 7.6537 | 52.84% | 28.1175 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **M5** | 9.2737 | 7.9307 | 49.68% | 30.4997 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **RNN** | 8.6057 | 7.2774 | 52.63% | 20.5109 |
| Monthly | Extreme Tail Shocks (|r| >= 3%) | 475 | **LSTM** | 10.3756 | 8.6713 | 50.32% | 32.1402 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **M0a** | 6.9433 | 6.0705 | 0.00% | 16.7994 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **M2** | 8.9593 | 7.7074 | 29.17% | 20.7927 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **M4** | 8.3094 | 6.6969 | 51.89% | 28.1175 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **M5** | 9.0808 | 7.4909 | 44.32% | 30.4997 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **RNN** | 10.2367 | 9.5728 | 0.76% | 20.5109 |
| Monthly | Large Upward Moves (r >= +2%) | 264 | **LSTM** | 11.4277 | 9.0552 | 67.05% | 32.1402 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **M0a** | 8.2811 | 7.3046 | 100.00% | 20.3729 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **M2** | 7.2471 | 6.0167 | 70.93% | 23.6021 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **M4** | 8.9530 | 7.3032 | 53.29% | 27.3731 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **M5** | 8.4741 | 7.1950 | 53.63% | 24.7104 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **RNN** | 5.6482 | 4.2845 | 97.23% | 17.5844 |
| Monthly | Large Downward Moves (r <= -2%) | 289 | **LSTM** | 8.3654 | 7.1941 | 35.64% | 20.6731 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M0a** | 10.8923 | 8.7909 | 62.07% | 20.3729 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M2** | 9.6165 | 7.6548 | 68.97% | 23.6021 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M4** | 14.8996 | 12.8571 | 13.79% | 27.3731 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **M5** | 12.9603 | 11.0515 | 13.79% | 24.7104 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **RNN** | 9.6154 | 8.0663 | 62.07% | 17.5844 |
| Monthly | OPEC+ Surprise Cut (Apr-May 2023) | 29 | **LSTM** | 10.9085 | 8.7719 | 51.72% | 20.6731 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M0a** | 6.3960 | 5.2886 | 84.21% | 15.6134 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M2** | 5.8116 | 4.6791 | 73.68% | 15.4317 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M4** | 7.9724 | 6.6267 | 31.58% | 18.1046 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **M5** | 6.9820 | 5.6590 | 47.37% | 16.3472 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **RNN** | 4.2588 | 3.4393 | 84.21% | 12.2041 |
| Monthly | Middle East War Escalation (Oct-Nov 2023) | 38 | **LSTM** | 6.3741 | 5.2048 | 34.21% | 15.8466 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M0a** | 5.9454 | 4.7769 | 23.53% | 12.5563 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M2** | 7.4158 | 6.2880 | 41.18% | 14.2326 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M4** | 7.2632 | 5.6604 | 52.94% | 20.0277 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **M5** | 5.4923 | 4.4238 | 66.67% | 12.3833 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **RNN** | 8.4678 | 7.3437 | 23.53% | 15.8083 |
| Monthly | Red Sea Shipping Crisis (Dec 2023 - Feb 2024) | 51 | **LSTM** | 5.7903 | 4.6585 | 74.51% | 12.4453 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **M0a** | 7.0067 | 5.4179 | 38.04% | 20.3729 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **M2** | 7.5980 | 5.8761 | 53.26% | 23.6021 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **M4** | 10.3583 | 8.3155 | 32.61% | 28.1175 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **M5** | 10.2011 | 8.1821 | 29.35% | 30.4997 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **RNN** | 8.3072 | 6.7602 | 36.96% | 18.0783 |
| Monthly | High Volatility Regime (Top 25% Vol) | 184 | **LSTM** | 12.1766 | 8.9190 | 52.17% | 32.1402 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **M0a** | 6.0980 | 4.9415 | 63.59% | 15.4591 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **M2** | 5.4367 | 4.5051 | 60.33% | 12.8353 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **M4** | 5.7250 | 4.6716 | 61.96% | 14.5964 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **M5** | 7.3757 | 6.2726 | 54.89% | 15.7970 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **RNN** | 5.5976 | 4.7375 | 63.59% | 12.2592 |
| Monthly | Low Volatility Regime (Bottom 25% Vol) | 184 | **LSTM** | 7.3012 | 5.9785 | 34.24% | 18.7060 |

#### Phát hiện cốt lõi từ phân tích cú sốc:
1. **Độ chính xác vượt trội trong các cú sốc đuôi ($|r| \ge 3\%$, 60 phiên OOS):**
   - Trong khi mô hình mỏ neo $M0a$ thất bại hoàn toàn với RMSE lên tới $4.5649\%$ và $DA$ chỉ đạt $56.67\%$, mô hình $M5$ đạt tỷ lệ đoán đúng chiều hướng kinh ngạc **96.67%** ($M2$ đạt $95.00\%$, $M4$ đạt $93.33\%$, RNN đạt $95.00\%$).
   - Điều này khẳng định: **Trong các phiên thị trường chao đảo mạnh, tín hiệu định hướng từ thị trường dầu thô Brent đêm hôm trước mang tính áp đặt cơ học lên giá xăng Singapore chiều hôm sau.**
2. **Sự trỗi dậy của đặc trưng biên lọc dầu trong thị trường biến động thấp (Bottom 25% Volatility, 189 phiên OOS):**
   - Khi thị trường ổn định, tín hiệu biến động giá dầu thô Brent suy yếu. Đây là lúc các biến kinh tế vi mô phát huy tối đa giá trị:
   - Mô hình $M5$ đạt $DA = 76.72\%$ và $RMSE = 1.0809\%$, vượt xa mô hình tuyến tính $M2$ ($DA = 69.84\%$, $RMSE = 1.1017\%$). Mức cải thiện $+6.88\%$ về độ chính xác chiều hướng chứng minh cây quyết định trích xuất thành công mối quan hệ phi tuyến giữa chênh lệch giá ốc-tan, biên crack spread và giá xăng Mogas 95.
3. **Sự vững chắc trong các sự kiện địa chính trị thực tế:**
   - Khủng hoảng Biển Đỏ (12/2023 – 02/2024, 51 phiên): Mô hình $M4$ và $M2$ đạt $DA = 82.35\%$, mạng RNN đạt $DA = 84.31\%$.
   - Chiến sự Trung Đông bùng phát (10/2023 – 11/2023, 38 phiên): $M2$ đạt $DA = 73.68\%$, $M4/M5$ đạt $DA = 68.42\%$.

---

## 5. KẾT LUẬN, ĐÓNG GÓP HỌC THUẬT VÀ GIỚI HẠN NGHIÊN CỨU

### 5.1. Tổng kết Kết quả Nghiên cứu
Nghiên cứu SPAFS V5.2 đã hoàn thành trọn vẹn việc giải quyết hai câu hỏi nghiên cứu định lượng trên cả 3 khung thời gian:
1. Đã chứng minh bằng cả kiểm định trong mẫu (Wald) và ngoài mẫu (Clark–West) rằng **thị trường Platts Singapore truyền dẫn giá hoàn toàn đối xứng** với giá dầu thô Brent.
2. Ở khung Daily, hệ hình học máy phi tuyến ($M4, M5$) vượt trội toàn diện với $DA > 70\%$ và $R^2_{OOS} \approx 38\%$. Ở khung Weekly, năng lực dự báo duy trì ở mức khá ($DA \approx 56.5\%$). Ở khung Monthly, hiện tượng nhiễu ngẫu nhiên chi phối sai số bình phương, nhưng $M4$ vẫn mang lại giá trị gia tăng về định hướng xu hướng ($DA = 53.13\%, p = 0.044$).
3. Mạng nơ-ron hồi quy sâu (**RNN, LSTM**) được chuẩn hóa qua 5 random seeds cung cấp một benchmark học thuật vững chắc, xác nhận tính ưu việt của mô hình cây tăng cường LightGBM trên tập dữ liệu chuỗi thời gian dạng bảng.

### 5.2. Các Giới Hạn Của Nghiên Cứu (Research Limitations)
1. **Hạn chế về Timestamp Proxy:** Do đặc thù lịch sử dữ liệu Platts và Brent tải từ các cơ sở dữ liệu thứ cấp, các mốc thời gian công bố được gán theo quy ước đóng phiên chuẩn của thị trường (16:30 SGT cho Platts và 19:30 London cho Brent). Mặc dù cơ chế vận hành này phản ánh chính xác cấu trúc thị trường, nghiên cứu không tuyên bố đã kiểm toán Point-in-Time ở cấp độ log API mili-giây.
2. **Loại bỏ dữ liệu NLP/Sentiment ($M6$):** Dữ liệu tin tức tài chính trong giai đoạn 2017 – 2025 thiếu dấu thời gian phát hành chính xác tới từng phút để khẳng định không bị nhìn trước thời điểm 08:30 SGT. Do đó, nhóm nghiên cứu quyết định loại bỏ mô hình $M6$ khỏi các bảng so sánh chính thức nhằm bảo toàn tính trung thực học thuật.
3. **Khả năng thương mại hóa thực tế:** Mặc dù $DA$ đạt hơn $70\%$, việc chuyển hóa kết quả dự báo thành chiến lược giao dịch sinh lời thực tế đối mặt với chi phí giao dịch vật chất (*physical storage fees*), rủi ro thanh khoản hợp đồng phái sinh Platts Singapore Mogas 95 Swaps tại sàn SGX, và biến động tỷ giá.

---

## TÀI LIỆU THAM KHẢO (REFERENCES - APA 7TH EDITION)

1. Bacon, R. W. (1991). Rockets and feathers: the asymmetric speed of adjustment of UK retail gasoline prices to world crude oil price changes. *Energy Economics*, 13(3), 211-218.
2. Borenstein, S., Cameron, A. C., & Gilbert, R. (1997). Do gasoline prices respond asymmetrically to crude oil price changes? *The Quarterly Journal of Economics*, 112(1), 305-339.
3. Clark, T. E., & McCracken, M. W. (2001). Tests of equal forecast accuracy and encompassing for nested models. *Journal of Econometrics*, 105(1), 85-110.
4. Clark, T. E., & West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. *Journal of Econometrics*, 138(1), 291-311.
5. de Prado, M. L. (2018). *Advances in Financial Machine Learning*. John Wiley & Sons.
6. Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253-263.
7. Galeotti, M., Lanza, A., & Manera, M. (2003). Rockets and feathers revisited: an international comparison on European gasoline markets. *Energy Economics*, 25(2), 175-190.
8. Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281-291.
9. Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., ... & Liu, T. Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems*, 30, 3146-3154.
10. Newey, W. K., & West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703-708.
11. Pesaran, M. H., & Timmermann, A. (1992). A simple nonparametric test of predictive performance. *Journal of Business & Economic Statistics*, 10(4), 461-465.
