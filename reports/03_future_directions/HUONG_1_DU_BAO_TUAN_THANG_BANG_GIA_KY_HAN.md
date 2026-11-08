# Hướng 1: Dự báo giá xăng Singapore 1 tuần và 1 tháng bằng giá kỳ hạn (swap/futures)

*Kế hoạch mở rộng dự án SPAFS V5.2. Ngày soạn: 07/11/2026.*

---

## 1. Vì sao cần hướng này?

Kết quả hiện tại của dự án (sau khi sửa lỗi) cho thấy:

| Kỳ hạn | Mô hình tốt nhất | Giảm sai số so với đoán "đứng yên" |
|---|---|---|
| 1 ngày | M2 (hồi quy theo Brent) | **+39,8%** |
| 1 tuần | M4 (LightGBM) | +4,6% |
| 1 tháng | Không có | Mọi mô hình đều âm (từ −16% đến −107%) |

Lợi thế dự báo 1 ngày đến từ **biến động Brent đêm qua** mà Singapore chưa kịp phản ánh. Sau vài ngày, thông tin này đã được hấp thụ hết. Dữ liệu hiện có (giá giao ngay Platts và Brent hợp đồng gần nhất) **không chứa thông tin nào nhìn về tương lai**, nên mô hình phức tạp hơn cũng không giúp được.

**Ý tưởng của hướng 1:** thị trường kỳ hạn (swap và futures) công bố hằng ngày **mức giá mà người mua bán đang chấp nhận cho các tháng tới**. Đây là nguồn thông tin "nhìn về phía trước" tốt nhất có thể có, được tổng hợp từ toàn bộ thị trường: tồn kho, nhà máy, vận tải, kỳ vọng OPEC. Hướng này đặt ra hai câu hỏi:

1. **Giá kỳ hạn dự báo giá xăng tuần hoặc tháng tới tốt đến đâu?** Câu trả lời trở thành mốc so sánh mới, trung thực hơn đoán "đứng yên".
2. **Mô hình của nhóm có thắng được giá kỳ hạn không?** Ví dụ bằng cách thêm độ dốc đường cong, biên lọc dầu kỳ hạn, hay độ biến động.

---

## 2. Thay đổi trong cách đặt bài toán

### 2.1 Mục tiêu dự báo mới: giá **trung bình** của kỳ tới

Swap xăng Singapore **thanh toán theo giá trung bình** của các phiên Platts trong tháng, không theo giá của một ngày. Để so sánh công bằng với swap, nhóm đề xuất thêm hai mục tiêu:

| Mục tiêu | Định nghĩa | Ghi chú |
|---|---|---|
| `target_avg_week` | ln(trung bình MG95 của 5 phiên tới / MG95 hôm nay) × 100 | Thay cho lợi suất đúng ngày thứ 5 |
| `target_avg_month` | ln(trung bình MG95 của 21 phiên tới / MG95 hôm nay) × 100 | Thay cho lợi suất đúng ngày thứ 21 |
| `target_calmonth_next` | ln(trung bình MG95 **tháng dương lịch kế tiếp** / MG95 hôm nay) × 100 | Khớp chính xác với swap M1 |

Lợi ích của giá trung bình:

- Khớp với cách swap thanh toán.
- Ít nhiễu hơn giá một ngày.
- **Sát thực tế Việt Nam:** giá cơ sở xăng dầu trong nước được tính theo bình quân giá Platts trong kỳ điều hành.

Các mục tiêu cũ (`target_return_weekly`, `target_return_monthly`) vẫn được giữ để so sánh.

### 2.2 Mốc so sánh mới: M0c, "tin vào thị trường kỳ hạn"

```
dự báo M0c (tháng tới)    = ln(swap Mogas 95 tháng M1 / MG95 hôm nay) × 100
dự báo M0c (tuần, 21 phiên) = nội suy giữa swap tháng hiện tại (balance-of-month) và swap M1
```

**Quy tắc đánh giá:** mô hình nào không thắng M0c thì không có giá trị thực tế, vì người dùng chỉ cần nhìn giá swap là đủ.

---

## 3. Dữ liệu cần bổ sung

### 3.1 Danh sách theo mức ưu tiên

| Ưu tiên | Bộ dữ liệu | Nội dung cần lấy | Tần suất / giai đoạn | Vai trò |
|---|---|---|---|---|
| **P1 – bắt buộc** | **Swap xăng Singapore** (Mogas 95; nếu không có thì Mogas 92) | Giá chốt cho tháng hiện tại (balance-of-month), M1, M2, M3 | Hằng ngày, 2008–2025 (tối thiểu 2017–2025) | Mốc M0c và biến "kỳ vọng thị trường" |
| **P1 – bắt buộc** | **Đường cong Brent futures (ICE)** | Giá chốt M1 đến M6, kèm tháng hợp đồng và ngày đáo hạn | Hằng ngày, 2008–2025 | Độ dốc đường cong dầu thô (thiếu hay dư hàng) |
| **P2 – nên có** | **Chênh lệch MG95 – MG92 kỳ hạn** | Giá M1 đến M3 | Hằng ngày | Quy đổi swap 92 thành swap 95 (swap 95 ít thanh khoản hơn) |
| **P2 – nên có** | **Crack swap xăng Singapore** (xăng 92 – Brent, kỳ hạn) | Giá M1 đến M3 | Hằng ngày | Kỳ vọng biên lọc dầu tương lai |
| **P3 – tuỳ chọn** | **Dubai swap / Brent–Dubai EFS** | Giá M1 đến M3 | Hằng ngày | Chi phí dầu thô của nhà máy châu Á |
| **P3 – tuỳ chọn** | **Tồn kho xăng dầu nhẹ Singapore** (Enterprise Singapore) | Tồn kho light distillates | Hằng tuần | Biến cung–cầu cơ bản |
| **Dự phòng (miễn phí)** | **NYMEX RBOB và WTI futures** (qua EIA) | Hợp đồng 1 đến 4 | Hằng ngày, 2008–2025 | Proxy để thử ý tưởng trước khi mua dữ liệu Singapore |

### 3.2 Thông tin đi kèm bắt buộc (metadata)

| Thông tin | Vì sao cần |
|---|---|
| **Thời điểm chốt giá** (giờ và múi giờ) | Để đưa vào cổng kiểm tra 08:30 SGT, tránh dùng thông tin chưa có. |
| **Tháng hợp đồng** của mỗi giá (ví dụ 2024-03) | Để biết "M1" vào từng ngày là tháng nào. |
| **Ngày đáo hạn / ngày giao dịch cuối** của từng hợp đồng | Để chuyển hợp đồng đúng ngày và tính giá kỳ hạn cố định. |
| **Cách thanh toán** (trung bình tháng hay một ngày) | Để chọn đúng mục tiêu so sánh (mục 2.1). |
| **Đơn vị** (USD/thùng, USD/tấn, cent/gallon) | RBOB tính theo USD/gallon, Brent và swap Singapore tính theo USD/thùng. |

### 3.3 Định dạng file đề xuất

Đặt dữ liệu thô tại `data/raw/forward/` theo định dạng **dài** (mỗi dòng là một giá của một hợp đồng trong một ngày):

| Cột | Kiểu | Ví dụ | Mô tả |
|---|---|---|---|
| `trade_date` | date | 2024-03-15 | Ngày giao dịch |
| `instrument` | str | `SG_MOGAS92_SWAP` | Mã sản phẩm do nhóm tự đặt (xem bảng dưới) |
| `contract_month` | str (YYYY-MM) | 2024-04 | Tháng hợp đồng |
| `tenor_label` | str | M1 | Nhãn theo cách nhà cung cấp gọi (BOM, M1, M2…) |
| `settle_price` | float | 92.35 | Giá chốt |
| `unit` | str | USD/bbl | Đơn vị |
| `settle_datetime_local` | datetime | 2024-03-15 16:30 | Thời điểm chốt, giờ địa phương |
| `settle_timezone` | str | Asia/Singapore | Múi giờ |
| `expiry_date` | date | 2024-04-30 | Ngày giao dịch cuối của hợp đồng |
| `source` | str | LSEG | Nguồn dữ liệu |

Mã `instrument` đề xuất:

| `instrument` | Sản phẩm |
|---|---|
| `SG_MOGAS95_SWAP` | Swap xăng 95 Singapore |
| `SG_MOGAS92_SWAP` | Swap xăng 92 Singapore |
| `SG_95_92_SPREAD_SWAP` | Chênh lệch kỳ hạn 95/92 |
| `SG_MOGAS92_CRACK_SWAP` | Crack swap xăng 92 – Brent |
| `ICE_BRENT_FUT` | Brent futures |
| `DUBAI_SWAP` | Dubai swap |
| `NYMEX_RBOB_FUT` | RBOB futures (dự phòng) |
| `NYMEX_WTI_FUT` | WTI futures (dự phòng) |

---

## 4. Lấy dữ liệu ở đâu và cách lấy

### 4.1 Tổng quan nguồn

| Nguồn | Có những gì | Chi phí | Mức khả thi với sinh viên |
|---|---|---|---|
| **LSEG Workspace (Refinitiv Eikon)** | Brent M1 đến M6, swap Singapore, crack, Dubai | Có tại nhiều thư viện hoặc khoa tài chính | **Cao nhất**, nếu trường có |
| **Bloomberg Terminal** | Như trên | Có tại một số trường | Cao, nếu trường có |
| **S&P Global Platts** (Platts Dimensions / Market Data) | Swap Mogas 95/92, crack, Dubai; chuẩn gốc | Đắt | Thấp. Hỏi qua doanh nghiệp đối tác. |
| **Doanh nghiệp xăng dầu** (Petrolimex, PV Oil, Saigon Petro…) | Thường có gói Platts | Xin hợp tác hoặc NDA | Trung bình |
| **CME Group / ICE** | Settlement từng hợp đồng: "Singapore Mogas 92 Unleaded (Platts)", Brent | Xem theo ngày miễn phí; lịch sử dài mua qua CME DataMine / ICE Data | Trung bình |
| **EIA – API miễn phí** | NYMEX RBOB và WTI các hợp đồng 1–4, giá giao ngay Brent | Miễn phí | **Lấy được ngay** |
| **Enterprise Singapore** | Tồn kho xăng dầu Singapore hằng tuần | Miễn phí (công bố công khai, có thể qua data.gov.sg) | Cao |

### 4.2 Cách lấy từ LSEG hoặc Bloomberg (khuyến nghị nếu trường có)

1. Liên hệ thư viện hoặc khoa để đặt lịch dùng máy có LSEG Workspace hoặc Bloomberg.
2. **Brent futures:**
   - LSEG có chuỗi hợp đồng liên tục `LCOc1`, `LCOc2`, …, `LCOc6` (Brent tháng 1 đến 6).
   - Nên tải **cả từng hợp đồng cụ thể** (theo tháng đáo hạn) để tự xử lý ngày chuyển hợp đồng.
3. **Swap xăng Singapore:**
   - Tìm theo từ khoá "Singapore Mogas 92 swap", "Mogas 95 swap", "Gasoline 92 crack Singapore", "Dubai swap".
   - Nhờ cán bộ hỗ trợ (hoặc chức năng tìm mã của terminal) xác nhận **mã chuỗi M1, M2, M3** và **cách thanh toán** của từng mã.
4. Xuất ra Excel hoặc CSV theo định dạng ở mục 3.3, giai đoạn 01/2008 đến 12/2025, tần suất ngày, lấy giá chốt (settlement/close).
5. Ghi lại **mã gốc** của từng chuỗi vào file `data/raw/forward/SOURCE_MAPPING.md` để có thể tái lập.

### 4.3 Cách lấy từ Platts hoặc doanh nghiệp

Gửi yêu cầu theo mẫu ở **Phụ lục A**. Hỏi rõ mã ký hiệu Platts (symbol code) cho:

- Mogas 92 và Mogas 95 swap (balance-of-month, M1 đến M3).
- Chênh lệch kỳ hạn 95/92.
- Crack swap xăng 92 – Brent.
- Dubai swap.

### 4.4 Cách lấy miễn phí qua EIA (làm thử ngay)

EIA (Cơ quan Thông tin Năng lượng Mỹ) công bố giá NYMEX futures hằng ngày, miễn phí:

1. Đăng ký API key miễn phí tại `https://www.eia.gov/opendata/`.
2. Dùng API v2, nhóm dữ liệu giá futures dầu mỏ (`petroleum/pri/fut`). Các chuỗi cần lấy:
   - **WTI Cushing, hợp đồng 1–4:** mã chuỗi dạng `RCLC1`, `RCLC2`, `RCLC3`, `RCLC4`.
   - **RBOB Regular Gasoline NY Harbor, hợp đồng 1–4:** mã chuỗi dạng `EER_EPMRR_PE1_Y35NY_DPG` đến `..._PE4_...`.
   - **Giá giao ngay Brent** (nhóm `petroleum/pri/spt`): mã `RBRTE`, dùng để đối chiếu.
3. Ví dụ truy vấn (thay `YOUR_KEY`):

   ```
   https://api.eia.gov/v2/petroleum/pri/fut/data/?api_key=YOUR_KEY
     &frequency=daily&data[0]=value
     &facets[series][]=RCLC1&facets[series][]=RCLC2
     &start=2008-01-01&end=2025-12-31
   ```

> **Lưu ý:** cần kiểm tra lại mã chuỗi và đường dẫn trên trang API Browser của EIA trước khi chạy, vì EIA đôi khi đổi cấu trúc.

**Giới hạn của dữ liệu EIA:**

- Chỉ có "hợp đồng 1, 2, 3, 4" theo thứ tự, không có ngày đáo hạn. Phải tự dựng lịch đáo hạn NYMEX.
- Đây là thị trường **Mỹ**, nên chỉ dùng làm **proxy** để kiểm chứng ý tưởng, không thay được swap Singapore.

### 4.5 Brent theo từng tháng hợp đồng (miễn phí, kém tin cậy hơn)

Investing.com và Barchart có lịch sử giá từng hợp đồng Brent theo tháng đáo hạn. Có thể tải tay hoặc thu thập tự động. Đây chỉ là phương án tạm: dữ liệu có thể thiếu ngày, và cần kiểm tra điều khoản sử dụng của trang.

---

## 5. Quy tắc thời điểm (point-in-time)

Dự án đang khoá mốc dự báo lúc **08:30 SGT sáng ngày t+1**. Dữ liệu mới phải tuân theo đúng quy tắc này:

| Dữ liệu | Thời điểm chốt | Giờ có dữ liệu (SGT) | Dùng được tại 08:30 SGT ngày t+1? |
|---|---|---|---|
| Swap Singapore ngày t | 16:30 SGT ngày t (Platts MOC) | khoảng 17:00–18:00 ngày t | Có |
| Brent futures ngày t | khoảng 19:30 giờ London | khoảng 02:30–03:30 ngày t+1 | Có (giống `brent_return_pct_aligned` hiện tại) |
| NYMEX RBOB/WTI ngày t | 14:30 giờ New York | khoảng 02:30–03:30 ngày t+1 | Có |
| Tồn kho Singapore tuần | Công bố theo lịch (thường giữa tuần) | Theo ngày công bố | Chỉ dùng **từ ngày công bố trở đi** |

Khi nạp dữ liệu, cần tạo cột `availability_datetime` (quy về SGT) và đưa qua cùng cổng kiểm tra `availability_datetime <= forecast_origin_datetime` đang dùng trong `src/data_proccessing/data_handling/alignment.py`.

---

## 6. Xử lý dữ liệu kỳ hạn

### 6.1 Chuyển hợp đồng và giá kỳ hạn cố định

Chuỗi "M1" sẽ nhảy cóc vào ngày chuyển hợp đồng. Để tránh nhiễu giả, nhóm đề xuất:

- **Giá kỳ hạn cố định (constant maturity):** nội suy tuyến tính giữa hai hợp đồng kề nhau, để có giá "đúng 1 tháng tới", "đúng 2 tháng tới"…
- **Lợi suất kỳ hạn:** chỉ tính trên **cùng một hợp đồng** giữa hai ngày liên tiếp, không tính trên chuỗi M1 đã nối.

### 6.2 Kiểm tra chất lượng (tương tự Gate 1.1/1.2 của dự án)

- Không trùng `(trade_date, instrument, contract_month)`.
- Giá dương. Bước nhảy theo ngày vượt ±25% thì gắn cờ để kiểm tra.
- Mỗi ngày giao dịch có đủ M1 đến M3. Ngày thiếu thì ghi vào báo cáo kiểm toán.
- Swap M1 phải hội tụ về trung bình giá giao ngay của tháng đó. Đây là cách kiểm tra **cách thanh toán** đã hiểu đúng hay chưa.
- Ngày giao dịch Singapore và London không trùng hoàn toàn: dùng giá gần nhất **đã có** trước 08:30 SGT, không nội suy về phía trước.

---

## 7. Biến mới sẽ tạo ra

| Biến | Công thức | Ý nghĩa |
|---|---|---|
| `fwd_premium_m1` | ln(swap MG95 M1 / MG95 giao ngay) × 100 | Mức tăng/giảm thị trường đang kỳ vọng cho tháng tới |
| `fwd_premium_bom` | ln(swap tháng hiện tại / MG95 giao ngay) × 100 | Kỳ vọng cho phần còn lại của tháng |
| `swap_slope_m1_m2` | swap M1 − swap M2 | Dương là backwardation (thiếu hàng), âm là contango (dư hàng) |
| `brent_slope_m1_m3`, `brent_slope_m1_m6` | Brent M1 − M3, M1 − M6 | Trạng thái cung–cầu dầu thô |
| `crack_fwd_m1` | swap xăng M1 − Brent M1 | Biên lọc dầu kỳ vọng |
| `crack_fwd_gap` | `crack_fwd_m1` − trung bình 3 tháng của crack giao ngay | Kỳ vọng biên lọc dầu quay về mức bình thường |
| `swap_ret_5d`, `swap_ret_20d` | Lợi suất 5 và 20 ngày của swap M1 (cùng hợp đồng) | Đà giá trên thị trường kỳ hạn |
| `stocks_sg_dev` (P3) | Tồn kho Singapore − trung bình cùng kỳ 5 năm | Dư hay thiếu so với mùa vụ |

---

## 8. Kế hoạch thực nghiệm

### Giai đoạn 0: Thử ý tưởng bằng dữ liệu miễn phí (1–2 tuần)

1. Lấy RBOB và WTI hợp đồng 1–4 qua EIA (mục 4.4).
2. Tạo các biến độ dốc đường cong (RBOB 1−2, WTI 1−3), ghép vào bộ dữ liệu Luồng 2 theo quy tắc ở mục 5.
3. Chạy lại các kỳ hạn tuần và tháng với engine walk-forward hiện có (`src/models/validation/walk_forward.py`, purge = h, embargo 2 và 5).
4. **Câu hỏi cần trả lời:** độ dốc đường cong có làm R²_OOS tuần/tháng **dương và có ý nghĩa** không?

### Giai đoạn 1: Dữ liệu Singapore thật (sau khi có P1)

1. Nạp swap Singapore và đường cong Brent, kiểm tra chất lượng (mục 6.2).
2. Thêm các mục tiêu trung bình (mục 2.1) vào `multi_horizon_targets.py`.
3. Xây mốc **M0c** và đánh giá nó so với M0a (đứng yên). Đây là kết quả đáng báo cáo ngay cả khi không có mô hình nào khác.
4. Xây các mô hình ứng viên. Ở kỳ hạn dài tín hiệu yếu, nên **ưu tiên mô hình đơn giản**:

   | Mã đề xuất | Mô hình | Mô tả |
   |---|---|---|
   | **M7** | Hồi quy có ràng buộc (ridge) | Mục tiêu trên `fwd_premium`, độ dốc, crack gap |
   | **M8** | Điều chỉnh M0c | Dự báo = M0c + β × (độ lệch crack, độ dốc); β co mạnh về 0 |
   | **M9** | LightGBM | Đủ các biến mới, chủ yếu để so sánh |

5. Đánh giá bằng module chung `src/models/evaluation/forecast_tests.py`:
   - R²_OOS so với **M0c** (không chỉ so với M0a).
   - Kiểm định DM và CW với `horizon = 5` hoặc `21`.
   - Tỷ lệ đúng hướng (DA).
   - PT **không dùng** cho mục tiêu chồng lấp.

### Kỳ vọng thực tế

- **M0c** nhiều khả năng thắng M0a ở kỳ hạn tháng, nhưng không nhiều.
- Mô hình của nhóm thắng được M0c dù chỉ **1–3% R²_OOS** đã là kết quả tốt theo chuẩn tài liệu nghiên cứu.
- Mẫu kỳ hạn tháng chỉ có khoảng **35 tháng độc lập** trong giai đoạn kiểm tra 2023–2025, nên cần dùng giai đoạn 2008–2025 nếu có dữ liệu.

---

## 9. Rủi ro và cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| Không mua hoặc xin được swap Singapore | Dùng proxy EIA (RBOB, WTI) và Brent curve. Ghi rõ đây là giới hạn của nghiên cứu. |
| Swap Mogas 95 thưa giao dịch, nhiều ngày trống | Dùng swap 92 cộng chênh lệch 95/92 kỳ hạn. Nếu không có chênh lệch kỳ hạn, dùng chênh lệch giao ngay hiện tại. |
| Hiểu sai cách thanh toán (trung bình tháng hay một ngày) | Kiểm tra hội tụ ở mục 6.2 trước khi dựng mô hình. |
| Lỗi ngày chuyển hợp đồng tạo lợi suất giả | Chỉ tính lợi suất trên cùng hợp đồng (mục 6.1). |
| Điều khoản bản quyền dữ liệu (Platts, LSEG) | Không đưa dữ liệu thô lên GitHub công khai. Chỉ lưu kết quả tổng hợp. Thêm `data/raw/forward/` vào `.gitignore`. |

---

## Phụ lục A: Mẫu email xin dữ liệu

> **Tiêu đề:** Xin hỗ trợ dữ liệu giá kỳ hạn xăng dầu Singapore phục vụ nghiên cứu học thuật
>
> Kính gửi Anh/Chị,
>
> Nhóm nghiên cứu [tên nhóm / trường] đang thực hiện đề tài dự báo giá xăng Platts FOB Singapore Mogas 95. Nhóm xin hỗ trợ trích xuất dữ liệu **giá chốt hằng ngày, giai đoạn 01/2008 – 12/2025**, gồm:
>
> 1. Swap Singapore Mogas 95 và Mogas 92: balance-of-month, M1, M2, M3.
> 2. Chênh lệch kỳ hạn Mogas 95/92: M1 đến M3.
> 3. Crack swap Singapore Mogas 92 vs Brent: M1 đến M3.
> 4. ICE Brent futures: M1 đến M6, kèm tháng hợp đồng và ngày đáo hạn.
> 5. (Nếu có) Dubai swap M1 đến M3.
>
> Với mỗi chuỗi, nhóm mong được biết **mã ký hiệu, đơn vị, thời điểm chốt giá và cách thanh toán** (trung bình tháng hay một ngày). Định dạng mong muốn: CSV hoặc Excel.
>
> Dữ liệu chỉ dùng cho mục đích học thuật, không chia sẻ cho bên thứ ba và không công bố dữ liệu thô. Nhóm sẵn sàng ký thoả thuận bảo mật nếu cần.
>
> Trân trọng,
> [Họ tên, email, số điện thoại, giảng viên hướng dẫn]

---

## Phụ lục B: Checklist trước khi bắt đầu mô hình

- [ ] Có ít nhất swap M1 (92 hoặc 95) và Brent M1 đến M3, hằng ngày, từ 2017 trở đi.
- [ ] Mỗi chuỗi có mã gốc, đơn vị, thời điểm chốt và cách thanh toán (ghi trong `SOURCE_MAPPING.md`).
- [ ] Có lịch đáo hạn hợp đồng.
- [ ] Đã kiểm tra hội tụ swap M1 so với trung bình giá giao ngay tháng tương ứng.
- [ ] Đã tạo `availability_datetime` (SGT) và qua được cổng kiểm tra 08:30.
- [ ] Đã thêm `data/raw/forward/` vào `.gitignore` nếu dữ liệu có bản quyền.
