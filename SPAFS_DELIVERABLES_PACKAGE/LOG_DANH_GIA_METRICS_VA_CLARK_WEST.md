# BÁO CÁO TOÀN DIỆN: THIẾT KẾ OOS THỐNG NHẤT, KIỂM TOÁN TIMESTAMP PIT VÀ KIỂM ĐỊNH TÁI LẬP CLARK–WEST / DIEBOLD–MARIANO
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)
### BẢN GHI NHẬN KẾT LUẬN THỰC NGHIỆM CHÍNH THỨC CỦA DỰ ÁN

---

## 1. CHỐT THIẾT KẾ ĐÁNH GIÁ NGOÀI MẪU (OOS DESIGN SPECIFICATION)

Để bảo đảm tính minh bạch tuyệt đối, hệ thống xác định rõ ràng và tách biệt thiết kế OOS cho từng nhánh:

### A. Nhánh Kinh tế lượng (Stream 1 Econometric: 2008–2025)
* **Tổng mẫu khả dụng:** $N_{eff} = 4,425$ phiên giao dịch hiệu dụng sau khi lấy trễ (từ ngày 06/05/2008 đến 29/12/2025).
* **Cửa sổ Warm-up trong mẫu:** Khởi tạo $\tau_0 = 3,500$ phiên giao dịch đầu tiên (06/05/2008 đến **21/04/2022**).
* **Cửa sổ kiểm định ngoài mẫu riêng của Stream 1:**
  - **Thời gian OOS:** Từ ngày **22/04/2022 đến ngày 29/12/2025**.
  - **Quy mô mẫu OOS:** Đúng **$N_{OOS}^{(1)} = 925$ phiên giao dịch thực tế**.
* **Các mô hình đánh giá trên tập này:** M0a (Zero Return), M0b (Directional), M1 (ARMA(1,1)), M2 (Linear Dynamic ADL), M3 (Asymmetric ADL).
* **Mục đích sử dụng:** Trả lời câu hỏi nghiên cứu **RQ1** về tính đối xứng trong truyền dẫn giá (Bộ 3 kiểm định Wald trên toàn mẫu $N=4,425$ và kiểm định ngoài mẫu trên $N=925$).

### B. Nhánh Học máy (Stream 2 Machine Learning: 2017–2025)
* **Tổng mẫu khả dụng:** $N_{eff} = 2,254$ phiên giao dịch hiệu dụng có target $t+1$ (từ ngày 03/01/2017 đến 29/12/2025).
* **Cửa sổ Warm-up trong mẫu:** Khởi tạo $\tau_0 = 1,500$ phiên giao dịch (03/01/2017 đến **27/12/2022**).
* **Phương pháp chia mẫu:** **Expanding Window Walk-Forward 1-step-ahead** (chu kỳ tái ước lượng định kỳ $\text{Refit} = 20$ phiên ~ 1 tháng, triệt tiêu phương sai bằng GBDT 10-Seed Ensemble).
* **Cửa sổ kiểm định ngoài mẫu riêng của Stream 2:**
  - **Thời gian OOS:** Từ ngày **28/12/2022 đến ngày 29/12/2025** (trọn vẹn 3 năm tài chính 2023, 2024, 2025).
  - **Quy mô mẫu OOS:** Đúng **$N_{OOS}^{(2)} = 754$ phiên giao dịch thực tế**.
* **Các mô hình đánh giá trên tập này:** **M4 (Technical LightGBM, 10 biến)** và **M5 (Economic Refining LightGBM, 15 biến)**.
* **Mục đích sử dụng:** Trả lời câu hỏi nghiên cứu **RQ2** về giá trị gia tăng dự báo của các đặc trưng kinh tế học lọc dầu hạ nguồn (Crack Spread, Octane Premium, Diesel Margin).

### C. Phân định tập mẫu cho từng phép so sánh và Kiểm toán Tính nhất quán

| Model ID | Phân luồng | Số dòng OOS riêng | Ngày bắt đầu | Ngày kết thúc | Số phiên giao thoa | Số target thiếu | Sai lệch target thực tế | Quy tắc căn chỉnh PIT |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **M0a** | Stream 1 | 925 | 2022-04-22 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M0b** | Stream 1 | 925 | 2022-04-22 | 2025-12-29 | 754 / 754 | 0 | (Binary Sign) | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M1**  | Stream 1 | 925 | 2022-04-22 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M2**  | Stream 1 | 925 | 2022-04-22 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M3**  | Stream 1 | 925 | 2022-04-22 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M4**  | Stream 2 | 754 | 2022-12-28 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |
| **M5**  | Stream 2 | 754 | 2022-12-28 | 2025-12-29 | 754 / 754 | 0 | 0.00000000 | Cutoff 08:30 SGT, 1-step (16:30 SGT t+1) |

> [!NOTE]
> **LÀM RÕ VỀ PHIÊN GIAO DỊCH 21/04/2022 TẠI STREAM 1:**  
> Chuỗi Stream 1 ($N=4,425$ phiên) thiết lập cửa sổ Warm-up $\tau_0 = 3,500$ phiên. Phiên quan sát thứ $3,500$ diễn ra đúng vào **ngày 21/04/2022**, đây là **phiên cuối cùng của tập Train khởi đầu (Warm-up Cutoff)**. Quá trình kiểm định ngoài mẫu OOS bắt đầu từ **phiên quan sát thứ 3,501, tức ngày 22/04/2022** ($N_{OOS}^{(1)} = 925$ phiên). Ngày 21/04/2022 nằm trọn vẹn trong tập huấn luyện ban đầu, không hề bị thiếu hay bị loại trừ.

---

## 2. NÂNG CẤP KIỂM TOÁN TIMESTAMP POINT-IN-TIME (PIT AUDIT) CẤP BẢN GHI

Quy trình kiểm toán độc lập được thực thi trên toàn bộ **2,255 bản ghi** thông qua kịch bản `audit_record_level_pit.py`:

```
========================================================================================
             KẾT QUẢ KIỂM TOÁN TIMESTAMP POINT-IN-TIME (PIT) NÂNG CẤP
========================================================================================
Tổng số bản ghi kiểm toán                 : 2,255 phiên (Chuỗi dữ liệu 2017–2025)
Thời gian chuỗi dữ liệu                   : 2017-01-03 đến 2025-12-30

1. XÁC MINH DỮ LIỆU NGUỒN (SOURCE CALENDAR & TARGET ALIGNMENT):
  - Ngày giao dịch nguồn (market_date)     : 2,255 / 2,255 (100.0% xác thực từ sàn)
  - Ngày quan sát dầu Brent nguồn          : 2,255 / 2,255 (100.0% xác thực từ sàn)
  - Ngày giao dịch khớp lịch Platts-Brent  : 2,198 / 2,255 (97.47% trùng lịch tuyệt đối)
  - Ngày mục tiêu strictly t+1             : 2,255 / 2,255 (100.0% phiên kế tiếp)

2. BÓC TÁCH MINH BẠCH: PROXY TIMESTAMPS VS REAL-TIME TICKS:
  - Số timestamp publication là PROXY      : 2,255 / 2,255 (100.0%)
  - Số timestamp Platts availability PROXY : 2,255 / 2,255 (100.0%)
  - Số timestamp Brent availability PROXY  : 2,255 / 2,255 (100.0%)
  - Timestamp tick thời gian thực từ feed  : 0 (Dữ liệu EOD lịch sử không lưu log tick)
  * Ghi chú khoa học: Toàn bộ mốc giờ 16:30 SGT, 03:30 SGT và 08:30 SGT là Proxy quy chuẩn
    theo quy ước phiên giao dịch thị trường (Rule-Based Market Proxy Timestamps).
    Nghiên cứu KHÔNG tuyên bố đã xác minh log tick thời gian thực từ máy chủ feed.

3. KIỂM ĐỊNH TÍNH BẤT BIẾN THỜI GIAN (TEMPORAL INVARIANTS):
  - Platts Obs (16:30) < Cutoff (08:30)    : 2,255 / 2,255 đạt 100.0% (Vi phạm: 0)
  - Platts Avail (03:30) <= Cutoff (08:30) : 2,255 / 2,255 đạt 100.0% (Vi phạm: 0)
  - Brent Avail (03:30) <= Cutoff (08:30)  : 2,255 / 2,255 đạt 100.0% (Vi phạm: 0)
  - Cutoff (08:30) < Target Close (16:30)  : 2,255 / 2,255 đạt 100.0% (Vi phạm: 0)
  - Khoảng đệm an toàn sau chốt Brent      : Trung vị 5.0 giờ (Tối thiểu 5.0 giờ)
  - Thời gian dẫn trước đến phiên mục tiêu : Đúng 8.0 giờ trước thời điểm chốt giá Platts
========================================================================================
TỔNG SỐ LỖI VI PHẠM QUY TẮC THỜI GIAN (LOOKAHEAD BIAS): 0 BẢN GHI (100% TUÂN THỦ QUY TẮC)
========================================================================================
```

---

## 3. BẢNG HIỆU NĂNG NGOÀI MẪU THEO CÁC TẬP MẪU CHUẨN HÓA

### Bảng 3.1: Hiệu năng Nhánh Kinh tế lượng trên Mẫu OOS Stream 1 ($N_{OOS} = 925$ phiên, 2022–2025)

| Model ID | Mô hình | Số biến ($K$) | RMSE (%/ngày) | MAE (%/ngày) | DA (%) | PT-Stat | $p$-Value (PT) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **M0a** | Naive Zero Return | 0 | 2.1248 | 1.5452 | 48.22% | 0.0000 | 0.5000 |
| **M0b** | Historical Expanding Mean | 1 | 3.0135 | 2.1332 | 49.30% | -0.4578 | 0.6764 |
| **M1** | ARMA(1,1) Đơn biến | 2 | 2.1249 | 1.5447 | 48.32% | 0.0000 | 0.5000 |
| **M2** | Linear Dynamic ADL Tuyến tính | 8 | **1.7092** | **1.2583** | **70.05%** | **12.1818** | $< 10^{-33}$ |
| **M3** | Asymmetric ADL Bất đối xứng | 10 | 1.7104 | 1.2592 | 70.16% | 12.2530 | $< 10^{-33}$ |

### Bảng 3.2: Hiệu năng Nhánh Học máy trên Mẫu OOS Stream 2 ($N_{OOS} = 754$ phiên, 2022–2025)

| Model ID | Mô hình | Số biến ($K$) | RMSE (%/ngày) | MAE (%/ngày) | DA (%) | MCC | PT-Stat | $p$-Value (PT) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M4** | Technical LightGBM Ensemble | 10 | 1.4221 | 1.0712 | **70.82%** | **0.4156** | **11.4202** | $< 10^{-28}$ |
| **M5** | Economic Refining LightGBM | 15 | **1.4163** | **1.0643** | 70.42% | 0.4078 | 11.2063 | $< 10^{-28}$ |

### Bảng 3.3: Đối chuẩn Liên luồng trên Tập Giao thoa Chung Thống nhất ($N_{OOS} = 754$ phiên, 2022–2025)

| Model ID | Phân nhóm | Số biến ($K$) | RMSE (%/ngày) | MAE (%/ngày) | $R^2_{OOS}$ (%) | DA (%) | MCC | PT-Stat | $p$-Value (PT) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M0a** | Zero Return | 0 | 1.8004 | 1.3390 | 0.00% | 48.41% | 0.0000 | -0.0000 | 0.5000 |
| **M0b** | Expanding Mean | 1 | 2.5393 | 1.9087 | -98.94% | 51.19% | 0.0229 | +0.6288 | 0.2648 |
| **M1** | ARMA(1,1) | 2 | 1.8004 | 1.3395 | -0.01% | 48.41% | 0.0000 | -0.0000 | 0.5000 |
| **M2** | Linear ADL | 8 | **1.3880** | **1.0517** | **+40.56%** | 70.29% | 0.4080 | +11.2115 | $< 10^{-28}$ |
| **M3** | Asymmetric ADL | 10 | 1.3888 | 1.0517 | +40.50% | 70.29% | 0.4083 | +11.2191 | $< 10^{-28}$ |
| **M4** | Technical LGBM | 10 | 1.4221 | 1.0712 | +37.61% | **70.82%** | **0.4156** | **+11.4202** | $< 10^{-28}$ |
| **M5** | Economic LGBM | 15 | 1.4163 | 1.0643 | +38.12% | 70.42% | 0.4078 | +11.2063 | $< 10^{-28}$ |

---

## 4. KẾT QUẢ KIỂM ĐỊNH TÁI LẬP: PHÂN BIỆT RẠCH RÒI CLARK–WEST VÀ DIEBOLD–MARIANO

### A. Bảng quy chuẩn Giả thuyết, Đuôi kiểm định và Kết luận Thống kê

| Phép kiểm định | Cặp mô hình | Giả thuyết không ($H_0$) | Giả thuyết đối ($H_1$) | Quy ước đuôi | Mức ý nghĩa $\alpha$ | Thống kê tính toán | Giá trị $p$-value | Quyết định thống kê |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Clark & West (2007)** | M5 vs M4 | $\text{MSPE}_{M4} \le \text{MSPE}_{M5} - \text{adj}$ | $\bar{f} > 0$ (M5 có MSPE hiệu chỉnh nhỏ hơn) | **Một phía (One-sided)** | 5% | $\mathbf{CW = +1.9688}$ | $\mathbf{p = 0.0245}$ | **BÁC BỎ $H_0$ Ở MỨC 5%** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (MSE bằng nhau) | $E[d_t] < 0$ (M5 có MSE nhỏ hơn M4) | **Một phía (One-sided)** | 5% | $DM = -0.7748$ | $p = 0.2194$ | **Không thể bác bỏ $H_0$** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (MSE bằng nhau) | $E[d_t] \ne 0$ (MSE hai mô hình khác nhau) | **Hai phía (Two-sided)** | 5% | $DM = -0.7748$ | $p = 0.4387$ | **Không thể bác bỏ $H_0$** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (MAE bằng nhau) | $E[d_t] < 0$ (M5 có MAE nhỏ hơn M4) | **Một phía (One-sided)** | 10% | $DM = -1.3088$ | $p = 0.0955$ | **BÁC BỎ $H_0$ Ở MỨC 10%** |
| **Clark & West (2007)** | M3 vs M2 | $\text{MSPE}_{M2} \le \text{MSPE}_{M3} - \text{adj}$ | $\bar{f} > 0$ (M3 có MSPE hiệu chỉnh nhỏ hơn) | **Một phía (One-sided)** | 5% | $CW = -0.3436$ | $p = 0.6344$ | **Không thể bác bỏ $H_0$** |
| **Pesaran-Timmermann**  | M5 | Hướng đi thực tế và dự báo độc lập | Tỷ lệ đoán đúng vượt trội xác suất ngẫu nhiên | **Một phía (One-sided)** | 1% | $PT = +11.2063$ | $p < 10^{-28}$ | **BÁC BỎ $H_0$ Ở MỨC 1%** |

### B. Giải thích vì sao Clark–West đạt ý nghĩa 5% nhưng DM Squared Loss không đạt ý nghĩa 5%:
1. **Bản chất mô hình lồng nhau (Nested Models):** M4 ($K=10$) lồng ghép hoàn toàn trong M5 ($K=15$).
2. **Nhiễu ước lượng tham số (Parameter Estimation Noise):** Dưới $H_0$ (5 biến mới vô nghĩa), M5 vẫn phải ước lượng thêm các tham số tương ứng trong quá trình Walk-forward. Việc ước lượng này tạo ra nhiễu làm tăng phương sai ngoài mẫu của M5 lên một lượng $+0.02624$.
3. **Sự thiên lệch của Diebold-Mariano:** Kiểm định DM tiêu chuẩn bỏ qua số hạng bù nhiễu này, dẫn đến thống kê DM bị **chệch âm nghiêm trọng (severely undersized)** và ưu ái quá mức cho mô hình nhỏ M4.
4. **Hiệu chỉnh Clark & West (2007):** Bằng cách bổ sung số hạng bù nhiễu $(\hat{y}_{M4} - \hat{y}_{M5})^2$, Clark–West phục hồi phân phối tiệm cận chuẩn, đem lại năng lực kiểm định chính xác và khẳng định M5 thực sự cải thiện năng lực dự báo ngoài mẫu có ý nghĩa thống kê ($CW = +1.9688, p = 0.0245 < 0.05$).

---

## 5. GIỚI HẠN CỦA TỶ LỆ ĐOÁN ĐÚNG CHIỀU HƯỚNG (~70%) VÀ CÁC HẠN CHẾ CỐT LÕI

### A. Directional Accuracy (~70%) KHÔNG PHẢI là bằng chứng trực tiếp chứng minh cơ chế kinh tế:
- Về mặt bản chất thống kê, tỷ lệ $\text{DA} \approx 70.4\% - 70.8\%$ là hệ quả của **cơ chế căn chỉnh thông tin qua múi giờ (Cross-Timezone Information Alignment)**: sàn ICE Brent London đóng cửa lúc 03:30 SGT trước mốc chốt Cutoff 08:30 SGT, cung cấp tín hiệu chi phí gốc rất mạnh cho phiên giao dịch chiều 16:30 SGT của Platts Singapore.
- Con số này chứng minh sự lan tỏa thông tin có hiệu lực cao qua múi giờ (Timezone Information Spillover), **không phải bằng chứng đứng độc lập chứng minh cho bất kỳ cơ chế vi mô nội sinh nào**. Bằng chứng kinh tế thực chất nằm ở việc các biến biên lọc dầu trong M5 đánh bại M4 qua kiểm định Clark–West ($p = 0.0245$).

### B. Ba hạn chế cốt lõi của nghiên cứu:
1. **Hạn chế về Timestamp Quy ước (Proxy Timestamps):** Dữ liệu lịch sử cuối ngày EOD 2008–2025 không lưu trữ log tick máy chủ thời gian thực. Toàn bộ mốc giờ 16:30, 03:30 và 08:30 SGT được mô phỏng theo quy ước phiên giao dịch của sàn. Nghiên cứu không tuyên bố đã xác minh log tick thời gian thực.
2. **Hạn chế về Phạm vi Thị trường:** Nghiên cứu tập trung chuyên biệt vào thị trường bán buôn hàng rời quốc tế tại cảng Singapore (Platts FOB Singapore Mogas 95) và giá chuẩn dầu thô ICE Brent. Kết luận phản ánh đặc trưng của thị trường đầu mối có tính cạnh tranh cao.
3. **Giới hạn Khái quát hóa sang Thị trường Bán lẻ:** Không thể tự động áp dụng kết luận đối xứng hoàn hảo này cho thị trường bán lẻ nội địa (như tại Việt Nam, Hoa Kỳ hay EU) do sự can thiệp của Quỹ Bình ổn giá, chu kỳ điều hành giá nhà nước và thuế phí nội địa.
