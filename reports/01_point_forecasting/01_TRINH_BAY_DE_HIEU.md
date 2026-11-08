# Dự án SPAFS: Dự báo giá xăng Singapore ngày mai tăng hay giảm

*Tài liệu trình bày cho giảng viên, viết theo cách dễ hiểu. Mọi con số lấy từ lần chạy lại ngày 07/11/2026, sau khi đã sửa lỗi.*

---

## 1. Tóm tắt trong 30 giây

> Mỗi sáng, trước khi thị trường Singapore mở cửa, nhóm dự báo **giá xăng RON 95 tại Singapore (Mogas 95)** chiều nay sẽ **tăng hay giảm, và bao nhiêu %** so với hôm qua.
>
> **Kết quả:** mô hình đoán đúng hướng khoảng **70% số ngày**, trong khi đoán ngẫu nhiên chỉ được khoảng 50%. Mô hình giảm được **khoảng 40% sai số** so với cách đoán "giá đứng yên".
>
> **Lý do chính:** dầu thô Brent giao dịch ở London và New York **trong lúc Singapore đang ngủ**. Sáng ra, giá xăng Singapore phải "bắt kịp" biến động đó. Mô hình khai thác chính độ trễ múi giờ này.
>
> **Giới hạn:** sang dự báo **1 tuần** thì mức cải thiện chỉ còn rất nhỏ, và với **1 tháng** thì không mô hình nào tốt hơn đoán "đứng yên".

---

## 2. Bài toán là gì?

**Đối tượng dự báo:** giá **Platts FOB Singapore Mogas 95**. Đây là giá xăng bán buôn chuẩn của châu Á, do hãng S&P Global Platts công bố lúc **16:30 giờ Singapore** mỗi ngày giao dịch. Giá xăng bán lẻ ở Việt Nam và khu vực được tính dựa trên giá này, nên dự báo được nó có giá trị cho doanh nghiệp nhập khẩu, đầu mối xăng dầu và cơ quan điều hành giá.

**Đại lượng dự báo:** không dự báo giá tuyệt đối (ví dụ 85 USD/thùng) mà dự báo **tỷ lệ thay đổi (%)** của giá hôm nay so với hôm qua. Từ đó suy ra **hướng**: tăng hay giảm.

**Thời điểm dự báo:** **08:30 sáng** giờ Singapore, trước khi giá chiều được công bố. Mô hình chỉ được dùng thông tin đã có trước 08:30. Đây là quy tắc "không nhìn trộm tương lai", được kiểm tra tự động cho từng dòng dữ liệu.

---

## 3. Ý tưởng cốt lõi: "Singapore ngủ, London thức"

```
 Ngày t (Singapore)                         Ngày t+1 (Singapore)
 ─────────────────────────────────────────────────────────────────────────────►
   16:30            Đêm (London / New York giao dịch)     08:30          16:30
     │                                                      │              │
 Platts chốt giá          Dầu Brent biến động               Mô hình        Platts chốt
 xăng ngày t              (ví dụ +3%), chốt khoảng          DỰ BÁO         giá ngày t+1
                          02:30 sáng t+1                    ở đây          = ĐÁP ÁN
```

Khi Platts chốt giá xăng Singapore lúc 16:30 ngày t, thị trường dầu thô phương Tây mới bắt đầu phiên. Nếu qua đêm dầu Brent tăng mạnh, giá xăng Singapore chiều hôm sau gần như chắc chắn sẽ tăng theo, vì xăng được lọc từ dầu thô.

Mô hình đo được điều này. Trong mô hình hồi quy M2:

- **Brent tăng 1% qua đêm** thì xăng Singapore hôm sau tăng trung bình khoảng **0,67%**.
- **Xăng hôm nay đã tăng 1%** thì hôm sau có xu hướng **giảm lại khoảng 0,27%**. Đây là hiện tượng "điều chỉnh", vì giá hôm nay có thể đã phản ứng quá đà.

Ví dụ: đêm qua Brent tăng 3%, còn xăng Singapore hôm qua đứng yên. Mô hình dự báo xăng chiều nay tăng khoảng **+2%**, tức dự báo **TĂNG**.

Trong mô hình LightGBM, biến "biến động Brent qua đêm" cũng là biến quan trọng nhất, quan trọng gấp **6 lần** biến đứng thứ hai.

> **Nhận xét cá nhân:** đây là điểm quan trọng nhất cần nói rõ với hội đồng. Mức 70% đúng hướng **không có nghĩa** là mô hình "nhìn thấy tương lai". Mô hình **tận dụng thông tin đã xảy ra** (giá Brent đêm qua) mà giá Singapore chưa kịp phản ánh. Đây là một phát hiện thực tế, có giá trị và hợp lệ, vì thông tin đó thật sự có trước 08:30. Nhưng nên gọi đúng tên: **"dự báo sự truyền dẫn giá"**, không phải "dự đoán thị trường".

---

## 4. Dữ liệu

| Nguồn | Nội dung | Thời gian |
|---|---|---|
| Platts Singapore | Giá xăng 95, xăng 92, dầu diesel 0,05%S | 2008 – 2025 |
| ICE Brent (BZ=F) | Giá dầu thô Brent hằng ngày | 2008 – 2025 |

Nhóm chia dữ liệu thành **hai luồng**, mỗi luồng phục vụ một câu hỏi nghiên cứu:

- **Luồng 1 (2008–2025, 4.428 ngày):** dùng cho các mô hình kinh tế lượng, để có chuỗi dài, nhiều chu kỳ giá.
- **Luồng 2 (2017–2025, 2.255 ngày):** dùng cho học máy.
  - Huấn luyện: 2017 → 12/2022.
  - **Kiểm tra: 28/12/2022 → 29/12/2025 (754 ngày giao dịch)**. Mô hình hoàn toàn không thấy giai đoạn này khi học.

**Các biến đầu vào ("đầu mối" cho mô hình):**

| Nhóm | Ví dụ | Ý nghĩa đời thường |
|---|---|---|
| Đà giá xăng | % thay đổi hôm nay, 1–3 ngày trước | Giá đang lên hay xuống |
| Đà giá dầu thô | % thay đổi Brent qua đêm, 1–3 ngày trước | Nguyên liệu đầu vào biến động ra sao |
| Độ "nóng" thị trường | Độ biến động 30 ngày, cờ "có cú sốc" | Thị trường đang yên hay đang hỗn loạn |
| Kinh tế nhà máy lọc dầu | Chênh lệch xăng 95 – dầu Brent, xăng 95 – xăng 92, xăng – diesel | Nhà máy lọc dầu lời hay lỗ, xăng đang đắt hay rẻ so với các sản phẩm khác |

---

## 5. Các mô hình: từ "đoán bừa" đến AI

Nhóm xây dựng một **thang mô hình** từ đơn giản đến phức tạp. Mỗi bậc chỉ được coi là có giá trị nếu nó **thắng được bậc dưới**.

| Mã | Tên | Cách hoạt động (ngôn ngữ đời thường) | Vai trò |
|---|---|---|---|
| **M0a** | Đoán "đứng yên" | Luôn dự báo thay đổi 0%. | **Thước đo gốc.** Mọi mô hình phải thắng được nó. |
| **M0b** | Đoán "theo quán tính" | Hôm nay tăng bao nhiêu thì đoán ngày mai tăng bấy nhiêu. | Kiểm tra xem giá có "đà" hay không. |
| **M1** | ARMA | Chỉ nhìn lịch sử giá xăng của chính nó để tìm quy luật lặp lại. | Kiểm tra: chỉ nhìn quá khứ của chính giá xăng có đủ không? |
| **M2** | Hồi quy động (ADL) | Một phương trình tuyến tính: giá xăng mai = a × Brent đêm qua + b × xăng hôm nay + … | Mô hình kinh tế lượng chuẩn, dễ giải thích. |
| **M3** | Hồi quy bất đối xứng | Như M2, nhưng tách riêng "Brent tăng" và "Brent giảm". | Kiểm tra hiện tượng **"tăng như tên lửa, giảm như lông vũ"**. |
| **M4** | LightGBM kỹ thuật | Hàng trăm cây quyết định nhỏ cùng "bỏ phiếu", dùng biến giá và biến động. | Học máy, bắt được quan hệ phi tuyến. |
| **M5** | LightGBM kinh tế | Như M4, cộng thêm các biến chênh lệch lọc dầu. | Kiểm tra: **kinh tế nhà máy lọc dầu có giúp dự báo tốt hơn không?** |
| **RNN / LSTM** | Mạng nơ-ron hồi quy | Đọc chuỗi 20 ngày gần nhất như đọc một câu văn rồi đoán tiếp. | Mốc so sánh với học sâu (deep learning). |

**Hai câu hỏi nghiên cứu chính:**

- **RQ1:** giá xăng Singapore có phản ứng **khác nhau** khi dầu thô tăng so với khi dầu thô giảm không? (So sánh M3 với M2.)
- **RQ2:** thông tin kinh tế của nhà máy lọc dầu có **giúp dự báo tốt hơn** không? (So sánh M5 với M4.)

---

## 6. Cách xây dựng và kiểm tra cho công bằng

### 6.1 "Thi thật, không xem đề trước" (walk-forward)

Cách đánh giá giống một kỳ thi kéo dài 3 năm:

1. Mô hình học dữ liệu từ đầu đến hôm qua.
2. Sáng nay mô hình đưa ra dự báo. Chiều nay so với giá thật.
3. Thêm ngày hôm nay vào dữ liệu học, rồi lặp lại cho ngày mai.

Mô hình được **học lại định kỳ** (mô hình kinh tế lượng học lại mỗi ngày, học máy học lại mỗi 20 ngày). Mô hình **không bao giờ được thấy dữ liệu của ngày nó đang dự báo**.

### 6.2 Khi dự báo xa hơn: phải "bỏ một khoảng trắng"

Với dự báo 1 tuần (5 phiên) hay 1 tháng (21 phiên), đáp án của một ngày huấn luyện chỉ biết được sau 5 hoặc 21 ngày. Vì vậy, khi dự báo vào ngày τ, mô hình chỉ được học những ngày mà **đáp án đã có trước τ**, cộng thêm một khoảng đệm an toàn (2 ngày cho tuần, 5 ngày cho tháng). Nếu không làm vậy, mô hình sẽ vô tình "chép đáp án". Lỗi này rất phổ biến trong các nghiên cứu tài chính.

### 6.3 Học sâu dùng nhiều lần chạy

RNN và LSTM được huấn luyện **5 lần với 5 hạt giống ngẫu nhiên khác nhau**, sau đó lấy trung bình. Cách này tránh kết quả "ăn may" do một lần khởi tạo tốt.

---

## 7. Đánh giá bằng thước đo nào?

| Thước đo | Hỏi câu gì? | Đọc thế nào |
|---|---|---|
| **RMSE / MAE** | Trung bình đoán lệch bao nhiêu điểm %? | Càng **nhỏ** càng tốt. |
| **R²_OOS** | Giảm được bao nhiêu % sai số so với đoán "đứng yên" (M0a)? | **> 0** là có ích, **< 0** là thua cả đoán đứng yên. Ví dụ 40% nghĩa là giảm 40% sai số bình phương. |
| **DA (độ chính xác hướng)** | Đoán đúng **tăng/giảm** bao nhiêu % số ngày? | Đoán bừa được khoảng 50%. Trên 55% đã đáng chú ý. |
| **MCC** | Đoán hướng có thật sự tốt, hay chỉ nhờ luôn đoán "tăng"? | Từ −1 đến 1. Bằng 0 là vô dụng. |
| **Kiểm định Pesaran–Timmermann** | Tỷ lệ đúng hướng có phải do may mắn không? | p < 0,05 nghĩa là không phải may mắn. |
| **Kiểm định Diebold–Mariano** | Mô hình A có **thật sự** tốt hơn B, hay chênh lệch chỉ do ngẫu nhiên? | p < 0,05 nghĩa là chênh lệch có thật. |
| **Kiểm định Clark–West** | Như trên, nhưng dành cho trường hợp B là A cộng thêm biến (ví dụ M5 = M4 + biến lọc dầu). | p < 0,05 nghĩa là các biến thêm vào có giá trị. |

> **Vì sao cần kiểm định thống kê?** Trong 754 ngày, hai mô hình chênh nhau 0,5% độ chính xác có thể chỉ là may rủi. Kiểm định cho biết chênh lệch đó có đáng tin hay không.

---

## 8. Kết quả cuối cùng

Kỳ kiểm tra từ 28/12/2022 đến 29/12/2025. Mọi mô hình được so trên **cùng các ngày** và học trên **cùng dữ liệu** 2017+.

### 8.1 Dự báo ngày mai (754 ngày)

| Mô hình | Sai số RMSE (điểm %) | Giảm sai số so với "đứng yên" | Đúng hướng | MCC |
|---|---|---|---|---|
| M0a – Đoán đứng yên | 1,80 | 0% (gốc) | 48,4% | 0,00 |
| M0b – Theo quán tính | 2,54 | **−98,9%** (tệ hơn gần gấp đôi) | 51,2% | 0,02 |
| M1 – ARMA | 1,81 | −1,4% | 48,5% | −0,03 |
| **M2 – Hồi quy động** | **1,40** | **+39,8%** | 69,1% | 0,38 |
| M3 – Hồi quy bất đối xứng | 1,40 | +39,4% | 68,8% | 0,38 |
| **M4 – LightGBM kỹ thuật** | 1,42 | +37,6% | **70,8%** | **0,42** |
| M5 – LightGBM kinh tế | 1,42 | +38,1% | 70,4% | 0,41 |
| RNN | 1,44 | +36,0% | 68,8% | 0,38 |
| LSTM | 1,47 | +33,5% | 67,9% | 0,38 |

**Đọc bảng:**

- Mọi mô hình **có dùng giá dầu Brent** (M2 đến LSTM) đều đoán đúng hướng khoảng **68–71%** và giảm khoảng **35–40%** sai số. Tất cả đều có ý nghĩa thống kê rất mạnh (p < 10⁻²⁰).
- Các mô hình **chỉ nhìn giá xăng của chính nó** (M0b, M1) **không thắng nổi** cách đoán "đứng yên". Giá xăng gần như không có "đà" tự thân, nên thông tin hữu ích nằm ở dầu thô.
- **Mô hình đơn giản nhất có dùng Brent (M2) ngang ngửa hoặc nhỉnh hơn AI.** LightGBM đoán hướng tốt hơn khoảng 1,5 điểm %, nhưng sai số lớn hơn một chút. Kiểm định DM cho thấy chênh lệch giữa M2 và M4 **không có ý nghĩa**. RNN và LSTM còn **kém M2 có ý nghĩa thống kê**.

### 8.2 Dự báo 1 tuần và 1 tháng

| Kỳ hạn | Mô hình tốt nhất | Giảm sai số so với "đứng yên" | Đúng hướng |
|---|---|---|---|
| 1 ngày | M2 | **+39,8%** | 69–71% |
| 1 tuần (5 phiên) | M4 | +4,6% (nhỏ) | khoảng 56% |
| 1 tháng (21 phiên) | Không có | Mọi mô hình đều **âm** (M2 −16%, M5 −41%, LSTM −107%) | khoảng 50–53% |

Mức cải thiện **giảm rất nhanh theo kỳ hạn**. Điều này khớp với ý tưởng ở mục 3: lợi thế đến từ biến động Brent **đêm qua**. Sau vài ngày, thông tin đó đã được thị trường hấp thụ hết, và giá xăng xa hơn gần như là "bước đi ngẫu nhiên".

### 8.3 Trả lời hai câu hỏi nghiên cứu

**RQ1 – "Tăng như tên lửa, giảm như lông vũ"?** **Không.** Trong mô hình M3:

- Khi Brent tăng 1%, xăng tăng khoảng **0,670%**.
- Khi Brent giảm 1%, xăng giảm khoảng **0,674%**. Gần như y hệt.

Kiểm định Wald không bác bỏ giả thuyết đối xứng (p = 0,95 cho phản ứng tức thời; p = 0,88 cho kiểm định tổng hợp). M3 cũng không dự báo tốt hơn M2. **Ở cấp giá bán buôn Singapore, truyền dẫn từ dầu thô là đối xứng.** Hiện tượng bất đối xứng mà người tiêu dùng hay than phiền, nếu có, nhiều khả năng nằm ở khâu **bán lẻ**, không phải ở thị trường bán buôn.

**RQ2 – Kinh tế nhà máy lọc dầu có giúp dự báo không?** **Có, nhưng rất ít.**

- So với M4, M5 giảm sai số bình phương khoảng **0,8%**.
- Kiểm định Clark–West có ý nghĩa ở mức 5% (p = 0,035), nhưng kiểm định Diebold–Mariano thì không (p = 0,24).
- Kết luận trung thực: **có tín hiệu, nhưng yếu, chưa đủ để khẳng định chắc chắn**.

---

## 9. Ý kiến cá nhân: điểm mạnh, điểm yếu, nên trình bày thế nào

**Điểm mạnh nên nhấn mạnh:**

1. **Quy trình chống "nhìn trộm tương lai" rất chặt:** chốt giờ 08:30, kiểm tra từng dòng dữ liệu, và bỏ khoảng trắng khi dự báo xa. Phần lớn nghiên cứu sinh viên mắc lỗi ở khâu này.
2. **So sánh công bằng:** cùng ngày kiểm tra, cùng dữ liệu, có mô hình gốc để so, có kiểm định thống kê thay vì chỉ so con số.
3. **Phát hiện có ý nghĩa thực tế:** độ trễ múi giờ giữa Brent và Singapore cho phép dự báo đúng hướng khoảng 70% cho ngày hôm sau.
4. **Kết quả trung thực:** không có bất đối xứng; AI không thắng hồi quy đơn giản; dự báo dài hạn thất bại. Các kết quả âm tính được trình bày thẳng thắn làm nghiên cứu **đáng tin hơn**.

**Điểm yếu nên chủ động thừa nhận:**

1. Độ chính xác 70% chủ yếu đến từ **một biến duy nhất** (Brent đêm qua). Vì vậy giá trị thực tiễn phụ thuộc vào việc người dùng có kịp hành động giữa 08:30 và 16:30 hay không.
2. Mô hình học sâu chỉ được huấn luyện **một lần**, không học lại định kỳ như các mô hình khác. So sánh vì thế hơi thiệt cho DL.
3. Giai đoạn kiểm tra 2023–2025 tương đối "bình thường". Chưa kiểm tra trong khủng hoảng lớn như 2008 hay 2020 với mô hình học máy.
4. Trong quá trình rà soát, nhóm đã phát hiện và sửa một số lỗi tính toán: M1 ARMA không thực sự dự báo, M0b bị chấm trên nhãn sai, công thức kiểm định PT/DM có sai sót. Chi tiết nằm trong `reports/01_point_forecasting/02_BAO_CAO_KY_THUAT_M0_M5_DL.md`. Các con số ở đây là **sau khi sửa**.

**Nếu chỉ được nói một câu với giảng viên:**

> *"Giá xăng bán buôn Singapore ngày mai phần lớn được quyết định bởi giá dầu Brent đêm nay. Một mô hình hồi quy đơn giản khai thác điều này đoán đúng hướng khoảng 70% số ngày, ngang với AI phức tạp. Phản ứng giá là đối xứng khi dầu tăng hay giảm. Lợi thế dự báo này biến mất khi nhìn xa hơn một tuần."*

---

## 10. Câu hỏi giảng viên có thể hỏi

| Câu hỏi | Gợi ý trả lời |
|---|---|
| "70% có phải do rò rỉ dữ liệu không?" | Không. Giá Brent đêm qua chốt khoảng 02:30, trước mốc dự báo 08:30. Mỗi dòng dữ liệu đều được kiểm tra thời điểm có thông tin. Mô hình chỉ dùng thông tin Singapore chưa kịp phản ánh. |
| "Sao AI không thắng hồi quy?" | Quan hệ chính (xăng ≈ 0,67 × Brent) gần như tuyến tính, nên mô hình tuyến tính đã bắt được gần hết. AI chỉ có lợi khi có quan hệ phi tuyến phức tạp, mà ở đây không có nhiều. |
| "Đoán đúng hướng 70% thì có kiếm tiền được không?" | Chưa chắc. Nghiên cứu chưa tính phí giao dịch, và cũng chưa xét liệu người dùng có thể giao dịch theo giá Platts trước 16:30 hay không. Đây là hướng phát triển tiếp theo. |
| "Tại sao dự báo tháng lại tệ hơn đoán đứng yên?" | Sau vài ngày, thông tin Brent đã được hấp thụ, phần còn lại gần như ngẫu nhiên. Mô hình phức tạp thì "học thuộc nhiễu" nên còn tệ hơn. |
| "Tại sao không dự báo giá tuyệt đối?" | Giá tuyệt đối có xu hướng trôi theo thời gian (không dừng), dễ tạo ra tương quan giả. Dự báo % thay đổi là cách chuẩn trong tài chính. |
