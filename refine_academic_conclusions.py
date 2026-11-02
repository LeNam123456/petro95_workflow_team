# -*- coding: utf-8 -*-
"""Refine academic conclusions, tone down over-claims, distinguish M4/M5 trade-offs, and synchronize deliverables."""

import re
import json
import shutil
from pathlib import Path

# Load reports
rep_path = Path("reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md")
rep_text = rep_path.read_text(encoding="utf-8")

# 1. Refine RQ1 Conclusion block in Section 4.1
old_rq1_box = """> [!IMPORTANT]
> **KẾT LUẬN HỌC THUẬT ĐỘT PHÁ (RQ1):** Bằng chứng thực nghiệm Newey-West HAC trên chuỗi dữ liệu 17.5 năm khẳng định **hiện tượng "Tên lửa và Lông vũ" hoàn toàn KHÔNG tồn tại tại sàn bán buôn Platts FOB Singapore**. Thị trường đầu mối quốc tế vận hành theo đúng cơ chế cạnh tranh hoàn hảo (Bacon, 1991): giá xăng bán buôn phản ứng sòng phẳng, cân bằng và đối xứng 100% trước cả cú sốc tăng lẫn cú sốc giảm của giá dầu thô Brent."""

new_rq1_box = """> [!IMPORTANT]
> **KẾT LUẬN HỌC THUẬT VỀ TRUYỀN DẪN GIÁ (RQ1):** Các kiểm định thực nghiệm Newey-West HAC hiện tại trên chuỗi dữ liệu 17.5 năm ($N = 4,425$ phiên hiệu dụng) **chưa cung cấp đủ bằng chứng thống kê để kết luận có sự bất đối xứng trong truyền dẫn giá từ dầu thô Brent sang giá xăng Mogas 95 tại sàn Platts FOB Singapore theo đặc tả nghiên cứu** ($W_F = 0.0035, p = 0.9530$ cho phản ứng tức thời; $W_F = 0.2240, p = 0.6360$ cho phản ứng tích lũy 2 ngày; và $\\chi^2 = 0.4962, p = 0.8833$ cho kiểm định ràng buộc chung). Về mặt kinh tế lượng, việc không thể bác bỏ giả thuyết vô hiệu $H_0$ đồng nghĩa với việc mô hình đối xứng vẫn là mô hình phù hợp và tối ưu hơn về mặt tiết kiệm tham số (parsimony)."""

if old_rq1_box in rep_text:
    rep_text = rep_text.replace(old_rq1_box, new_rq1_box)
else:
    # Regex fallback
    rep_text = re.sub(
        r'> \[!IMPORTANT\]\s*\n>\s*\*\*KẾT LUẬN HỌC THUẬT.*?của giá dầu thô Brent\.',
        new_rq1_box,
        rep_text,
        flags=re.DOTALL
    )

# 2. Refine RQ2 Conclusion block and M4 vs M5 nuance
old_rq2_box = """> [!TIP]
> **KẾT LUẬN HỌC THUẬT QUAN TRỌNG (RQ2):** Giả thuyết vô hiệu $H_0$ bị **bác bỏ dứt khoát ở mức ý nghĩa 5%**. Kết quả chứng minh rằng việc bổ sung các biến kinh tế lọc dầu hạ nguồn (Crack Spread, Phí Octane và Chênh lệch Xăng-Diesel) mang lại năng lực dự báo vượt trội có ý nghĩa thống kê thực chất so với việc chỉ dựa vào các chỉ báo kỹ thuật động lượng thuần túy."""

new_rq2_box = """> [!TIP]
> **KẾT LUẬN THỐNG KÊ VỀ ĐẶC TRƯNG LỌC DẦU (RQ2) VÀ SO SÁNH ĐA TIÊU CHÍ GIỮA M4 VÀ M5:**  
> 1. **Về sai số độ lớn:** Mô hình M5 (tích hợp các biến kinh tế lọc dầu hạ nguồn) đạt sai số thấp hơn M4 cả về RMSE ($1.4163\\%$ so với $1.4221\\%$) và MAE ($1.0643\\%$ so với $1.0712\\%$). Kiểm định lồng ghép hiệu chỉnh Clark & West (2007) đạt thống kê $CW = +1.9688$ với $p = 0.0245 < 0.05$, **bác bỏ giả thuyết vô hiệu $H_0$ ở mức ý nghĩa 5%** và xác nhận việc bổ sung các biến biên lọc dầu cải thiện MSPE ngoài mẫu của quần thể.  
> 2. **Về khả năng định hướng:** Mô hình kỹ thuật M4 lại nhỉnh hơn một chút về độ chính xác định hướng ($\\text{DA} = 70.82\\%$ so với $70.42\\%$ của M5) và hệ số tương quan Matthews ($\\text{MCC} = 0.4156$ so với $0.4078$).  
> 3. **Nhận định khoa học:** **Không kết luận M5 vượt trội hoàn toàn trên mọi tiêu chí**. Sự đánh đổi này phản ánh mục tiêu thực tiễn: M5 phù hợp hơn khi nhà giao dịch ưu tiên thu hẹp biên độ tổn thất tuyệt đối (loss magnitude), trong khi M4 phù hợp hơn khi ưu tiên tỷ lệ đoán đúng chiều hướng dao động (directional hit-rate)."""

if old_rq2_box in rep_text:
    rep_text = rep_text.replace(old_rq2_box, new_rq2_box)
else:
    rep_text = re.sub(
        r'> \[!TIP\]\s*\n>\s*\*\*KẾT LUẬN HỌC THUẬT QUAN TRỌNG \(RQ2\):.*?thuần túy\.',
        new_rq2_box,
        rep_text,
        flags=re.DOTALL
    )

# 3. Refine Section 4.3 (PIT Audit text) to explicitly state proxy nature and avoid absolute claims
old_pit_statement = """- **Tổng số vi phạm rò rỉ dữ liệu (Lookahead Violations):** **0 bản ghi (0.00%)**."""
new_pit_statement = """- **Tổng số vi phạm quy tắc thời gian nội nhật:** **0 bản ghi (0.00%)** trên 2,255 phiên.
> [!WARNING]
> **GIỚI HẠN KIỂM TOÁN POINT-IN-TIME (PIT AUDIT CAVEAT):**  
> Quá trình kiểm toán xác nhận 100% các điều kiện thời gian nội nhật phù hợp với logic kinh doanh dựa trên **timestamp proxy quy chuẩn theo giờ thị trường** (16:30 SGT Platts close, 03:30 SGT ICE Brent settlement, 08:30 SGT forecast cutoff). Nghiên cứu **không tuyên bố đã chứng minh hoàn toàn không có lookahead bias ở cấp độ thực tế**, do dữ liệu lịch sử cuối ngày (EOD) không lưu trữ log tick nhận dữ liệu thời gian thực từ máy chủ phân phối feed."""

if old_pit_statement in rep_text:
    rep_text = rep_text.replace(old_pit_statement, new_pit_statement)

# 4. Refine Section 5.2 (Ba đóng góp học thuật và thực tiễn cốt lõi)
old_contrib_1 = """1. **Đóng góp 1 (Về mặt Kinh tế lượng vi mô):** Cung cấp bằng chứng thực nghiệm vững chắc trên chuỗi 17.5 năm dữ liệu bác bỏ giả thuyết "Tên lửa và Lông vũ" tại thị trường đầu mối bán buôn Platts Singapore. Giá bán buôn phản ứng hoàn toàn đối xứng ($p = 0.9530$), chứng minh tính phân hóa sâu sắc giữa thị trường bán buôn quốc tế và thị trường bán lẻ nội địa."""
new_contrib_1 = """1. **Đóng góp 1 (Về mặt Kinh tế lượng vi mô):** Cung cấp bằng chứng thực nghiệm có kiểm soát trên chuỗi 17.5 năm dữ liệu ($N = 4,425$ phiên hiệu dụng) cho thấy các kiểm định hiện tại chưa cung cấp đủ bằng chứng thống kê để kết luận có sự bất đối xứng trong truyền dẫn giá ($p = 0.9530$ cho phản ứng tức thời và $p = 0.6344$ ngoài mẫu). Kết quả này cho thấy mô hình đối xứng chuẩn vẫn là đặc tả đại diện phù hợp tại thị trường bán buôn hàng rời quốc tế."""

old_contrib_2 = """2. **Đóng góp 2 (Về mặt Học máy & Kinh tế lọc dầu):** Chứng minh bằng kiểm định lồng ghép Clark & West (2007) ($p = 0.0245 < 0.05$) rằng các biến biên lọc dầu hạ nguồn (Crack Spread, Octane Premium, Gasoil Substitution) đóng góp năng lực dự báo vượt trội thực sự so với các chỉ báo kỹ thuật đơn thuần, kéo giảm RMSE ngoài mẫu xuống mức kỷ lục $1.4163\%$/ngày."""
new_contrib_2 = """2. **Đóng góp 2 (Về mặt Học máy & Kinh tế lọc dầu):** Làm rõ sự đánh đổi đa mục tiêu giữa mô hình kỹ thuật M4 và mô hình kinh tế M5. Bổ sung các biến cấu trúc biên lọc dầu hạ nguồn (Gasoline Crack Spread, Octane Premium, Diesel Margin) trong M5 giúp cải thiện có ý nghĩa thống kê về sai số MSPE ngoài mẫu theo kiểm định lồng ghép Clark & West (2007) ($CW = +1.9688, p = 0.0245 < 0.05$), đưa RMSE xuống $1.4163\\%$, trong khi mô hình kỹ thuật M4 duy trì ưu thế nhẹ về độ chính xác định hướng ($\\text{DA} = 70.82\\%$) và hệ số tương quan Matthews ($\\text{MCC} = 0.4156$)."""

if old_contrib_1 in rep_text:
    rep_text = rep_text.replace(old_contrib_1, new_contrib_1)
if old_contrib_2 in rep_text:
    rep_text = rep_text.replace(old_contrib_2, new_contrib_2)

# Save updated academic report
rep_path.write_text(rep_text, encoding="utf-8")
art_path = Path("C:/Users/LeeNam/.gemini/antigravity/brain/c95a4cf9-b685-49db-8f18-df5994910785/SPAFS_V5_2_BAO_CAO_HOAN_CHINH.md")
if art_path.parent.exists():
    art_path.write_text(rep_text, encoding="utf-8")

print("Updated SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md with exact academic caveats.")

# 5. Create authoritative README for instructor audit
readme_content = """# HƯỚNG DẪN KIỂM TRA, ĐỐI CHIẾU VÀ TÁI LẬP KẾT QUẢ NGHIÊN CỨU
## DỰ ÁN DỰ BÁO LỢI SUẤT XĂNG PLATS FOB SINGAPORE (SPAFS V5.2)
### TÀI LIỆU PHỤC VỤ HỘI ĐỒNG BẢO VỆ VÀ PHẢN BIỆN KHOA HỌC

Tài liệu này cung cấp hướng dẫn đầy đủ để giảng viên/người phản biện kiểm chứng độc lập toàn bộ các kết quả thực nghiệm được trình bày trong Báo cáo khoa học SPAFS V5.2.

---

## 1. BẢNG TỔNG HỢP KẾT QUẢ HIỆN CÓ TRÊN 754 PHIÊN OOS CHUNG

Được tính trên tập mẫu ngoài mẫu chung thống nhất (**Common Overlapping Window** từ **28/12/2022 đến 29/12/2025**, $N_{OOS} = 754$ phiên giao dịch):

| Chỉ số đánh giá | M4 (Technical LightGBM) | M5 (Economic LightGBM) | Mô hình đạt ưu thế | Ý nghĩa thống kê & Nhận định thực nghiệm |
| :--- | :---: | :---: | :---: | :--- |
| **Sai số bình phương (RMSE)** | **1.4221%** | **1.4163%** | **M5 tốt hơn** | M5 giảm 0.0058 điểm % sai số độ lớn |
| **Sai số tuyệt đối (MAE)** | **1.0712%** | **1.0643%** | **M5 tốt hơn** | M5 giảm 0.0069 điểm % sai số tuyệt đối |
| **Độ chính xác định hướng (DA)** | **70.82%** | **70.42%** | **M4 tốt hơn** | M4 nhỉnh hơn 0.40 điểm % về tỷ lệ bắt trúng hướng |
| **Hệ số Matthews (MCC)** | **0.4156** | **0.4078** | **M4 tốt hơn** | M4 nhỉnh hơn 0.0078 về tương quan phân loại nhị phân |
| **Pesaran-Timmermann stat** | **+11.4202** ($p < 10^{-28}$) | **+11.2063** ($p < 10^{-28}$) | **Cả hai mô hình** | Vượt trội ngẫu nhiên ở mức ý nghĩa cao nhất ($p < 0.01$) |

> [!IMPORTANT]
> **QUY TẮC KẾT LUẬN KHOA HỌC:**  
> **Không kết luận M5 tốt nhất trên mọi tiêu chí.**  
> - M5 vượt trội hơn về các chỉ tiêu sai số biên độ (RMSE, MAE) và có ý nghĩa thống kê theo kiểm định Clark & West (2007) ($p = 0.0245$).  
> - M4 lại nhỉnh hơn về các chỉ tiêu định hướng phân loại (DA, MCC).  
> Sự lựa chọn mô hình tùy thuộc vào mục tiêu quản trị rủi ro: ưu tiên kiểm soát độ lệch giá tuyệt đối (chọn M5) hay ưu tiên dự báo đúng chiều hướng biến động để định thời hợp đồng (chọn M4).

---

## 2. BẢNG PHÂN LOẠI TRẠNG THÁI TÁI LẬP CỦA CÁC KẾT QUẢ

| Hạng mục kiểm định | Tập mẫu áp dụng | Kết quả ghi nhận | Trạng thái xác minh | Tệp dữ liệu / Kịch bản đối chiếu |
| :--- | :---: | :---: | :---: | :--- |
| **Hiệu năng M4 & M5** | OOS $N=754$ | RMSE 1.4221 vs 1.4163; DA 70.82% vs 70.42% | **ĐÃ TÁI LẬP 100% TỪ CSV** | `out_of_sample_predictions_all_7_models_harmonized_754.csv` |
| **Clark-West (M5 vs M4)** | OOS $N=754$ | $CW = +1.9688, p = 0.0245$ (Bác bỏ $H_0$ ở 5%) | **ĐÃ TÁI LẬP 100% TỪ CSV** | `run_reproducible_clark_west_dm.py` |
| **DM Squared Loss (M5 vs M4)**| OOS $N=754$ | $DM = -0.7748, p = 0.2194$ (Không bác bỏ 5%) | **ĐÃ TÁI LẬP 100% TỪ CSV** | `run_reproducible_clark_west_dm.py` |
| **DM Absolute Loss (M5 vs M4)**| OOS $N=754$ | $DM = -1.3088, p = 0.0955$ (Bác bỏ ở biên 10%)| **ĐÃ TÁI LẬP 100% TỪ CSV** | `run_reproducible_clark_west_dm.py` |
| **Clark-West (M3 vs M2)** | OOS $N=754$ | $CW = -0.3436, p = 0.6344$ (Không bác bỏ $H_0$)| **ĐÃ TÁI LẬP 100% TỪ CSV** | `run_reproducible_clark_west_dm.py` |
| **Hiệu năng 7 Mô hình** | OOS $N=754$ | M0a, M0b, M1, M2, M3, M4, M5 | **ĐÃ TÁI LẬP 100% TỪ CSV** | `out_of_sample_predictions_all_7_models_harmonized_754.csv` |
| **Wald Tests RQ1** | Toàn mẫu $N=4,425$ | $W_F = 0.0035 (p=0.9530); W_F = 0.2240 (p=0.6360)$ | **ĐÃ XÁC MINH TỪ SCRIPT M3** | `01_run_m3_asymmetric_adl_and_wald_test.py` |
| **Stream 1 OOS riêng** | OOS $N=925$ | M0a đến M3 (2022-04-22 đến 2025-12-29) | **ĐÃ XÁC MINH TỪ FILE RUNNER**| `out_of_sample_predictions_stream1_925.csv` |
| **Mô hình M6 (Multimodal News)**| Stream 2 | Chưa tích hợp vào hệ thống chính thức | **KẾ HOẠCH MỞ RỘNG TƯƠNG LAI**| Không nằm trong gói thực nghiệm V5.2 |

---

## 3. LỆNH 1-DÒNG ĐỂ TÁI LẬP TOÀN BỘ BẢNG KẾT QUẢ

Giảng viên hoặc người phản biện chỉ cần mở terminal tại thư mục chứa gói giải nén và chạy lệnh:

```bash
python 04_m4_m5_machine_learning_scripts/run_reproducible_clark_west_dm.py --csv 04_m4_m5_machine_learning_scripts/out_of_sample_predictions_all_7_models_harmonized_754.csv
```

Kịch bản sẽ:
1. Đọc trực tiếp 754 dòng dữ liệu dự báo thực tế.
2. Tính toán lại từ đầu toàn bộ RMSE, MAE, DA, MCC, PT-stat cho 7 mô hình.
3. Chạy lại kiểm định Clark & West (2007) và Diebold & Mariano (HLN 1997).
4. Tái tạo tệp JSON kết quả `reproducible_statistical_tests.json` mà không sử dụng bất kỳ số liệu lưu sẵn nào.

---

## 4. BỐI CẢNH VÀ LÝ GIẢI KHOA HỌC CHO CÁC CÂU HỎI THƯỜNG GẶP CỦA HỘI ĐỒNG

### Câu hỏi 1: Vì sao Clark–West có ý nghĩa 5% ($p=0.0245$) nhưng Diebold–Mariano Squared Loss lại không có ý nghĩa ($p=0.2194$)?
* **Trả lời:** M4 ($K=10$) lồng ghép hoàn toàn trong M5 ($K=15$). Dưới giả thuyết vô hiệu $H_0$ (5 biến kinh tế không có giá trị dự báo), M5 vẫn phải ước lượng thêm 5 tham số. Quá trình ước lượng này tạo ra **nhiễu ước lượng tham số (parameter estimation noise)** làm tăng phương sai ngoài mẫu của M5 lên một lượng xấp xỉ $+0.02624$.
* Kiểm định Diebold–Mariano tiêu chuẩn **bỏ qua số hạng bù nhiễu này**, dẫn đến thống kê DM bị **chệch âm nghiêm trọng (severely undersized)** và ưu ái quá mức cho mô hình nhỏ M4.
* Kiểm định Clark & West (2007) đưa vào số hạng hiệu chỉnh $(\\hat{y}_{M4} - \\hat{y}_{M5})^2$ để triệt tiêu nhiễu, phục hồi phân phối chuẩn và khẳng định M5 thực sự cải thiện chất lượng dự báo ngoài mẫu có ý nghĩa thống kê ($CW = +1.9688, p = 0.0245 < 0.05$).

### Câu hỏi 2: Có phải tỷ lệ đoán đúng hướng ~70% chứng minh cơ chế kinh tế vi mô độc quyền hay thông đồng giá?
* **Trả lời:** **Hoàn toàn không.** Tỷ lệ $\\text{DA} \\approx 70.4\\% - 70.8\\%$ là hệ quả thống kê của **sự căn chỉnh thông tin qua múi giờ (Timezone Information Alignment)**: sàn London ICE Brent đóng cửa lúc 03:30 SGT trước mốc Cutoff 08:30 SGT, cung cấp tín hiệu chi phí gốc rất mạnh cho phiên chiều 16:30 SGT của Platts Singapore.
* Con số này chứng minh **sự lan tỏa thông tin có hiệu lực cao qua múi giờ (Timezone Information Spillover)**. Bằng chứng kinh tế thực chất nằm ở việc các biến biên lọc dầu trong M5 vượt qua kiểm định Clark–West ($p = 0.0245$) khi đối đầu với mô hình kỹ thuật M4.

### Câu hỏi 3: Điểm chốt chặn Warm-up Stream 1 ngày 21/04/2022 có ý nghĩa gì?
* **Trả lời:** Chuỗi Stream 1 ($N=4,425$ phiên) áp dụng cửa sổ khởi động $\\tau_0 = 3,500$ phiên. Phiên quan sát thứ $3,500$ diễn ra đúng vào **ngày 21/04/2022**, đóng vai trò là **phiên cuối cùng của tập Train khởi đầu (In-sample Warm-up Cutoff)**. Quá trình kiểm định ngoài mẫu OOS bắt đầu từ **phiên quan sát thứ 3,501, tức ngày 22/04/2022** ($N_{OOS}^{(1)} = 925$ phiên). Ngày 21/04/2022 nằm trọn vẹn trong tập huấn luyện ban đầu, không hề bị mất mát dữ liệu.

### Câu hỏi 4: Nghiên cứu có tuyên bố đã chứng minh hoàn toàn không có lookahead bias không?
* **Trả lời:** **Không.** Nghiên cứu xác nhận 100% các quy tắc thời gian nội nhật tuân thủ logic kinh doanh dựa trên **timestamp proxy quy chuẩn theo giờ thị trường** (16:30 SGT Platts close, 03:30 SGT ICE Brent settlement, 08:30 SGT forecast cutoff). Do dữ liệu lịch sử EOD không lưu log tick thời gian thực từ máy chủ phân phối feed, nghiên cứu thẳng thắn ghi nhận đây là một giới hạn phương pháp luận và không tuyên bố đã xác minh tick-level arrival timestamps.
"""

Path("SPAFS_DELIVERABLES_PACKAGE/README_HUONG_DAN_KIEM_TRA_VA_TAI_LAP.md").write_text(readme_content, encoding="utf-8")
Path("C:/Users/LeeNam/Downloads/README_HUONG_DAN_KIEM_TRA_VA_TAI_LAP.md").write_text(readme_content, encoding="utf-8")
print("Exported README_HUONG_DAN_KIEM_TRA_VA_TAI_LAP.md to deliverables package and Downloads.")
