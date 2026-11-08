# Hướng 4: Dự báo **khoảng dao động và rủi ro** giá xăng Singapore cho 1 ngày, 1 tuần và 1 tháng

*Kế hoạch mở rộng dự án SPAFS V5.2, giữ nguyên dữ liệu hiện có. Ngày soạn: 07/11/2026.*

---

## 1. Vì sao chuyển sang hướng này?

### 1.1 Điểm xuất phát

Kết quả hiện tại của dự án (sau khi sửa lỗi):

| Kỳ hạn | Dự báo **mức tăng/giảm** tốt nhất | Giảm sai số so với đoán "đứng yên" |
|---|---|---|
| 1 ngày | M2 (hồi quy theo Brent) | **+39,8%**, đúng hướng khoảng 70% |
| 1 tuần | M4 (LightGBM) | +4,6% |
| 1 tháng | Không có | Mọi mô hình đều âm |

Ở kỳ hạn tuần và tháng, **hướng đi của giá gần như ngẫu nhiên** với dữ liệu hiện có. Muốn dự báo tốt hơn **hướng** thì phải mua thêm dữ liệu kỳ hạn (hướng 1).

### 1.2 Ý tưởng của hướng 4

Không dự báo được giá **đi về đâu**, nhưng có thể dự báo giá **dao động mạnh đến mức nào**.

Trong tài chính, mức biến động có tính **"dồn cục"**: giai đoạn hỗn loạn thường kéo dài, giai đoạn yên ả cũng vậy. Vì thế, dù không biết tháng tới giá tăng hay giảm, ta vẫn có thể nói:

> *"Tháng tới, giá xăng Singapore có 80% khả năng thay đổi trong khoảng **−10% đến +9%**. Mức rủi ro hiện tại: **THẤP / TRUNG BÌNH / CAO** (so với các lần dự báo trước trong lịch sử)."*

**Ai dùng được dự báo dạng này?**

| Người dùng | Dùng để làm gì |
|---|---|
| Doanh nghiệp nhập khẩu xăng dầu | Lập ngân sách mua hàng, quyết định có phòng ngừa rủi ro giá hay không |
| Cơ quan điều hành giá | Ước tính mức trích hoặc chi Quỹ bình ổn giá cần chuẩn bị |
| Doanh nghiệp vận tải, logistics | Dự phòng chi phí nhiên liệu theo kịch bản xấu |

### 1.3 Câu hỏi nghiên cứu mới (RQ4)

- **RQ4a:** có thể đưa ra **khoảng dự báo hiệu chỉnh đúng** không? Nghĩa là nói 80% thì thực tế giá rơi vào khoảng 80% số lần.
- **RQ4b:** khoảng dự báo theo mô hình có **hẹp hơn**, tức hữu ích hơn, so với khoảng cố định ngây thơ không?
- **RQ4c:** có phân biệt được giai đoạn **rủi ro cao và thấp** trước khi chúng xảy ra không?
- **RQ4d:** thông tin về dầu Brent và biên lọc dầu có giúp dự báo **rủi ro** tốt hơn so với chỉ nhìn biến động quá khứ không?

---

## 2. Kiểm tra sơ bộ: hướng này có triển vọng không?

Đã chạy thử nhanh với cách đơn giản nhất: dùng **độ lệch chuẩn 63 ngày gần nhất**, quy theo kỳ hạn bằng √h, để dựng khoảng 80%. Phương pháp này không ước lượng tham số nào, nên mỗi dự báo chỉ dùng thông tin quá khứ.

### 2.1 Toàn bộ chuỗi 2008–2025 (Luồng 1, khoảng 4.350 ngày)

| Kỳ hạn | Tương quan "biến động quá khứ" với "độ lớn biến động tương lai" | Tỷ lệ giá thực rơi vào khoảng 80% | Độ lệch chuẩn thực tế: nhóm rủi ro **thấp** (Q1) và **cao** (Q4) |
|---|---|---|---|
| 1 ngày | 0,42 | 81,6% | 1,34% và **3,85%** (gấp 2,9 lần) |
| 1 tuần | 0,39 | 79,5% | 3,25% và **8,27%** (gấp 2,5 lần) |
| 1 tháng | 0,30 | 77,6% | 7,62% và **17,89%** (gấp 2,3 lần) |

**Nhận xét:** trên chuỗi dài có nhiều khủng hoảng (2008, 2014–2015, 2020, 2022), khi mô hình nói "rủi ro cao" thì giá thực sự dao động **mạnh gấp 2,3–2,9 lần** so với lúc nó nói "rủi ro thấp". Khoảng 80% cũng gần đúng 80%.

### 2.2 Chỉ giai đoạn kiểm tra 2023–2025 (Luồng 2)

| Kỳ hạn | Tương quan | Khoảng 80% theo biến động **gần đây** | Khoảng 80% theo biến động **cố định** (giai đoạn huấn luyện) |
|---|---|---|---|
| 1 tuần | 0,11 | **81,3%** ✅ | 96,4% (quá rộng) |
| 1 tháng | −0,04 | **84,3%** ✅ | 100% (quá rộng, vô dụng) |

**Nhận xét trung thực:**

- **Điểm mạnh:** khoảng dựa trên biến động gần đây vẫn **hiệu chỉnh tốt**. Khoảng cố định thì quá rộng, vì giai đoạn huấn luyện 2017–2022 có COVID và khủng hoảng 2022.
- **Điểm yếu:** giai đoạn 2023–2025 **khá yên ả, ít chênh lệch rủi ro**, nên khả năng *phân biệt tháng rủi ro* gần như bằng 0. Vì vậy cần đánh giá **cả trên chuỗi 2008–2025** (mục 6.3), không chỉ trên 2023–2025.

---

## 3. Bài toán và sản phẩm dự báo

### 3.1 Đại lượng cần dự báo

Giữ nguyên các mục tiêu đã có trong dữ liệu (không cần thêm dữ liệu):

| Kỳ hạn | Cột mục tiêu | Định nghĩa |
|---|---|---|
| 1 ngày | `target_return_daily` | ln(P_{t+1} / P_t) × 100 |
| 1 tuần | `target_return_weekly` | ln(P_{t+5} / P_t) × 100 |
| 1 tháng | `target_return_monthly` | ln(P_{t+21} / P_t) × 100 |

*Tuỳ chọn:* thêm mục tiêu **giá trung bình** của tuần hoặc tháng tới, sát với cách tính giá cơ sở ở Việt Nam. Mục tiêu này tính được ngay từ giá MG95 sẵn có.

### 3.2 Ba sản phẩm cho mỗi ngày và mỗi kỳ hạn

| Sản phẩm | Ví dụ đầu ra | Cách tạo |
|---|---|---|
| **Khoảng dự báo 80% và 95%** | [−7,1%; +6,8%] và [−11,0%; +10,5%] | Các phân vị 2,5%, 10%, 90%, 97,5% |
| **Xác suất tăng** | P(tăng) = 54% | Phân phối dự báo, hoặc mô hình phân loại riêng |
| **Mức rủi ro** | Độ biến động dự kiến 6,2%, nhãn **CAO** | So độ biến động dự kiến với các ngưỡng phân vị lịch sử (chỉ dùng dữ liệu quá khứ) |

Ở kỳ hạn **1 ngày**, có thể ghép **dự báo điểm của M2** (đúng hướng khoảng 70%) với **khoảng của mô hình rủi ro**, để vừa có hướng vừa có biên độ.

---

## 4. Các mô hình

Xây theo **thang từ đơn giản đến phức tạp**, như các mô hình M0–M5 hiện có:

| Mã | Mô hình | Cách hoạt động (ngôn ngữ đời thường) | Biến đầu vào |
|---|---|---|---|
| **Q0** | Biến động **cố định** | Dùng độ lệch chuẩn của toàn bộ giai đoạn huấn luyện, không đổi theo thời gian | Không có |
| **Q1** | Biến động **gần đây** | Độ lệch chuẩn 63 ngày gần nhất, hoặc trung bình có trọng số giảm dần (EWMA, λ = 0,94 kiểu RiskMetrics), quy theo kỳ hạn bằng √h | Lợi suất MG95 quá khứ |
| **Q2** | **GARCH(1,1)**, phân phối Student-t | Mô hình kinh tế lượng chuẩn cho biến động "dồn cục"; dự báo biến động nhiều bước rồi cộng dồn cho kỳ hạn h | Lợi suất MG95 quá khứ |
| **Q3** | **Hồi quy phân vị** (quantile regression) | Ước lượng trực tiếp phân vị 10% và 90% của lợi suất tương lai theo các biến | Biến động gần đây, độ lớn biến động Brent, chênh lệch xăng–Brent, cờ cú sốc |
| **Q4** | **LightGBM phân vị + hiệu chỉnh conformal** | Học máy dự báo phân vị; bước conformal điều chỉnh độ rộng để tỷ lệ bao phủ đúng như cam kết | Toàn bộ 15 biến của M5 |
| **Q2-X** | **GARCH-X** (tuỳ chọn) | GARCH có thêm biến ngoại sinh: biến động Brent đêm qua | Như Q2, cộng Brent |

**Xác suất tăng:**
- Kỳ hạn 1 ngày: dùng dự báo của M2 kèm phân phối sai số.
- Kỳ hạn tuần/tháng: so với mốc "luôn nói 50%" và mốc "tỷ lệ tăng lịch sử".

**Ghi chú về Q2 (GARCH):** chỉ ước lượng lại mỗi 20 phiên, giống LightGBM, để giảm thời gian chạy. Giữa hai lần ước lượng, biến động vẫn được cập nhật hằng ngày theo dữ liệu mới.

---

## 5. Đánh giá bằng metric nào?

| Metric | Câu hỏi | Tốt khi | Trả lời cho |
|---|---|---|---|
| **Coverage** (tỷ lệ bao phủ) | Nói 80% thì thực tế rơi vào khoảng bao nhiêu %? | Gần 80% (và gần 95% với khoảng 95%) | RQ4a |
| **Độ rộng khoảng trung bình** | Khoảng có đủ hẹp để hữu ích không? | Hẹp nhất có thể khi coverage vẫn đúng | RQ4b |
| **Pinball loss** (quantile loss) | Gộp cả độ chính xác lẫn độ hẹp của các phân vị | Nhỏ hơn mô hình so sánh | RQ4b, RQ4d |
| **Kiểm định Kupiec** | Tỷ lệ "trượt ra ngoài khoảng" có đúng 20% (hoặc 5%) không? | p > 0,05 | RQ4a |
| **Kiểm định Christoffersen** | Các lần trượt có bị **dồn cục** không, tức mô hình có phản ứng chậm khi thị trường đổi trạng thái? | p > 0,05 | RQ4a |
| **Tương quan / R² Mincer–Zarnowitz** giữa biến động dự báo và độ lớn biến động thực tế | Mô hình có phân biệt được giai đoạn rủi ro không? | Hệ số dương, có ý nghĩa | RQ4c |
| **QLIKE loss** | Dự báo phương sai tốt đến đâu (chuẩn trong tài liệu nghiên cứu về biến động) | Nhỏ hơn mô hình so sánh | RQ4c, RQ4d |
| **Brier score / log-loss** | Xác suất tăng có hiệu chỉnh tốt không? | Nhỏ hơn mốc "luôn nói 50%" | Xác suất tăng |
| **Biểu đồ hiệu chỉnh** | Nói 60% thì thực tế tăng khoảng 60% số lần không? | Nằm gần đường chéo | Xác suất tăng |
| **Diebold–Mariano trên pinball loss / QLIKE** | Mô hình A tốt hơn B có ý nghĩa thống kê không? | p < 0,05 | So sánh mô hình |

**Lưu ý với kỳ hạn tuần/tháng:** các ngày dự báo chồng lấp nhau. Hai lần trượt liên tiếp có thể chỉ là **cùng một cú sốc**. Vì vậy:

- Kiểm định Kupiec và Christoffersen nên chạy trên **mẫu không chồng lấp** (lấy mỗi 5 hoặc 21 phiên một điểm).
- DM dùng HAC với h − 1 lag, như module `forecast_tests.py` hiện có.

---

## 6. Cách xây dựng và kiểm tra

### 6.1 Dùng lại nền móng hiện có

| Thành phần | Trạng thái | Việc cần làm |
|---|---|---|
| Dữ liệu `stream1_econometric_2008_2025.parquet`, `stream2_multi_horizon_2017_2025.parquet` | Có sẵn | Không cần thêm. Với Luồng 1, tạo thêm mục tiêu 5 và 21 phiên bằng cách cộng dồn lợi suất ngày. |
| Engine walk-forward `src/models/validation/walk_forward.py` (purge = h, embargo) | Có sẵn | Mở rộng để `predict` trả về **nhiều phân vị** thay vì một số |
| Module đánh giá `src/models/evaluation/forecast_tests.py` | Có sẵn (DM, HAC) | Thêm module mới `interval_tests.py` |
| Mô hình M0a…M5 | Có sẵn | Giữ nguyên; M2 dùng cho xác suất tăng 1 ngày |

### 6.2 Module mới đề xuất

| File | Interface | Nội dung |
|---|---|---|
| `src/models/risk/volatility.py` | `fit(X, y)`, `predict_quantiles(X, levels)` | Q0, Q1, Q2 (dùng thư viện `arch` cho GARCH) |
| `src/models/risk/quantile.py` | Như trên | Q3 (statsmodels `QuantReg`), Q4 (LightGBM `objective="quantile"` + conformal) |
| `src/models/evaluation/interval_tests.py` | `interval_metrics(y, lower, upper, level)`, `pinball_loss(y, q, level)`, `kupiec_test(...)`, `christoffersen_test(...)`, `qlike(...)`, `brier(...)` | Một chỗ duy nhất cho mọi metric khoảng; có test đối chiếu công thức |
| `src/models/runner_risk_multi_horizon.py` | Chạy mọi Q0–Q4 cho 3 kỳ hạn | Xuất `artifacts/risk/` |

### 6.3 Hai bộ đánh giá

| Bộ | Dữ liệu | Giai đoạn kiểm tra | Mục đích |
|---|---|---|---|
| **Chính** | Luồng 2 (2017–2025) | 28/12/2022 → 2025 (khớp với kết quả hiện tại) | So sánh trực tiếp với M0a…M5 và RNN/LSTM |
| **Kiểm tra độ bền** | Luồng 1 (2008–2025) | Ví dụ 2012 → 2025, gồm các giai đoạn 2014–2015, 2020, 2022 | Kiểm tra khả năng phân biệt rủi ro khi **có** khủng hoảng (RQ4c) |

### 6.4 Quy tắc chống "nhìn trộm tương lai"

- Mọi biến dùng để dự báo rủi ro tại ngày t chỉ được dùng thông tin có trước **08:30 SGT ngày t+1**, giống mô hình hiện có.
- Các **ngưỡng rủi ro** (thấp / trung bình / cao) chỉ được tính từ **dữ liệu quá khứ** tại mỗi thời điểm, không dùng phân vị của toàn bộ mẫu.
- Bước hiệu chỉnh conformal của Q4 chỉ dùng **phần dư của các dự báo đã có đáp án** trước thời điểm dự báo (đã trừ purge h + embargo).

---

## 7. Kế hoạch thực hiện

| Bước | Việc | Ước lượng |
|---|---|---|
| 1 | Viết `interval_tests.py` kèm test (coverage, pinball, Kupiec, Christoffersen, QLIKE, Brier) | 0,5 ngày |
| 2 | Q0, Q1 và mở rộng engine walk-forward cho phân vị | 0,5 ngày |
| 3 | Q2 GARCH (cài thư viện `arch`), Q3 hồi quy phân vị | 0,5–1 ngày |
| 4 | Q4 LightGBM phân vị + conformal | 0,5 ngày |
| 5 | Chạy 3 kỳ hạn trên Luồng 2 và kiểm tra độ bền trên Luồng 1 | 0,5 ngày |
| 6 | Biểu đồ quạt (fan chart), biểu đồ hiệu chỉnh, báo cáo kết quả md | 0,5 ngày |

**Tổng:** khoảng **3 ngày làm việc**.

---

## 8. Kết quả kỳ vọng (thực tế)

| Câu hỏi | Kỳ vọng | Mức tin cậy |
|---|---|---|
| RQ4a: khoảng hiệu chỉnh đúng | **Có trên 2012–2025** (80,3–81,1% với Q1, Q2 ở cả 3 kỳ hạn); trên 2023–2025 thì **đúng ở tuần** (80,1%), nhưng **hơi rộng ở ngày** (83%) và **quá rộng ở tháng** (88–95%) vì giai đoạn này yên ả hơn giai đoạn học. | Cao |
| RQ4b: hẹp hơn khoảng cố định | **Có**, đặc biệt trên 2023–2025, vì khoảng cố định quá rộng (96–100%). | Cao |
| RQ4c: phân biệt giai đoạn rủi ro | **Có trên 2008–2025** (nhóm rủi ro cao biến động mạnh gấp 2,3–2,9 lần); **yếu trên 2023–2025** | Trung bình |
| RQ4d: Brent và biên lọc dầu giúp dự báo rủi ro | Có thể có ở **1 ngày** (biến động Brent đêm qua); không chắc ở tuần/tháng | Thấp đến trung bình |
| Xác suất tăng tuần/tháng | Gần mốc 50%, cải thiện rất nhỏ | Cao (tức là gần như không cải thiện) |

---

## 9. Rủi ro và cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| Giai đoạn kiểm tra 2023–2025 quá yên ả, khó chứng minh RQ4c | Báo cáo song song bộ kiểm tra độ bền 2008–2025 (mục 6.3) |
| Lợi suất có "đuôi dày" (cú sốc lớn hơn phân phối chuẩn), khoảng 95% bị trượt nhiều | Dùng phân phối Student-t trong GARCH; dùng phân vị thực nghiệm hoặc conformal thay vì giả định chuẩn |
| GARCH không hội tụ ở một số lần ước lượng lại | Dùng lại tham số lần trước và ghi vào log; có Q1 làm phương án dự phòng |
| Mẫu tháng chồng lấp làm kiểm định quá lạc quan | Chạy Kupiec và Christoffersen trên mẫu không chồng lấp; DM dùng HAC h − 1 |
| Hội đồng hỏi "không dự báo được hướng thì có ích gì?" | Nhấn mạnh người dùng thực tế (mục 1.2): ngân sách, quỹ bình ổn, phòng ngừa rủi ro. Kèm ví dụ biểu đồ quạt. |

---

## 10. Cách trình bày với giảng viên (một câu)

> *"Với dữ liệu hiện có, giá xăng ngày mai dự báo được hướng (đúng khoảng 70%). Ở kỳ hạn tuần và tháng, hướng giá gần như ngẫu nhiên, nhưng **mức độ rủi ro thì dự báo được**: mô hình đưa ra khoảng dao động đúng tỷ lệ cam kết, hẹp hơn cách làm ngây thơ, và trên giai đoạn 2008–2025 phân biệt được thời kỳ rủi ro cao, khi giá biến động mạnh gấp 2–3 lần thời kỳ rủi ro thấp."*

---

## Phụ lục: Checklist trước khi bắt đầu

- [ ] Cài thư viện `arch` cho GARCH (`pip install arch`).
- [ ] Tạo mục tiêu 5 và 21 phiên cho Luồng 1 (cộng dồn lợi suất ngày, bỏ các dòng cuối chưa có đáp án).
- [ ] Mở rộng engine walk-forward cho dự báo phân vị, giữ nguyên quy tắc purge/embargo và test chống rò rỉ.
- [ ] Viết `interval_tests.py` và test đối chiếu công thức trước khi chạy mô hình.
- [ ] Chốt các mức phân vị: 2,5%, 10%, 50%, 90%, 97,5%.
- [ ] Chốt ngưỡng nhãn rủi ro (ví dụ: dưới phân vị 25% là thấp, trên 75% là cao), tính theo **dữ liệu quá khứ**.
