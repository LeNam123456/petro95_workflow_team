# NHẬT KÝ KIỂM TOÁN SỬ DỤNG TRÍ TUỆ NHÂN TẠO — ĐỢT 1 (AI AUDIT LOG — PHASE 1)
## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)
### Báo Cáo Minh Bạch Học Thuật & Quản Trị Tương Tác AI (Academic Integrity & AI Disclosure Report)

* **Tên đề tài:** Dự Báo Tỷ Suất Thay Đổi & Hướng Biến Động Chuẩn Giá Platts FOB Singapore Mogas 95
* **Dự án mã nguồn:** `petro95_workflow_team` (Repository: `https://github.com/LeNam123456/petro95_workflow_team.git`)
* **Tác giả / Nghiên cứu viên:** Lê Nam (LeNam123456)
* **Giai đoạn báo cáo (Phase):** Đợt 1 — Nền Tảng Dữ Liệu, Quản Trị Thời Gian Thực (PIT) & Kiểm Toán Hợp Đồng Dữ Liệu
* **Thời gian thực hiện:** Tháng 09/2026 – Tháng 10/2026
* **Công cụ AI hỗ trợ:** Google Antigravity AI Assistant (Model: Gemini 3.8 Flash High)
* **Chuẩn liêm chính học thuật áp dụng:** Khung minh bạch AI của Elsevier / COPE (Committee on Publication Ethics) & Quy chế Đào tạo / Nghiên cứu Khoa học

---

## 📑 MỤC LỤC
1. [BẢN CHẤT & MỤC ĐÍCH CỦA VIỆC NỘP AI AUDIT LOG ĐỢT 1](#1-bản-chất--mục-đích-của-việc-nộp-ai-audit-log-đợt-1)
2. [MA TRẬN PHÂN ĐỊNH TRÁCH NHIỆM: CON NGƯỜI (HUMAN) VS AI](#2-ma-trận-phân-định-trách-nhiệm-con-người-human-vs-ai)
3. [NHẬT KÝ TỔNG HỢP CÁC PHIÊN LÀM VIỆC ĐỢT 1 (SESSION LOGS)](#3-nhật-ký-tổng-hợp-các-phiên-làm-việc-đợt-1-session-logs)
4. [KIỂM SOÁT ẢO GIÁC & CƠ CHẾ KIỂM CHỨNG KHOA HỌC (VERIFICATION & RIGOR)](#4-kiểm-soát-ảo-giác--cơ-chế-kiểm-chứng-khoa-học-verification--rigor)
5. [CÁC QUYẾT ĐỊNH PHƯƠNG PHÁP LUẬN QUAN TRỌNG DO CON NGƯỜI CHỈ ĐẠO](#5-các-quyết-định-phương-pháp-luận-quan-trọng-do-con-người-chỉ-đạo)
6. [TỔNG KẾT ARTIFACTS ĐỢT 1 & CAM KẾT LIÊM CHÍNH](#6-tổng-kết-artifacts-đợt-1--cam-kết-liêm-chính)

---

## 1. BẢN CHẤT & MỤC ĐÍCH CỦA VIỆC NỘP AI AUDIT LOG ĐỢT 1

### 1.1. "AI Audit Log Đợt 1" là gì?
**AI Audit Log (Nhật ký Kiểm toán Sử dụng AI)** là hồ sơ khoa học ghi nhận lại một cách minh bạch, có hệ thống toàn bộ quá trình tương tác giữa Nghiên cứu viên (Con người) và các hệ thống Trí tuệ Nhân tạo tạo sinh (AI) trong suốt quá trình triển khai đề tài.

**"Đợt 1" (Phase 1 / Milestone 1)** đánh dấu mốc hoàn thành **Tầng Nền tảng Dữ liệu & Thiết kế Phương pháp luận (Data Foundation & Methodology Layer)**. Việc nộp AI Audit Log Đợt 1 phục vụ các mục đích cốt lõi:
1. **Chứng minh Quyền Tác Giả & Vai Trò Lãnh Đạo (Human Agency):** Chứng minh rằng toàn bộ ý tưởng nghiên cứu, bản chất bài toán kinh tế, các phát hiện về độ trễ thị trường và quyết định kiến trúc đều xuất phát từ tư duy của người nghiên cứu; AI chỉ đóng vai trò là "công cụ hỗ trợ lập trình và tăng tốc tính toán".
2. **Minh Bạch Học Thuật Tuyệt Đối (Full Scientific Disclosure):** Tuân thủ tuyệt đối quy định của Hội đồng Khoa học, Nhà trường và các tạp chí quốc tế Scopus Q2/Q3 (*Energy Economics, Energy Reports*) về việc công khai công cụ AI.
3. **Chống Ảo Giác & Bịa Đặt Dữ Liệu (Hallucination Audit):** Xác thực rằng mọi con số thực nghiệm ($N = 4,428$, $p = 0.9552$, $R^2 = 31.22\%$) đều được tính toán từ dữ liệu thực tế trên máy tính, không bị AI "tự vẽ ra".
4. **Bảo Vệ Luận Văn / Khóa Luận Trước Hội Đồng:** Giúp nghiên cứu viên tự tin giải trình với giảng viên hướng dẫn và hội đồng chấm thi về quy trình làm việc độc lập, khoa học và chuyên nghiệp.

---

## 2. MA TRẬN PHÂN ĐỊNH TRÁCH NHIỆM: CON NGƯỜI (HUMAN) VS AI

| Khía Cạnh | Vai Trò Của Nghiên Cứu Viên (Lê Nam) | Vai Trò Hỗ Trợ Của AI (Antigravity Assistant) |
| :--- | :--- | :--- |
| **Xác định Đề tài & Bài toán** | • Lựa chọn chuẩn giá Platts FOB Singapore MG95.<br>• Định hình 2 câu hỏi nghiên cứu cốt lõi (RQ1 Asymmetric Shocks vs RQ2 News Value). | • Gợi ý định dạng cấu trúc đề cương nghiên cứu theo chuẩn Scopus Q2/Q3. |
| **Phát hiện Vấn đề Thị trường** | • Phát hiện lệch múi giờ: Platts đóng 16:30 SGT, Brent đóng 03:00 SGT sáng hôm sau.<br>• Chỉ đạo thiết lập mốc Cutoff 08:30 SGT sáng ngày $t+1$. | • Viết mã nguồn Python mô phỏng chính xác mốc Cutoff PIT vào cấu hình hệ thống. |
| **Kiến Trúc Dữ Liệu** | • Đưa ra khung 15 hạng mục xử lý dữ liệu doanh nghiệp và gom nhóm thành 6 Layer.<br>• Thiết lập triết lý: *Outlier Detection $\ne$ Outlier Removal* để bảo tồn cú sốc kinh tế thật. | • Triển khai mã nguồn cấu trúc module (`config.py`, `aliases.py`, `pipeline.py`, `data_handling/`). |
| **Phương Pháp Luận Thống Kê** | • Bắt buộc dùng **Clark & West (2007)** thay cho Diebold-Mariano chuẩn do mô hình lồng nhau.<br>• Yêu cầu bổ sung kiểm định Pesaran-Timmermann và McNemar. | • Lập trình toán học chính xác các công thức hiệu chỉnh MSPE và phân phối xác suất. |
| **Kiểm Soát Chất Lượng & Đối Soát** | • Ra lệnh xóa toàn bộ mã nguồn cũ để yêu cầu kiểm tra code lên chat trước.<br>• Đặt câu hỏi truy xuất nguồn gốc số liệu: *"Từ đâu có kết quả như vậy?"*<br>• Phát hiện lỗi encoding dính byte null làm hỏng hiển thị README trên GitHub. | • Chạy script kiểm toán đối soát từng dòng dữ liệu.<br>• Giải trình chi tiết nguồn gốc phép tính OLS Newey-West.<br>• Sửa lỗi mã hóa sang UTF-8 thuần (0 byte null). |

---

## 3. NHẬT KÝ TỔNG HỢP CÁC PHIÊN LÀM VIỆC ĐỢT 1 (SESSION LOGS)

### Phiên 1: Khởi Tạo Dự Án & Định Danh Bài Toán Platts Singapore
* **Bối cảnh:** Bắt đầu từ dự án tại `D:\Petro_95` với file thô ban đầu `brent_crude_oil_historical.csv` và `crawl_data.ipynb`.
* **Vấn đề thảo luận:** Chuyển đổi định danh từ dự báo giá bán lẻ sang dự báo chuẩn giá bán buôn **Platts FOB Singapore Mogas 95 (MG95)**.
* **Đóng góp của Con người:** Yêu cầu chuyển trọng tâm sang tỷ suất sinh lời logarit $r_{t+1}$ làm Primary Target (chuỗi dừng $I(0)$) thay vì dự báo mức giá danh nghĩa $P_{t+1}$.
* **Hỗ trợ của AI:** Tìm kiếm và tích hợp bộ dữ liệu 4,559 dòng Platts (`price_petroleum.xlsx - Data.csv`) vào cấu trúc `data/raw/`.

### Phiên 2: Chuẩn Hóa Quản Trị Thời Gian Thực (Point-in-Time Control Plane)
* **Bối cảnh:** Reviewer hoặc Hội đồng dễ bắt bẻ lỗi rò rỉ tương lai (Lookahead Bias).
* **Đóng góp của Con người:**
  * Chỉ rõ bản chất phiên giao dịch: Platts MOC chốt 16:30 SGT, trong khi sàn ICE Brent chốt tại London lúc 03:00 SGT sáng hôm sau.
  * Quyết định dời $t_{origin}$ về **08:30 SGT sáng ngày $t+1$** để cả Platts và Brent đều sẵn sàng 100%.
  * Nêu ra Transparency Caveat: Brent chứa thông tin qua đêm nên kiểm định Wald phản ánh cả độ trễ đồng bộ múi giờ.
* **Hỗ trợ của AI:** Xây dựng hệ trục 5 mốc thời gian thực:
  $$\{ \text{observation\_datetime, publication\_datetime, availability\_datetime, forecast\_origin\_datetime, target\_market\_date} \}$$
  với điều kiện cứng $\text{availability} \le \text{origin}$.

### Phiên 3: Khung Thiết Kế Hai Mẫu Nghiên Cứu (Two-Sample Framework)
* **Bối cảnh:** Dữ liệu tin tức GDELT chỉ ổn định từ 2017, trong khi Platts kéo dài từ 2008.
* **Đóng góp của Con người:** Không chấp nhận gán `NEWS_COUNT = 0` cho giai đoạn 2008–2016 vì đó là "thiếu dữ liệu" chứ không phải "thị trường không có tin". Chỉ đạo chia thành 2 luồng độc lập: Luồng 1 (2008–2025) cho Kinh tế lượng, Luồng 2 (2017–2025) cho Học máy.
* **Hỗ trợ của AI:** Lập trình hàm cắt mẫu `patrition.py`, chia Luồng 2 thành Train (2017–2019, $N=749$) và Out-of-Sample Test (2020–2025, $N=1,508$).

### Phiên 4: Tái Cấu Trúc Theo Chuẩn Kỹ Nghệ Dữ Liệu Doanh Nghiệp (15 Mục / 6 Layer)
* **Bối cảnh:** Nghiên cứu viên đề xuất khung 15 hạng mục xử lý dữ liệu doanh nghiệp và yêu cầu cấu trúc lại SPAFS.
* **Đóng góp của Con người:** 
  * Xác định PIT không phải là một bước tiền xử lý đơn lẻ mà là **Control Plane xuyên suốt**.
  * Thiết lập triết lý tài chính: *Outlier Detection $\ne$ Outlier Removal* (bảo tồn các cú sốc COVID 2020, khủng hoảng giá dầu).
  * Tách biệt rạch ròi Data Transformation vs Feature Engineering.
* **Hỗ trợ của AI:** Ánh xạ 15 hạng mục vào 6 Layer kiến trúc, xây dựng toàn bộ package `src/data_proccessing/` gồm 10 module độc lập chạy theo mô hình pipeline chuyên nghiệp.

### Phiên 5: Thẩm Tra Độc Lập Nguồn Gốc Số Liệu (Zero-Hallucination Audit)
* **Bối cảnh:** Nghiên cứu viên yêu cầu xóa toàn bộ mã nguồn cũ để giữ dữ liệu sạch, sau đó chất vấn: *"Vậy từ đâu bạn có kết quả như vậy?"*
* **Đóng góp của Con người:** Thực hiện kiểm tra chéo (Cross-examination) nghiêm ngặt để đảm bảo các con số $F=0.0031, p=0.9552, R^2=31.22\%$ là thật.
* **Hỗ trợ của AI:** Trích xuất chi tiết công thức toán, chỉ ra đường dẫn file thực tế `stream1_econometric_2008_2025.csv`, và cung cấp đoạn mã Python 5 dòng để nghiên cứu viên tự tay chạy kiểm chứng lại trên máy.

### Phiên 6: Di Chuyển Repository & Xử Lý Sự Cố Hiển Thị README
* **Bối cảnh:** Chuyển sang repository chính thức `https://github.com/LeNam123456/petro95_workflow_team.git`, nhưng ảnh chụp màn hình cho thấy README bị dính liền thành một khối chữ thô.
* **Đóng góp của Con người:** Cung cấp ảnh chụp màn hình lỗi và yêu cầu điều chỉnh lại README tương xứng kèm giải thích lý do.
* **Hỗ trợ của AI:**
  * Dùng Python phân tích nhị phân và phát hiện **25 byte null (`\x00`)** ở cuối file do PowerShell ghi UTF-16 đè vào UTF-8.
  * Viết lại `README.md` theo chuẩn UTF-8 thuần, tối ưu hóa giao diện GitHub Flavored Markdown và đẩy thành công lên nhánh `main` qua SSH.

---

## 4. KIỂM SOÁT ẢO GIÁC & CƠ CHẾ KIỂM CHỨNG KHOA HỌC (VERIFICATION & RIGOR)

Nhằm đảm bảo nghiên cứu không bị ảnh hưởng bởi hiện tượng ảo giác (AI Hallucination):

1. **Nguyên Tắc "Không Tin Tưởng Mù Quáng" (Trust but Verify):**
   Mọi ước lượng thống kê do AI đề xuất đều được kiểm chứng lại bằng việc thực thi trực tiếp trên terminal với các thư viện định lượng tiêu chuẩn quốc tế: `statsmodels 0.15.0`, `lightgbm 4.7.0`, `scipy 1.17.1`, `pandas 3.0.5`.
2. **Kiểm Toán Dấu Vết (Audit Trail Verification):**
   Mỗi bước tiền xử lý đều sinh ra cặp tệp báo cáo song hành:
   * File dữ liệu sạch dạng nén: Apache Parquet (bảo toàn 100% schema và timestamp).
   * File kiểm toán chi tiết: JSON (chứa thông tin máy, số dòng, trạng thái kiểm tra).
   * File bảng tổng kết: CSV (phục vụ trích xuất vào phụ lục bài báo khoa học).
3. **Bảo Tồn Tính Bất Biến Của Dữ Liệu Gốc (Data Immutability):**
   Tập dữ liệu thô trong `data/raw/` được khóa quyền ghi, mọi biến đổi chỉ được phép ghi vào `data/interim/` và `data/processed/`.

---

## 5. CÁC QUYẾT ĐỊNH PHƯƠNG PHÁP LUẬN QUAN TRỌNG DO CON NGƯỜI CHỈ ĐẠO

Trong Đợt 1, Nghiên cứu viên đã đưa ra **6 quyết định phương pháp luận mang tính then chốt**, định hình toàn bộ hướng đi của đề tài:

1. **Loại bỏ Tỷ giá USD/SGD khỏi Core Model:** Cả 4 chuỗi Platts và chuỗi dầu thô Brent đều giao dịch bằng USD/bbl. Việc không đưa tỷ giá vào Core Model giúp đề tài tập trung trọn vẹn vào cơ chế kinh tế lọc dầu mà không bị nhiễu bởi chính sách tiền tệ của MAS.
2. **Loại bỏ Cointegration / ECM:** Nhận định chính xác rằng khi biến phụ thuộc là Return $r_{t+1}$ (chuỗi dừng $I(0)$), mô hình ECM không còn phù hợp về mặt lý thuyết. Thay vào đó, đưa biến trễ $(MG95 - Brent)_{t-1}$ làm mỏ neo cân bằng dài hạn (Mean-Reversion term).
3. **Bắt buộc dùng Clark & West (2007) cho RQ2:** Nhận diện việc $M6$ lồng trong $M5$ khiến kiểm định Diebold-Mariano truyền thống bị lệch âm do nhiễu tham số dư thừa.
4. **Phân tách Độc lập 2 Mẫu Nghiên Cứu:** Bảo vệ tính khách quan của kiểm định tin tức RQ2 bằng cách chỉ so sánh $M5$ vs $M6$ trên giai đoạn 2017–2025.
5. **Cấm Tự Động Xóa Outlier:** Giữ nguyên các cú sốc biến động cực đoan của thị trường dầu mỏ trong đại dịch COVID-19 (tháng 03–04/2020) để kiểm định tính chống chịu của mô hình.
6. **Kiểm Soát Độ Phức Tạp Của Cây Quyết Định (Parsimony Freeze):** Cố định độ sâu cây nông `max_depth = 3`, `num_leaves = 7` cho LightGBM, cấm sử dụng các mô hình Deep Learning quá phức tạp (PatchTST, LSTM) để tránh hiện tượng học vẹt trên dữ liệu bảng tài chính.

---

## 6. TỔNG KẾT ARTIFACTS ĐỢT 1 & CAM KẾT LIÊM CHÍNH

### 6.1. Danh mục sản phẩm bàn giao Đợt 1
* **Mã nguồn hoàn chỉnh:** Package `src/data_proccessing/` (10 module) điều phối pipeline 8 bước chuẩn doanh nghiệp.
* **Bộ dữ liệu sạch có phiên bản:**
  * `canonical_market_panel.parquet` (Bảng điều khiển PIT 5 mốc thời gian).
  * `stream1_econometric_2008_2025.parquet` ($N = 4,428$ ngày giao dịch đồng bộ).
  * `stream2_aligned_nlp_2017_2025.parquet` ($N = 2,255$ ngày giao dịch đối chứng).
  * `weekly_price_robustness.parquet` ($N = 922$ tuần kiểm tra độ bền vững).
* **Hồ sơ kiểm toán chất lượng:** 12 file JSON & CSV tại `reports/data_quality/` đạt 100% Gate 1.1 $\to$ Gate 1.3.
* **Tài liệu phương pháp luận:** [`SPAFS_V5_2_BLUEPRINT_AND_SYSTEM_SPECIFICATION.md`](file:///D:/Petro_95/SPAFS_V5_2_BLUEPRINT_AND_SYSTEM_SPECIFICATION.md) và [`README.md`](file:///D:/Petro_95/README.md).
* **Kho lưu trữ đồng bộ:** Đã đẩy toàn bộ lên GitHub tại `https://github.com/LeNam123456/petro95_workflow_team.git` (nhánh `main`).

### 6.2. Cam kết liêm chính học thuật (Declaration of Academic Integrity)
> *"Tôi cam kết rằng báo cáo AI Audit Log này phản ánh trung thực 100% quá trình sử dụng công cụ AI trong Đợt 1 của đề tài. Trí tuệ Nhân tạo chỉ đóng vai trò là một trợ lý kỹ thuật hỗ trợ viết mã và định dạng tài liệu dưới sự định hướng, giám sát, thẩm định và chỉ đạo phương pháp luận hoàn toàn độc lập của tôi. Tôi chịu trách nhiệm học thuật cao nhất và tuyệt đối về tính chính xác của toàn bộ dữ liệu, mô hình và kết luận được trình bày trong đề tài này."*

**Nghiên cứu viên thực hiện:**  
*Lê Nam*  
*Repository:* [LeNam123456/petro95_workflow_team](https://github.com/LeNam123456/petro95_workflow_team)
