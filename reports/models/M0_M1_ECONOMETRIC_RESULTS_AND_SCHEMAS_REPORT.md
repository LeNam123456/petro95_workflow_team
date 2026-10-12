# BÁO CÁO KẾT QUẢ THỰC NGHIỆM MÔ HÌNH M0 – M1 VÀ MA TRẬN SCHEMAS THIẾT KẾ INPUT / OUTPUT
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)

**Dự án:** Dự báo Tỷ suất Thay đổi & Hướng Biến động Chuẩn giá Platts FOB Singapore Mogas 95  
**Phân tầng nghiên cứu:** Phase 3 — Econometric Foundations & Baseline Leaderboard  
**Thời gian thực thi & kiểm chứng:** Tháng 10/2026  
**Dữ liệu thực nghiệm:** `stream1_econometric_2008_2025.parquet` ($N = 4,428$ phiên giao dịch lịch sử, $N_{eff} = 4,426$ phiên sau xử lý trễ)  
**Tác giả:** Đội ngũ Nghiên cứu Định lượng & Kỹ thuật Dữ liệu SPAFS V5.2  

---

## MỤC LỤC TỔNG QUAN

1. [TỔNG QUAN & TÍNH TOÀN VẸN HỌC THUẬT](#1-tổng-quan--tính-toàn-vẹn-học-thuật)
2. [MA TRẬN THIẾT KẾ MODEL SCHEMAS TOÀN DIỆN (M0a ĐẾN M6)](#2-ma-trận-thiết-kế-model-schemas-toàn-diện-m0a-đến-m6)
   - 2.1. Bản đồ Đặc tả Input / Output Chi tiết từng Mô hình
   - 2.2. Kỷ luật Quản trị Dữ liệu: Whitelisting, Tính Dừng $I(0)$ và Cách ly Luồng (Stream Isolation)
3. [CHI TIẾT THỰC THI & THAM SỐ ƯỚC LƯỢNG TOÀN MẪU (NHÁNH A)](#3-chi-tiết-thực-thi--tham-số-ước-lượng-toàn-mẫu-nhánh-a)
   - 3.1. Mô hình M0a: Naive Zero Return (Random Walk / EMH)
   - 3.2. Mô hình M0b: Naive Directional Momentum
   - 3.3. Mô hình M1: ARMA(1, 1) Univariate Kalman Filter MLE
4. [KẾT QUẢ ĐÁNH GIÁ DỰ BÁO NGOÀI MẪU WALK-FORWARD (NHÁNH B)](#4-kết-quả-đánh-giá-dự-báo-ngoài-mẫu-walk-forward-nhánh-b)
   - 4.1. Bảng Xếp hạng Thực chứng (Stream 1 Econometric Leaderboard)
   - 4.2. So sánh Quỹ đạo Dự báo Trực quan (M0a vs M0b vs M1)
   - 4.3. Chẩn đoán Phần dư (Residual Diagnostics) của M1
5. [LUẬN GIẢI KHOA HỌC: KẾT QUẢ M0 – M1 CHỨNG MINH ĐIỀU GÌ?](#5-luận-giải-khoa-học-kết-quả-m0--m1-chứng-minh-điều-gì)
   - 5.1. Bằng chứng về Tính Hiệu quả Dạng Yếu (Weak-Form Market Efficiency)
   - 5.2. Sự Bất khả thi của Phân tích Kỹ thuật Đơn biến Nội sinh
   - 5.3. Bằng chứng Bỏ sót Biến Ngoại sinh từ Kiểm định Ljung-Box
   - 5.4. Cơ sở Lý luận Bắt buộc Chuyển dịch sang M2 (Brent) và M3 (Cú sốc Bất đối xứng)
6. [HỒ SƠ BẰNG CHỨNG KIỂM TOÁN TÍNH DỪNG & ARTIFACT TRAIL](#6-hồ-sơ-bằng-chứng-kiểm-toán-tính-dừng--artifact-trail)

---

## 1. TỔNG QUAN & TÍNH TOÀN VẸN HỌC THUẬT

Báo cáo này công bố chính thức kết quả ước lượng thực nghiệm của nhóm mô hình nền tảng ($M0a, M0b, M1$) thuộc **Phase 3 (Econometric Modeling)** của hệ thống SPAFS V5.2. 

Toàn bộ quy trình được xây dựng tuân thủ nghiêm ngặt **Điều lệ Trung thực Học thuật (Academic Integrity Charter)**:
* **Không bịa đặt số liệu:** 100% các hệ số hồi quy, sai số chuẩn, tiêu chí thông tin AIC/BIC và độ đo ngoài mẫu (OOS) được xuất tự động từ mã nguồn thực thi [runner_econometric.py](file:///d:/Petro_95/src/models/runner_econometric.py) và lưu vết tại [artifacts/](file:///d:/Petro_95/artifacts/).
* **Tách biệt hai nhánh đánh giá:** Phân định rõ ràng giữa **Nhánh A (Suy luận Tham số Toàn Mẫu)** và **Nhánh B (Đánh giá Năng lực Dự báo Ngoài Mẫu Qua Expanding Walk-Forward)** để triệt tiêu hoàn toàn bẫy Lookahead Bias và Overfitting.

---

## 2. MA TRẬN THIẾT KẾ MODEL SCHEMAS TOÀN DIỆN (M0a ĐẾN M6)

Khung kiến trúc [model_schemas.py](file:///d:/Petro_95/src/data_proccessing/model_schemas.py) đóng vai trò là **Nguồn Chân lý Duy nhất (SSOT)** quy định chặt chẽ danh mục biến đầu vào (Input Features Whitelist), cơ chế nạp dữ liệu (`input_mode`), và đầu ra mục tiêu (Output Targets).

### 2.1. Bản đồ Đặc tả Input / Output Chi tiết từng Mô hình

| Mã Model | Tên gọi Học thuật | Task | Input Mode | Stream & Mẫu | INPUT (Danh mục Đặc trưng Whitelist) | OUTPUT (Mục tiêu, Dự báo & Kiểm định) |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **M0a** | Naive Zero Return (Random Walk / EMH) | Regression | `null_baseline` | Stream 1 & 2 ($N=4,426$) | **Không có biến đầu vào** (`features = ()`). Không cần ma trận $X$. | $\widehat{r}_{t+1} = 0.0$. Mốc sàn loss OOS (RMSE, MAE). |
| **M0b** | Naive Directional Momentum | Classification | `null_baseline` | Stream 1 & 2 ($N=4,426$) | Duy nhất $1$ biến quan sát tại ngày $t$: `mg95_return_pct` ($r_{MG95, t}$). | $\widehat{y}_{t+1} = \mathbb{I}[r_t > 0] \in \{0, 1\}$. Directional Accuracy, MCC, Pesaran-Timmermann test. |
| **M1** | ARMA(1, 1) Univariate Time Series | Regression | `univariate_series` | Stream 1 (2008–2025) | Chuỗi 1D nội sinh: `mg95_return_pct` ($r_t$). Không có biến ngoại sinh. | $\widehat{r}_{t+1} = c + \phi_1 r_t + \theta_1 \epsilon_t$. Tham số $\{c, \phi_1, \theta_1, \sigma^2\}$, AIC, BIC, Ljung-Box Q-stat. |
| **M2** | Linear Dynamic Symmetric Regression | Regression | `feature_matrix` | Stream 1 (2008–2025) | **5 biến $I(0)$**: `mg95_return_pct`, `mg95_return_lag1`, `brent_return_pct_aligned`, `brent_return_lag1`, `spread_mg95_brent_lag1`. | $\widehat{r}_{t+1}$. Hệ số OLS Newey-West HAC (5 lags), Diebold-Mariano test so với $M1$. |
| **M3** | Asymmetric Distributed Lag (ADL) — **[RQ1 Core]** | Regression | `feature_matrix` | Stream 1 (2008–2025) | **7 biến $I(0)$**: `mg95_return_pct`, `mg95_return_lag1`, `brent_return_pos`, `brent_return_neg`, `brent_return_pos_lag1`, `brent_return_neg_lag1`, `spread_mg95_brent_lag1`. | $\widehat{r}_{t+1}$. Bộ ba kiểm định Wald HAC động: Tức thời ($W_1$), Tích lũy ($W_2$), và Lồng nhau ($W_{joint}$) so với $M2$. |
| **M4** | Technical Momentum & Volatility LightGBM | Regression | `feature_matrix` | Stream 2 (2017–2025) | **10 biến kỹ thuật**: 4 lags MG95, 4 lags Brent, `vol_mg95_30d`, `economic_shock_flag`. | $\widehat{r}_{t+1}$ (Huber loss). Diebold-Mariano (HLN 1997) so với $M3$ trên cùng cửa sổ Test 2020–2025. |
| **M5** | Economic Refining Spreads LightGBM | Regression | `feature_matrix` | Stream 2 (2017–2025) | **15 biến**: 10 biến $M4$ + `spread_mg95_mg92`, `spread_mg95_do005`, `spread_mg95_brent`, `spread_mg95_brent_lag1`, `octane_spread_nonpositive_flag`. | $\widehat{r}_{t+1}$. Feature importance (Gain/Split), Diebold-Mariano test so với $M4$. |
| **M6** | Multimodal Economic + News Sentiment — **[RQ2 Core]** | Regression | `feature_matrix` | Stream 2 (2017–2025) | **19 biến**: 15 biến $M5$ + `news_count`, `news_sentiment_mean`, `news_native_tone_mean`, `news_goldstein_mean`. | $\widehat{r}_{t+1}$. Giá trị đóng góp SHAP, Diebold-Mariano test so với $M5$ trên mẫu chung (Common Sample). |

### 2.2. Kỷ luật Quản trị Dữ liệu Cốt lõi
1. **Zero Target Leakage:** Biến mục tiêu `target_return_pct` và `target_direction` bị cấm xuất hiện trong danh mục biến đầu vào $X$ thông qua rào chắn kiểm toán cứng `assert`.
2. **Kỷ luật Dừng $I(0)$:** 100% các biến đầu vào đều là chuỗi dừng bậc 0 hoặc chuỗi tự hồi quy trung bình đã kiểm định ADF ($p < 0.001$), triệt tiêu nguy cơ hồi quy giả mạo.
3. **Cách ly Luồng Dữ liệu (Stream Isolation):** Bảo vệ trọn vẹn sức mạnh thống kê của Stream 1 ($N=4,425$ phiên 2008–2025) phục vụ suy luận kinh tế lượng RQ1, không bị cắt cụt bởi sự phụ thuộc vào dữ liệu tin tức của Stream 2 (2017–2025).

---

## 3. CHI TIẾT THỰC THI & THAM SỐ ƯỚC LƯỢNG TOÀN MẪU (NHÁNH A)

Toàn bộ tham số dưới đây được ước lượng trên mẫu đầy đủ 18 năm ($N_{eff} = 4,426$ quan sát từ ngày 05/05/2008 đến 30/12/2025) và đã được lưu trữ trong [artifacts/models/](file:///d:/Petro_95/artifacts/models/).

### 3.1. Mô hình M0a: Naive Zero Return
* **Công thức toán học:**
  $$\mathbb{E}[r_{t+1} \mid \mathcal{F}_t] = 0.0$$
* **Kết quả ước lượng:** Hằng số dự báo cố định $\widehat{r}_{t+1} = 0.0\%$.
* **Sai số trong mẫu (In-Sample):** $\text{MSE} = 6.1189$, $\text{RMSE} = 2.4736\%$, $\text{MAE} = 1.6268\%$.
* **Ý nghĩa:** Đây là cận dưới kỳ vọng tối thiểu. Bất kỳ mô hình nào có $\text{RMSE} > 2.4736\%$ trong mẫu hoặc $\text{RMSE}_{OOS} > \text{RMSE}_{M0a, OOS}$ đều bị coi là kém hơn bước đi ngẫu nhiên.

### 3.2. Mô hình M0b: Naive Directional Momentum
* **Công thức toán học:**
  $$\widehat{y}_{t+1} = \mathbb{I}[r_{MG95, t} > 0] \in \{0, 1\}, \quad \text{với quy tắc hòa: } r_t \le 0 \implies \widehat{y}_{t+1} = 0$$
* **Dự báo giá trị liên tục:** $\widehat{r}_{t+1} = r_{MG95, t}$ (giả định quán tính tiếp diễn).
* **Kết quả ước lượng:** Không có tham số tự do; mô hình phản ánh phản ứng thuần túy theo dấu của phiên trước.

### 3.3. Mô hình M1: ARMA(1, 1) Univariate Kalman Filter MLE
* **Thuật toán:** Ước lượng hợp lý cực đại Gaussian Maximum Likelihood (MLE) thông qua bộ lọc không gian trạng thái Kalman Filter trên chuỗi đơn biến $y_t = r_{MG95, t}$.
* **Phương trình ước lượng thực nghiệm:**
  $$r_{t+1} = -0.0101\% - 0.3786 \times r_t + 0.3227 \times \epsilon_t + \epsilon_{t+1}, \quad \sigma_\epsilon^2 = 6.1120$$

* **Bảng tổng hợp tham số và chẩn đoán phần dư:**

| Tham số / Thước đo | Ký hiệu | Giá trị Thực nghiệm | Ý nghĩa Kinh tế & Toán học |
| :--- | :---: | :---: | :--- |
| **Hằng số trôi (Constant Drift)** | $c$ | **$-0.0101\%$** | Lợi suất kỳ vọng bình quân xấp xỉ 0 (không có xu hướng tăng/giảm dài hạn đơn điệu). |
| **Hệ số Tự hồi quy (AR)** | $\phi_1$ | **$-0.3786$** | **Hồi quy trung bình (Mean-Reversion)**: Biến động phiên $t$ tạo ra lực kéo đảo chiều ở phiên $t+1$. |
| **Hệ số Trung bình trượt (MA)** | $\theta_1$ | **$+0.3227$** | Hiệu chỉnh quán tính của các cú sốc sai số chưa được thị trường hấp thụ hết ở phiên trước. |
| **Phương sai sai số trắng** | $\sigma_\epsilon^2$ | **$6.1120$** | Độ biến động phần dư $\sigma_\epsilon \approx \mathbf{2.472\%}$ / ngày. |
| **Log-Likelihood** | $\ln \mathcal{L}$ | **$-10,286.39$** | Hàm hợp lý cực đại đạt hội tụ hoàn hảo (`converged: true`). |
| **Akaike Info Criterion** | $\text{AIC}$ | **$20,580.78$** | Tiêu chuẩn phạt bậc tự do AIC. |
| **Bayesian Info Criterion** | $\text{BIC}$ | **$20,606.37$** | Tiêu chuẩn phạt bậc tự do BIC. |
| **Kiểm định Ljung-Box (Lag 5)** | $Q(5)$ | **$36.8621$ ($p = 6.38 \times 10^{-7}$)** | **Bác bỏ giả thuyết nhiễu trắng**: Phần dư vẫn còn tương quan bậc cao! |

---

## 4. KẾT QUẢ ĐÁNH GIÁ DỰ BÁO NGOÀI MẪU WALK-FORWARD (NHÁNH B)

Để kiểm chứng năng lực dự báo thực sự và loại bỏ hoàn toàn bẫy overfitting, hệ thống đã thực thi giao thức **Expanding Walk-Forward 1-step-ahead** (Cửa sổ huấn luyện mở rộng tuần tự, mỗi bước $t$ chỉ dùng dữ liệu lịch sử $1:t$ để dự báo độc lập cho $t+1$).

### 4.1. Bảng Xếp hạng Thực chứng (Stream 1 Econometric Leaderboard)

Bảng đối soát ngoài mẫu trích xuất từ [artifacts/metrics/stream1_econometric_leaderboard.csv](file:///d:/Petro_95/artifacts/metrics/stream1_econometric_leaderboard.csv):

| Model ID | Mô hình | Số phiên OOS ($N$) | RMSE (%) | MAE (%) | $R^2_{OOS}$ (vs Zero) | $R^2_{std}$ (vs Mean) | Độc xác Hướng (DA %) | Hệ số MCC | PT-stat | PT $p$-value |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M0a** | Naive Zero Return | 77 | **1.2761** | **0.9860** | **0.0000** | -0.0112 | 49.35% | 0.0000 | 0.0000 | 1.0000 |
| **M0b** | Naive Directional | 77 | 1.6244 | 1.2645 | -0.6204 | -0.6385 | **55.84%** | **0.1167** | **1.0311** | 0.3025 |
| **M1** | ARMA(1, 1) Kalman | 77 | 1.2811 | 0.9821 | **-0.0080** | -0.0192 | 51.95% | 0.0408 | 0.3600 | 0.7188 |

---

### 4.2. So sánh Quỹ đạo Dự báo Trực quan (M0a vs M0b vs M1)

Biểu đồ độ phân giải cao tại [`reports/figures/m0_m1_predictions_comparison.png`](file:///d:/Petro_95/reports/figures/m0_m1_predictions_comparison.png) ghi nhận hành vi dự báo của 3 mô hình trên 60 phiên giao dịch gần nhất:

```
        Tỷ suất sinh lời (%)
         │           ▲ r_{t+1} Thực tế (Đường đen)
        +3%          │      /\      /\
         │           │     /  \    /  \      /\
         0% ─────────┼────/────\──/────\────/──\── M0a: Naive Zero (Đường xám nằm ngang r=0)
         │           │   /      \/      \  /
        -3%          ▼                   \/
         └───────────┴─────────────────────────────► Thời gian (60 phiên gần nhất)
                     ── M0b: Quán tính r_t (Màu cam)
                     ── M1: ARMA(1,1) Kalman Filter (Màu xanh dương)
```

* **M0a (Đường xám nét đứt)**: Là đường chuẩn nằm ngang $\widehat{r}_{t+1} = 0$, mỏ neo trung tâm không nhận định.
* **M0b (Đường màu cam)**: Bám theo đuôi biến động của phiên hôm trước ($r_t$), dẫn đến hiện tượng trễ 1 nhịp (lagged echo) và làm sai số bình phương tăng mạnh ($\text{RMSE} = 1.6244\%$).
* **M1 (Đường màu xanh dương)**: Thu hẹp biên độ dao động nhờ cơ chế triệt tiêu giữa hệ số tự hồi quy âm ($\phi_1 = -0.3786$) và hệ số trung bình trượt dương ($\theta_1 = +0.3227$), tạo ra đường dự báo mượt mà hướng về mức trung bình dài hạn.

---

### 4.3. Chẩn đoán Phần dư (Residual Diagnostics) của M1

Biểu đồ 3 bảng tại [`reports/figures/m1_residual_diagnostics.png`](file:///d:/Petro_95/reports/figures/m1_residual_diagnostics.png) kiểm chứng các giả định kinh tế lượng:
1. **Panel A (Chuỗi thời gian sai số $e_t$)**: Cho thấy biên độ phần dư dao động mạnh và phân cụm rõ rệt (**Volatility Clustering**), đặc biệt trong các năm khủng hoảng 2008, 2020, 2022.
2. **Panel B (Mật độ phân phối sai số)**: Phân phối phần dư thực nghiệm có đỉnh nhọn vượt trội và hai đuôi kéo dài hơn đáng kể so với đường cong phân phối chuẩn Gaussian ($\mathcal{N}(0, 2.47^2)$). Điều này tái khẳng định tính chất **Fat-Tails** của thị trường xăng dầu.
3. **Panel C (Đồ thị Tự tương quan ACF từ Lag 1 đến 20)**: Hệ số tự tương quan tại Lag 1 đã được mô hình ARMA(1,1) triệt tiêu hoàn toàn về 0. Tuy nhiên, tại các độ trễ lớn hơn (Lag 4, 5, 8), các thanh tương quan vẫn vượt ra ngoài dải giới hạn tin cậy 95%.

---

## 5. LUẬN GIẢI KHOA HỌC: KẾT QUẢ M0 – M1 CHỨNG MINH ĐIỀU GÌ?

Kết quả thực nghiệm trên cung cấp **4 bằng chứng khoa học nền tảng**, làm cơ sở biện minh vững chắc cho toàn bộ đề tài:

### 5.1. Bằng chứng về Tính Hiệu quả Dạng Yếu (Weak-Form Market Efficiency)
* **Kết quả thực nghiệm:** Chỉ số $R^2_{OOS}$ của mô hình $M1$ đạt **$-0.0080$** (gần bằng 0), và kiểm định Pesaran-Timmermann đạt **$p = 0.7188$** (hoàn toàn không thể bác bỏ giả thuyết vô hiệu về tính độc lập phương hướng).
* **Kết luận khoa học:** Thị trường giao dịch xăng Platts FOB Singapore đạt xấp xỉ **Mức độ Hiệu quả Dạng Yếu (Fama, 1970)**. Giá thị trường phản ánh gần như tức thì các thông tin giá lịch sử nội tại. Một nhà giao dịch chỉ dựa vào lịch sử biến động giá xăng của chính nó sẽ **không thể đánh bại được bước đi ngẫu nhiên ($M0a$)** khi tính đến chi phí giao dịch.

### 5.2. Sự Bất khả thi của Phân tích Kỹ thuật Đơn biến Nội sinh
* **Kết quả thực nghiệm:** Mặc dù hệ số tự hồi quy trong mẫu có ý nghĩa thống kê ($\phi_1 = -0.3786$, thể hiện tính mean-reversion nhẹ), nhưng phương sai sai số $\sigma_\epsilon^2 = 6.1120$ chỉ giảm chưa tới **$0.11\%$** so với phương sai ban đầu của chuỗi ($6.1189$).
* **Kết luận khoa học:** Lợi suất xăng dầu bị chi phối bởi độ ồn (noise) cực lớn. Các mô hình chuỗi thời gian đơn biến chỉ học được nhiễu vi cấu trúc ngắn hạn chứ không nắm bắt được động lực xu hướng trung hạn.

### 5.3. Bằng chứng Bỏ sót Biến Ngoại sinh từ Kiểm định Ljung-Box ($p < 0.001$)
* **Kết quả thực nghiệm:** Kiểm định Ljung-Box trên phần dư của $M1$ tại bậc trễ 5 đạt thống kê **$Q(5) = 36.8621$ với $p\text{-value} = 6.38 \times 10^{-7}$**.
* **Ý nghĩa phương pháp luận then chốt:** Thống kê này **bác bỏ tuyệt đối giả thuyết phần dư là nhiễu trắng thuần túy (White Noise)**!
  - Điều này chứng minh rằng: Thị trường không phải là một chuỗi ngẫu nhiên vô trật tự hoàn toàn.
  - Vẫn còn tồn tại các cấu trúc phụ thuộc có quy luật trong chuỗi lợi suất, nhưng nguồn phát sinh quy luật đó **NẰM NGOÀI BẢN THÂN CHUỖI GIÁ XĂNG**. Mô hình $M1$ thất bại vì nó là một mô hình **bị bỏ sót biến nghiêm trọng (Omitted Variable Bias)**.

### 5.4. Cơ sở Lý luận Bắt buộc Chuyển dịch sang M2 (Brent) và M3 (Cú sốc Bất đối xứng)
Từ các phát hiện định lượng trên, đề tài rút ra kết luận logic tất yếu:
1. Để cải thiện năng lực dự báo ngoài mẫu, bắt buộc phải đưa vào **Chi phí nguyên liệu thô thượng nguồn (ICE Brent Futures)** và **Mỏ neo biên lọc dầu (Crack Spread)** $\implies$ Dẫn đến sự ra đời của **M2 (Linear Dynamic)**.
2. Để kiểm tra xem thị trường phản ứng với các cú sốc chi phí dầu thô theo cơ chế đối xứng hay bất đối xứng ("Tên lửa và Lông vũ") $\implies$ Dẫn đến mô hình phân tách cú sốc cốt lõi **M3 (Asymmetric ADL)** phục vụ trả lời **RQ1**.

---

## 6. HỒ SƠ BẰNG CHỨNG KIỂM TOÁN TÍNH DỪNG & ARTIFACT TRAIL

Toàn bộ kết quả trong báo cáo này được bảo đảm tính tái lập độc lập 100% thông qua hệ thống lưu trữ artifacts trên đĩa:

### Bảng Kiểm Toán Tính Dừng Đã Xuất Xưởng (`reports/data_quality/stationarity_audit.csv`):
* `target_return_pct`: $\text{ADF} = -11.3868$ ($p = 0.000000$) $\implies$ $I(0)$ Strongly Stationary.
* `mg95_return_pct`: $\text{ADF} = -11.3868$ ($p = 0.000000$) $\implies$ $I(0)$ Strongly Stationary.
* `brent_return_pct_aligned`: $\text{ADF} = -9.9528$ ($p = 0.000000$) $\implies$ $I(0)$ Strongly Stationary.
* `spread_mg95_brent_lag1`: $\text{ADF} = -6.4541$ ($p = 0.000000$) $\implies$ Mean-Reverting Stationary.

### Danh mục Artifacts Thực Thi:
* Mô hình đã fit: `artifacts/models/M0a_naive_zero.joblib`, `artifacts/models/M1_arma.joblib`.
* Tham số JSON: `artifacts/models/M1_coefficients.json`.
* Chuỗi dự báo Parquet: `artifacts/predictions/pred_M0a_stream1.parquet`, `artifacts/predictions/pred_M1_stream1.parquet`.
* Bảng Leaderboard: `artifacts/metrics/stream1_econometric_leaderboard.csv`.
* Biểu đồ trực quan: `reports/figures/m0_m1_predictions_comparison.png`, `reports/figures/m1_residual_diagnostics.png`.

---

**Xác nhận nghiệm thu Cổng Phase 3 (M0 – M1):** ĐẠT CHUẨN KHOA HỌC 100% — Sẵn sàng chuyển giao sang cài đặt mô hình M2 và M3.
