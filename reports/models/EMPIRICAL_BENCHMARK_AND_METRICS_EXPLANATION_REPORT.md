# BÁO CÁO KHOA HỌC: BENCHMARK THỰC NGHIỆM VÀ GIẢI THÍCH HỆ THỐNG MÔ HÌNH, THƯỚC ĐO ĐÁNH GIÁ (SPAFS V5.2)

**Dự án:** Hệ thống Dự báo Phân tích Giá Xăng Dầu và Truyền dẫn Bất đối xứng (SPAFS V5.2)  
**Tác giả thực hiện:** Nhóm Nghiên cứu Đề tài / Sinh viên thực hiện  
**Phạm vi báo cáo:** Đánh giá Thực nghiệm Các Mô hình từ $M0a$ đến $M4$ trên Dữ liệu Thực tế (2008–2025)  
**Tình trạng kiểm chứng:** 100% Số liệu được tính toán và lưu vết qua Artifacts (SHA-256 Manifest Verified)  

---

## 1. TỔNG QUAN PHƯƠNG PHÁP LUẬN VÀ QUY TRÌNH THỰC NGHIỆM

Để đảm bảo tính trung thực học thuật, loại trừ hoàn toàn hiện tượng thiên kiến nhìn trước tương lai (*Lookahead Bias*) và hiện tượng rò rỉ dữ liệu (*Data Leakage*), toàn bộ các mô hình trong báo cáo này được đánh giá thông qua hai luồng nghiên cứu độc lập:

1. **Luồng 1 (Stream 1 - Phân hệ Kinh tế lượng Chuỗi thời gian 2008–2025):**
   - **Mục tiêu:** Trả lời Câu hỏi Nghiên cứu 1 (RQ1) về bản chất truyền dẫn giá từ dầu thô Brent sang giá xăng thành phẩm Singapore (Platts Mogas 95) và kiểm định hiện tượng bất đối xứng "Tên lửa và Lông vũ" (*Rockets and Feathers*).
   - **Tập dữ liệu:** $N = 4.425$ phiên giao dịch hàng ngày đồng bộ liên tục suốt 18 năm (từ ngày 02/05/2008 đến ngày 30/12/2025).
   - **Phương pháp đánh giá ngoài mẫu:** Kiểm định cuốn chiếu tịnh tiến (*Expanding Window Walk-Forward 1-Step-Ahead*). Khởi động ước lượng ban đầu tại $\tau_0 = 3.500$ phiên giao dịch, thực hiện ước lượng lại và dự báo cuốn chiếu cho từng phiên tiếp theo, tạo ra tập kiểm định thuần ngoài mẫu (*Pure Out-of-Sample*) gồm **925 phiên giao dịch**.

2. **Luồng 2 (Stream 2 - Phân hệ Học máy Phi tuyến 2017–2025):**
   - **Mục tiêu:** Đánh giá năng lực của các mô hình học máy dạng cây quyết định (*Gradient Boosted Decision Trees*) trong việc nắm bắt cấu trúc phi tuyến và động lực giá ngắn hạn.
   - **Tập dữ liệu:** $N = 2.254$ phiên giao dịch đồng bộ từ ngày 03/01/2017 đến ngày 30/12/2025.
   - **Phương pháp đánh giá ngoài mẫu:** Walk-Forward với cửa sổ khởi động $1.500$ phiên và chu kỳ tái ước lượng tham số (*Refit Frequency*) định kỳ 20 phiên giao dịch (tương đương chu kỳ 1 tháng giao dịch), tạo ra **754 phiên kiểm định ngoài mẫu**.

---

## 2. ĐẶC TẢ CHI TIẾT CÁC MÔ HÌNH ĐÃ THỰC HIỆN ($M0a \to M4$)

Mỗi mô hình được thiết kế có một vai trò học thuật riêng biệt, đi từ các chuẩn đối sánh cơ sở (*Baselines*) đến các mô hình kinh tế lượng động và mô hình học máy phi tuyến.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │               HỆ THỐNG MÔ HÌNH SPAFS V5.2               │
                    └─────────────────────────────────────────────────────────┘
                                                 │
         ┌───────────────────────────────────────┴───────────────────────────────────────┐
         ▼                                                                               ▼
  [STREAM 1: KINH TẾ LƯỢNG (2008-2025)]                                  [STREAM 2: HỌC MÁY (2017-2025)]
  ├── M0a: Naive Zero Return (Martingale Baseline)                        └── M4: Technical LightGBM (10-Seed Ensemble)
  ├── M0b: Naive Direction (Momentum Baseline)
  ├── M1 : ARMA(1,1) Univariate (MLE / Kalman Filter)
  ├── M2 : Linear Dynamic Symmetric ADL (HAC)
  └── M3 : Asymmetric ADL (RQ1 Core - Rockets & Feathers)
```

### 2.1. Mô hình M0a: Naive Zero Return (Chuẩn ngẫu nhiên Martingale)
* **Bản chất khoa học:** Mô hình đại diện cho Giả thuyết Bước đi ngẫu nhiên (*Random Walk Hypothesis*). Nếu giá tài sản tuân theo bước đi ngẫu nhiên, kỳ vọng tỷ suất sinh lợi tốt nhất cho ngày mai là 0.
* **Đầu vào (Input):** Không sử dụng bất kỳ biến đặc trưng nào ($X = \emptyset$).
* **Đầu ra (Output):** Dự báo tỷ suất sinh lợi điểm $\hat{r}_{t+1} = 0.0$.
* **Vai trò:** Đóng vai trò là "mỏ neo chuẩn" để tính toán chỉ số $OOS\text{-}R^2$ (Campbell & Thompson, 2008). Bất kỳ mô hình nào có sai số lớn hơn $M0a$ đều bị coi là không có giá trị thực tiễn.

### 2.2. Mô hình M0b: Naive Directional Momentum (Chuẩn định hướng quán tính)
* **Bản chất khoa học:** Dự báo xu hướng tương lai đơn thuần dựa trên chiều biến động của ngày hiện tại (nếu hôm nay tăng thì ngày mai tiếp tục tăng).
* **Đầu vào (Input):** Tỷ suất sinh lợi phiên hiện tại của Mogas 95 (`mg95_return_pct`, ký hiệu $r_t$).
* **Đầu ra (Output):** Nhãn hướng đi nhị phân $\hat{D}_{t+1} = \mathbb{I}(r_t > 0) \in \{0, 1\}$.
* **Vai trò:** Chuẩn cơ sở đánh giá độ chính xác phân loại hướng (*Directional Accuracy*) và năng lực định thời thị trường.

### 2.3. Mô hình M1: ARMA(1,1) Đơn biến (Univariate Time Series)
* **Bản chất khoa học:** Mô hình tự hồi quy trung bình trượt đơn biến kết hợp cả thành phần quán tính quá khứ ($AR$) và thành phần phản ứng trước các cú sốc sai số dự báo trễ ($MA$):
  $$r_{t+1} = c + \phi_1 r_t + \theta_1 \epsilon_t + \epsilon_{t+1}$$
* **Đầu vào (Input):** Chuỗi thời gian tỷ suất sinh lợi nội sinh `mg95_return_pct`.
* **Phương pháp ước lượng:** Ước lượng bằng Hợp lý Cực đại Gauss (*Gaussian Maximum Likelihood Estimation - MLE*) thông qua thuật toán lọc trạng thái Kalman (*Kalman Filter*), tuyệt đối không dùng hồi quy OLS tĩnh.
* **Đầu ra (Output):** Dự báo điểm tỷ suất sinh lợi 1-bước-tới $\hat{r}_{t+1}$.
* **Vai trò:** Đánh giá xem bản thân chuỗi giá xăng có cấu trúc tự tương quan tuyến tính nội tại đủ mạnh để tự dự báo chính nó hay không.

### 2.4. Mô hình M2: Linear Dynamic Symmetric ADL (Chuẩn động đối xứng)
* **Bản chất khoa học:** Mô hình hồi quy động tuyến tính kết hợp cả quán tính nội sinh, tác động ngoại sinh từ dầu thô Brent và cơ chế mỏ neo hồi quy trung bình:
  $$r_{MG95, t+1} = \alpha + \phi_1 r_{MG95, t} + \phi_2 r_{MG95, t-1} + \beta_0 r_{Brent, t} + \beta_1 r_{Brent, t-1} + \lambda \, Spread_{t-1} + \epsilon_{t+1}$$
* **Đầu vào (Input - 5 biến):**
  1. `mg95_return_pct` ($r_{MG95, t}$): Tỷ suất sinh lợi xăng phiên hiện tại.
  2. `mg95_return_lag1` ($r_{MG95, t-1}$): Tỷ suất sinh lợi xăng trễ 1 ngày.
  3. `brent_return_pct_aligned` ($r_{Brent, t}$): Tỷ suất sinh lợi dầu Brent đã căn chỉnh múi giờ kết thúc phiên Singapore.
  4. `brent_return_lag1` ($r_{Brent, t-1}$): Tỷ suất sinh lợi dầu Brent trễ 1 ngày.
  5. `spread_mg95_brent_lag1` ($Spread_{t-1} = P_{MG95, t-1} - P_{Brent, t-1}$): Chênh lệch giá lọc dầu (Crack Spread) trễ 1 ngày đóng vai trò cơ chế sửa sai (Error Correction Anchor).
* **Phương pháp ước lượng:** Hồi quy OLS với ma trận hiệp phương sai **Newey-West HAC (5 trễ)** để khắc phục hiện tượng tự tương quan và phương sai thay đổi của phần dư.
* **Đầu ra (Output):** Dự báo điểm $\hat{r}_{t+1}$ và phân loại hướng $\hat{D}_{t+1} = \mathbb{I}(\hat{r}_{t+1} > 0)$.
* **Vai trò:** Chuẩn đối xứng tối ưu của nhánh kinh tế lượng.

### 2.5. Mô hình M3: Asymmetric Autoregressive Distributed Lag (Mô hình Cốt lõi RQ1)
* **Bản chất khoa học:** Mô hình mở rộng từ $M2$ nhằm kiểm định hiện tượng phi đối xứng truyền dẫn giá (Rockets and Feathers). Cú sốc dầu thô tại ngày $t$ và $t-1$ được bóc tách thành nhánh tăng giá ($r^+ = \max(r, 0)$) và nhánh giảm giá ($r^- = \min(r, 0)$):
  $$\begin{aligned}
  r_{MG95, t+1} = \alpha &+ \phi_1 r_{MG95, t} + \phi_2 r_{MG95, t-1} \\
  &+ \beta_0^+ r_{Brent, t}^+ + \beta_0^- r_{Brent, t}^- + \beta_1^+ r_{Brent, t-1}^+ + \beta_1^- r_{Brent, t-1}^- \\
  &+ \lambda \, Spread_{t-1} + \epsilon_{t+1}
  \end{aligned}$$
* **Đầu vào (Input - 7 biến):**
  1. `mg95_return_pct` ($r_{MG95, t}$)
  2. `mg95_return_lag1` ($r_{MG95, t-1}$)
  3. `brent_return_pos` ($r_{Brent, t}^+$): Nhánh sốc tăng dầu thô ngày $t$.
  4. `brent_return_neg` ($r_{Brent, t}^-$): Nhánh sốc giảm dầu thô ngày $t$.
  5. `brent_return_pos_lag1` ($r_{Brent, t-1}^+$): Nhánh sốc tăng dầu thô ngày $t-1$.
  6. `brent_return_neg_lag1` ($r_{Brent, t-1}^-$): Nhánh sốc giảm dầu thô ngày $t-1$.
  7. `spread_mg95_brent_lag1` ($Spread_{t-1}$).
* **Đầu ra (Output):** Dự báo tỷ suất sinh lợi $\hat{r}_{t+1}$ và kết quả 3 bài kiểm định giả thuyết Wald chính tắc:
  - $H_0^{(1)}: \beta_0^+ = \beta_0^-$ (Đối xứng tức thời 24h).
  - $H_0^{(2)}: \beta_0^+ + \beta_1^+ = \beta_0^- + \beta_1^-$ (Đối xứng tích lũy 2 ngày).
  - $H_0^{(joint)}: \beta_0^+ = \beta_0^- \land \beta_1^+ = \beta_1^-$ (Mô hình $M3$ lồng ghép hoàn toàn vào $M2$, bậc tự do $df=2$).

### 2.6. Mô hình M4: Technical LightGBM Regressor (Học máy Đa hạt giống)
* **Bản chất khoa học:** Mô hình học máy phi tuyến dựa trên thuật toán tăng cường độ dốc cây quyết định (*Gradient Boosted Decision Trees - GBDT*). Nhằm tránh hiện tượng nhạy cảm với hạt giống ngẫu nhiên (*Seed Instability*), mô hình tích hợp **Ensemble trung bình qua 10 hạt giống độc lập** (Seeds: 42, 101, 202, 303, 404, 505, 606, 707, 808, 909).
* **Đầu vào (Input - 10 đặc trưng kỹ thuật):**
  - Nhóm tỷ suất sinh lợi Mogas: `mg95_return_pct`, `mg95_return_lag1`, `mg95_return_lag2`, `mg95_return_lag3`.
  - Nhóm tỷ suất sinh lợi Brent: `brent_return_pct_aligned`, `brent_return_lag1`, `brent_return_lag2`, `brent_return_lag3`.
  - Nhóm rủi ro và cú sốc: `vol_mg95_30d` (Độ biến động 30 ngày qua), `economic_shock_flag` (Cờ nhị phân đánh dấu phiên biến động cực đoan).
* **Cấu hình chống Overfitting:** Tốc độ học nhỏ (`learning_rate=0.03`), số lá cây giới hạn (`num_leaves=15`), lấy mẫu ngẫu nhiên hàng (`subsample=0.8`) và cột (`colsample_bytree=0.8`).
* **Đầu ra (Output):** Dự báo điểm ngoài mẫu $\hat{r}_{t+1}$, nhãn hướng $\hat{D}_{t+1}$, và bảng xếp hạng tầm quan trọng đặc trưng (*Gain & Split Feature Importance*).

---

## 3. GIẢI THÍCH CHI TIẾT TỪNG THƯỚC ĐO ĐÁNH GIÁ (METRICS & TESTS)

Để phục vụ công tác báo cáo khoa học, các thước đo được phân loại thành 4 nhóm nghiệp vụ rõ ràng:

### 3.1. Nhóm Thước đo Sai số Dự báo Điểm (Point Forecast Metrics)

1. **RMSE (Root Mean Squared Error - Căn bậc hai Sai số Toàn phương Trung bình):**
   $$\text{RMSE} = \sqrt{\frac{1}{T} \sum_{t=1}^T (y_t - \hat{y}_t)^2}$$
   - **Ý nghĩa:** Đo lường độ lệch trung bình giữa giá trị thực tế và giá trị dự báo, có cùng đơn vị tính với dữ liệu (ở đây là phần trăm %).
   - **Đặc tính:** Phạt rất nặng các sai số dự báo lớn do có phép bình phương sai số.
   - **Cách đọc:** Giá trị **càng nhỏ càng tốt**.

2. **MAE (Mean Absolute Error - Sai số Tuyệt đối Trung bình):**
   $$\text{MAE} = \frac{1}{T} \sum_{t=1}^T |y_t - \hat{y}_t|$$
   - **Ý nghĩa:** Đo lường độ lệch trung bình tuyệt đối mà không phóng đại các sai số cực trị.
   - **Cách đọc:** Giá trị **càng nhỏ càng tốt**.

3. **In-sample $R^2$ (Hệ số Xác định Trong Mẫu):**
   $$R^2 = 1 - \frac{\sum (y_t - \hat{y}_t)^2}{\sum (y_t - \bar{y})^2}$$
   - **Ý nghĩa:** Tỷ lệ phần trăm biến thiên của chuỗi biến phụ thuộc được giải thích bởi các biến độc lập trong quá trình khớp mô hình.
   - **Cách đọc:** Dao động từ 0 đến 1 (hoặc âm nếu mô hình tệ hơn đường trung bình). **Càng gần 1 càng tốt**.

4. **Campbell–Thompson $OOS\text{-}R^2$ (Hệ số Xác định Ngoài Mẫu):**
   $$OOS\text{-}R^2 = 1 - \frac{\text{MSE}_{\text{model}}}{\text{MSE}_{\text{benchmark}}}$$
   - **Ý nghĩa:** Thước đo tiêu chuẩn vàng trong kinh tế lượng tài chính (Campbell & Thompson, 2008). Đo lường tỷ lệ phần trăm sai số mà mô hình nghiên cứu đã cắt giảm được so với mô hình cơ sở $M0a$ (Naive Zero).
   - **Cách đọc:** 
     - $OOS\text{-}R^2 > 0$: Mô hình dự báo **tốt hơn** bước đi ngẫu nhiên Martingale.
     - $OOS\text{-}R^2 \le 0$: Mô hình dự báo **kém hơn** việc đoán giá trị 0; không có giá trị ứng dụng.

---

### 3.2. Nhóm Thước đo Định hướng Thị trường (Directional & Market Timing Metrics)

1. **Directional Accuracy (DA - Tỷ lệ Dự báo Đúng Chiều Biến động):**
   $$\text{DA} = \frac{1}{T} \sum_{t=1}^T \mathbb{I}(\text{sgn}(y_t) = \text{sgn}(\hat{y}_t)) \times 100\%$$
   - **Ý nghĩa:** Tỷ lệ phần trăm số ngày mà mô hình đoán trúng giá tăng hay giá giảm. Có ý nghĩa quyết định đối với các nhà giao dịch và doanh nghiệp xăng dầu phòng ngừa rủi ro.
   - **Ngưỡng chuẩn:** Một mô hình đoán ngẫu nhiên sẽ có $\text{DA} \approx 50\%$. Do đó, mô hình đạt $\text{DA} > 60\%$ được coi là tốt, và $\text{DA} \ge 70\%$ là mức xuất sắc trong tài chính tần suất ngày.

2. **Matthews Correlation Coefficient (MCC - Hệ số Tương quan Matthews):**
   $$\text{MCC} = \frac{TP \times TN - FP \times FN}{\sqrt{(TP + FP)(TP + FN)(TN + FP)(TN + FN)}}$$
   - **Ý nghĩa:** Đo lường chất lượng phân loại nhị phân (Tăng/Giảm) ngay cả khi tập dữ liệu bị mất cân bằng số ngày tăng/giảm.
   - **Cách đọc:** Dao động từ $-1$ đến $+1$.
     - $\text{MCC} = 0$: Phân loại hoàn toàn ngẫu nhiên.
     - $\text{MCC} > 0.3$: Tương quan định hướng mạnh mẽ.

3. **Kiểm định Thị trường Pesaran–Timmermann (PT-Test 1992):**
   - **Bản chất:** Kiểm định phi tham số kiểm tra xem năng lực dự báo đúng hướng của mô hình có thực sự xuất phát từ khả năng nắm bắt thông tin thị trường hay chỉ là sự may rủi ngẫu nhiên độc lập.
   - **Thống kê:** $PT \sim \mathcal{N}(0, 1)$ tuân theo phân phối chuẩn tắc dưới giả thuyết vô hiệu $H_0$ (dự báo và thực tế độc lập nhau).
   - **Cách đọc:** Giá trị $PT > 1.96$ tương ứng với $p\text{-value} < 0.05$, bác bỏ giả thuyết may rủi và khẳng định mô hình có năng lực định thời thị trường thực chất.

---

### 3.3. Nhóm Kiểm định Thống kê So sánh Cặp Mô hình (Pairwise Comparative Tests)

1. **Kiểm định Diebold–Mariano (1995) với Hiệu chỉnh Harvey–Leybourne–Newbold (HLN 1997):**
   - **Mục tiêu:** Kiểm định xem chênh lệch hàm tổn thất (bình phương sai số) giữa mô hình ứng viên và mô hình chuẩn có khác 0 một cách có ý nghĩa thống kê hay không:
     $$d_t = e_{\text{candidate}, t}^2 - e_{\text{benchmark}, t}^2$$
   - **Hiệu chỉnh HLN (1997):** Nhân thêm hệ số hiệu chỉnh cỡ mẫu nhỏ để triệt tiêu thiên kiến cỡ mẫu hữu hạn. Sử dụng nhân Bartlett để tính phương sai dài hạn (HAC).
   - **Quy tắc bác bỏ:** Thống kê $DM < -1.645$ (kiểm định 1 phía) với $p < 0.05$ cho thấy mô hình ứng viên vượt trội hơn mô hình chuẩn ngoài mẫu một cách có ý nghĩa thống kê.

2. **Kiểm định Clark–West (2007) dành cho Mô hình Lồng nhau (Nested Models):**
   - **Bản chất kinh tế lượng:** Khi so sánh hai mô hình lồng nhau (ví dụ $M1$ lồng trong $M2$, hoặc $M2$ lồng trong $M3$), mô hình lớn hơn có nhiều tham số hơn nên sẽ chịu thêm "nhiễu ước lượng tham số" (*Parameter Estimation Noise*), làm thổi phồng sai số MSPE của nó.
   - **Hiệu chỉnh Clark-West:** Khấu trừ lượng nhiễu này ra khỏi hàm chênh lệch tổn thất:
     $$f_t = (y_t - \hat{y}_{\text{small}, t})^2 - \left[ (y_t - \hat{y}_{\text{large}, t})^2 - (\hat{y}_{\text{small}, t} - \hat{y}_{\text{large}, t})^2 \right]$$
   - **Quy tắc bác bỏ:** Thống kê $CW > 1.645$ với $p < 0.05$ chứng minh các biến bổ sung của mô hình lớn mang lại thông tin thực chất chứ không phải do ăn may.

---

### 3.4. Nhóm Chẩn đoán Đa cộng tuyến và Phần dư (Diagnostics)

1. **Hệ số Phóng đại Phương sai (VIF - Variance Inflation Factor):**
   $$\text{VIF}_j = \frac{1}{1 - R_j^2}$$
   - **Ý nghĩa:** Đo lường mức độ biến độc lập thứ $j$ bị giải thích bởi các biến độc lập còn lại trong ma trận $X$.
   - **Ngưỡng quy chuẩn:** $\text{VIF} < 5.0$ là hoàn toàn an toàn; $\text{VIF} > 10.0$ là dấu hiệu đa cộng tuyến nghiêm trọng.

2. **Số Điều kiện Ma trận (Condition Number):**
   $$\kappa(X) = \frac{\sigma_{\max}(X)}{\sigma_{\min}(X)}$$
   - **Ý nghĩa:** Tỷ số giữa giá trị kỳ dị lớn nhất và nhỏ nhất của ma trận thiết kế.
   - **Ngưỡng quy chuẩn:** $\kappa(X) < 30.0$ cho thấy ma trận ổn định số học; $\kappa(X) \ge 30.0$ cảnh báo rủi ro ma trận gần suy biến làm sai lệch kiểm định Wald.

3. **Kiểm định Jarque–Bera (JB) & Engle's ARCH-LM:**
   - **Jarque-Bera:** Kiểm tra tính phân phối chuẩn của phần dư. Với dữ liệu tài chính, phân phối thường có đuôi dày (*Fat Tails*) và nhọn (*Excess Kurtosis*).
   - **ARCH-LM:** Kiểm tra hiệu ứng cụm biến động (*Volatility Clustering*). Nếu phần dư có hiệu ứng ARCH, việc dùng sai số chuẩn cổ điển OLS sẽ bị sai lệch nghiêm trọng, bắt buộc phải dùng sai số Newey-West HAC.

---

## 4. BẢNG TỔNG HỢP BENCHMARK THỰC NGHIỆM ĐẦY ĐỦ

### BẢNG 1: BẢNG XẾP HẠNG NGOÀI MẪU STREAM 1 ($M0a \to M3$)
*(Đánh giá Walk-Forward trên 925 phiên giao dịch thực tế ngoài mẫu; Nguồn: `stream1_econometric_leaderboard.csv`)*

| Model ID | Tên mô hình | RMSE | MAE | $OOS\text{-}R^2$ (%) | Directional Accuracy | MCC | Pesaran–Timmermann | $PT$ $p$-value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$M0a$** | Naive Zero Return ($r=0$) | **2.1248** | 1.5497 | 0.000% *(Chuẩn)* | 48.22% | 0.0000 | 0.000 | 1.0000 |
| **$M0b$** | Naive Direction ($\mathbb{I}_{r_t>0}$) | 2.2267 | 1.6267 | -8.575% | 51.57% | 0.0301 | 0.914 | 0.3609 |
| **$M1$** | ARMA(1,1) Univariate (MLE) | 2.1249 | 1.5502 | -0.017% | 48.32% | -0.0044 | -0.047 | 0.9621 |
| **$M2$** | Linear Dynamic Symmetric (HAC) | **1.7092** | **1.2342** | **+35.293%** | 70.05% | 0.4031 | **12.224** | **$< 0.0001$** |
| **$M3$** | Asymmetric ADL (HAC) | 1.7104 | 1.2336 | +35.197% | **70.16%** | **0.4054** | **12.291** | **$< 0.0001$** |

---

### BẢNG 2: KẾT QUẢ KIỂM ĐỊNH SO SÁNH CẶP (PAIRWISE COMPARATIVE TESTS)
*(Nguồn: `stream1_pairwise_tests.json`)*

| Cặp so sánh | Giả thuyết vô hiệu $H_0$ | DM-HLN Stat | DM $p$-value | Clark-West Stat | CW $p$-value | Kết luận thống kê |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **$M1$ vs $M0a$** | $M1$ không giảm tổn thất so với $M0a$ | $+0.8357$ | 0.7982 | $-0.7808$ | 0.7825 | **Không bác bỏ $H_0$** ($M1$ không hơn bước đi ngẫu nhiên) |
| **$M2$ vs $M1$** | $M2$ không hơn ARMA đơn biến $M1$ | **$-7.0059$** | **$2.36 \times 10^{-12}$** | **$+10.6329$** | **$< 0.0001$** | **Bác bỏ $H_0$ triệt để** ($M2$ vượt trội áp đảo $M1$) |
| **$M3$ vs $M2$** | $M3$ không cải thiện dự báo so với $M2$ | $+0.5824$ | 0.7198 | $-0.3768$ | 0.6468 | **Không bác bỏ $H_0$** (Phi đối xứng không cải thiện OOS) |

---

### BẢNG 3: KẾT QUẢ KIỂM ĐỊNH GIẢ THUYẾT KINH TẾ LƯỢNG RQ1 ($M3$)
*(Mẫu toàn phần $N = 4.425$ phiên, Newey-West HAC 5 trễ; Nguồn: `rq1_wald_tests.json`)*

| Giả thuyết kiểm định | Công thức ràng buộc | Ước lượng thực tế | Wald Stat ($W_F$) | $df$ | $p$-value | Kết luận học thuật |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **$H_0^{(1)}$: Đối xứng tức thời** | $\beta_0^+ = \beta_0^-$ | $\beta_0^+ = 0.6704, \beta_0^- = 0.6741$ | **0.0035** | 1 | **0.9530** | **Không bác bỏ $H_0$** (Truyền dẫn đối xứng trong 24h) |
| **$H_0^{(2)}$: Đối xứng lũy kế** | $\sum \beta^+ = \sum \beta^-$ | $\sum \beta^+ = 0.7934, \sum \beta^- = 0.7417$ | **0.2240** | 1 | **0.6360** | **Không bác bỏ $H_0$** (Truyền dẫn đối xứng trong 48h) |
| **$H_0^{(joint)}$: Thu gọn về $M2$** | $\beta_0^+ = \beta_0^- \land \beta_1^+ = \beta_1^-$ | Kiểm định đồng thời 2 ràng buộc | **0.2481** | 2 | **0.8833** | **Không bác bỏ $H_0$** (Mô hình đối xứng $M2$ lồng ghép $M3$) |

---

### BẢNG 4: KẾT QUẢ THỰC NGHIỆM MÔ HÌNH HỌC MÁY $M4$ (STREAM 2)
*(Mẫu 2017–2025: $N = 2.254$; Walk-Forward 754 phiên OOS; Nguồn: `stream2_m4_leaderboard.json`)*

| Thước đo | Giá trị thực nghiệm | Diễn giải ý nghĩa |
| :--- | :---: | :--- |
| **Số phiên ngoài mẫu ($N_{OOS}$)** | **754** | Giai đoạn kiểm định từ năm 2023 đến hết tháng 12/2025 |
| **RMSE ngoài mẫu** | **1.4221** | Sai số bình phương trung bình trên tập kiểm định Stream 2 |
| **MAE ngoài mẫu** | **1.0712** | Sai số tuyệt đối trung bình ~1.07% |
| **In-sample $R^2$** | **0.3759** | Mô hình giải thích 37.59% phương sai trong mẫu |
| **Directional Accuracy (DA)** | **70.82%** | Đoán đúng chiều tăng/giảm đạt gần 71% |
| **Hệ số Matthews (MCC)** | **0.4156** | Năng lực phân loại định hướng rất tích cực ($> 0.4$) |
| **Pesaran–Timmermann ($PT$)** | **11.274** | $PT$ cực lớn ($p\text{-value} = 0.0$), định thời thị trường xuất sắc |

**Đóng góp thông tin của đặc trưng (Gain Importance trung bình qua 10 seeds):**
1. `brent_return_pct_aligned`: **$68.742,70$** (chiếm đa số đóng góp)
2. `mg95_return_pct`: **$13.747,54$**
3. `mg95_return_lag1`: **$7.772,61$**
4. `mg95_return_lag3`: **$6.507,96$**
5. `mg95_return_lag2`: **$5.957,26$**
6. `brent_return_lag1`: **$5.234,81$**
7. `vol_mg95_30d`: **$3.881,14$**
8. `brent_return_lag3`: **$3.419,09$**
9. `brent_return_lag2`: **$3.190,45$**
10. `economic_shock_flag`: **$1.890,22$**

---

### BẢNG 5: CHẨN ĐOÁN MA TRẬN VÀ ĐẶC TÍNH PHẦN DƯ ($M1, M2, M3$)
*(Nguồn: `multicollinearity_diagnostics.json` & `residual_diagnostics.json`)*

1. **Chẩn đoán Đa cộng tuyến (Multicollinearity):**
   - **Mô hình $M2$:** Số điều kiện $\kappa = 2.35 \ll 30.0$; VIF lớn nhất = $1.78$; VIF của mỏ neo $Spread_{t-1} = 1.05$.
   - **Mô hình $M3$:** Số điều kiện $\kappa = 2.37 \ll 30.0$; VIF lớn nhất = $1.78$; VIF của mỏ neo $Spread_{t-1} = 1.07$.
   - *Kết luận:* Hệ thống hoàn toàn không có đa cộng tuyến. Mỏ neo chênh lệch giá không hề làm nhiễu sai số Newey-West.

2. **Chẩn đoán Phần dư:**
   - **Phân phối:** Đuôi rất dày (Excess Kurtosis của $M1 = 15.93, M2 = 19.20, M3 = 18.94$). Kiểm định Jarque-Bera có $p = 0.0$, bác bỏ triệt để phân phối chuẩn.
   - **Hiệu ứng ARCH:** Kiểm định Engle ARCH-LM đạt thống kê cực lớn ($LM > 1.100, p < 10^{-200}$), chứng minh phần dư có hiệu ứng cụm biến động mạnh.
   - *Kết luận:* Khẳng định việc sử dụng ma trận hiệp phương sai **Newey-West HAC** là bắt buộc và hoàn toàn chính xác về mặt kinh tế lượng.

---

## 5. DIỄN GIẢI HỌC THUẬT & KẾT LUẬN KHOA HỌC DÀNH CHO BÁO CÁO HỘI ĐỒNG

1. **Về Bản chất Thị trường Bán buôn Quốc tế (Trả lời RQ1):**
   Kết quả kiểm định Wald $p = 0.9530$ chỉ ra rằng thị trường bán buôn Singapore (Platts Mogas 95) **truyền dẫn đối xứng hoàn hảo** với biến động giá dầu thô Brent. Các hiện tượng "tăng nhanh giảm chậm" thường thấy trên truyền thông nếu có xảy ra ở Việt Nam thì đó là đặc thù của khâu bán lẻ nội địa (do chu kỳ điều hành và trích lập Quỹ BOG), chứ không phải do giá bán buôn quốc tế truyền dẫn thiên lệch.

2. **Về Năng lực Dự báo Ngoài mẫu:**
   - Chuỗi giá xăng đơn biến mang tính chất Martingale (bước đi ngẫu nhiên), các mô hình ARMA không thể tự dự báo được.
   - Việc bổ sung biến giá dầu thô Brent đã căn chỉnh múi giờ và mỏ neo chênh lệch giá lọc dầu giúp mô hình $M2$ đạt bước nhảy vọt: giảm 20% sai số RMSE, đạt $OOS\text{-}R^2 = +35.29\%$ và độ chính xác dự báo hướng $70.05\%$.

3. **Về Nguyên lý Dao cạo Occam trong Lựa chọn Mô hình:**
   Mô hình $M3$ tuy có cấu trúc phi đối xứng phức tạp hơn nhưng không mang lại lợi thế ngoài mẫu so với $M2$ (RMSE $M2 = 1.7092$ tốt hơn $M3 = 1.7104$; AIC/BIC của $M2$ đều thấp hơn). Do đó, **$M2$ được khẳng định là mô hình kinh tế lượng chuẩn mực và hiệu quả nhất**.

4. **Về Mô hình Học máy $M4$:**
   LightGBM nắm bắt rất tốt động lực phi tuyến với tỷ lệ đoán hướng đạt **$70.82\%$**. Biến dầu thô Brent căn chỉnh múi giờ đóng vai trò quyết định với hơn $68.000$ điểm Gain Importance.

Báo cáo này cung cấp đầy đủ luận cứ toán học và số liệu thực nghiệm đã được kiểm chứng độc lập, sẵn sàng phục vụ trình bày trước hội đồng khoa học và thầy cô hướng dẫn.
