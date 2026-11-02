# -*- coding: utf-8 -*-
"""Update Markdown academic reports, log files, and regenerate Word docx with full academic caveats."""

import re
import json
import shutil
from pathlib import Path

# Paths
md_workspace = Path("reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md")
md_artifact = Path("C:/Users/LeeNam/.gemini/antigravity/brain/c95a4cf9-b685-49db-8f18-df5994910785/SPAFS_V5_2_BAO_CAO_HOAN_CHINH.md")

content = md_workspace.read_text(encoding="utf-8")

# 1. Update PT-stats in Table 4.2: 11.2737 -> 11.4202 and 11.1743 -> 11.2063
content = content.replace("11.2737", "11.4202")
content = content.replace("11.1743", "11.2063")

# 2. Add OOS consistency table & 2022-04-21 explanation in Section 4.2
oos_consistency_block = """#### Bảng 4.4: Bảng Kiểm toán Tính nhất quán của Tập Mẫu Ngoài mẫu (OOS Consistency & Cross-Stream Alignment)

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
> **LÀM RÕ KHOA HỌC VỀ NGÀY 21/04/2022 TẠI STREAM 1:**  
> Chuỗi dữ liệu kinh tế lượng Stream 1 ($N=4,425$ phiên hiệu dụng) áp dụng cửa sổ khởi động huấn luyện $\\tau_0 = 3,500$ phiên. Phiên quan sát thứ $3,500$ diễn ra đúng vào **ngày 21/04/2022**, đóng vai trò là **phiên chốt chặn cuối cùng của tập Train trong mẫu (In-sample Warm-up Cutoff)**. Do đó, quá trình kiểm định ngoài mẫu OOS bắt đầu một cách nghiêm ngặt từ **phiên quan sát thứ 3,501, tức ngày 22/04/2022** ($N_{OOS}^{(1)} = 925$ phiên). Ngày 21/04/2022 hoàn toàn không bị mất mát hay loại trừ bất thường mà thuộc trọn vẹn vào tập huấn luyện khởi đầu."""

if "#### Bảng 4.4: Bảng Kiểm toán Tính nhất quán" not in content:
    content = content.replace("### 4.3. Xác minh Điểm chốt Thời gian", oos_consistency_block + "\n\n### 4.3. Xác minh Điểm chốt Thời gian")

# 3. Update Section 4.4 (Pairwise Tests) with exact hypotheses, one-sided/two-sided rules, and Clark-West vs DM explanation
pw_explanation = """### 4.4. Kiểm định Cặp đôi Tái lập: Giả thuyết Thống kê và So sánh Chuyên sâu Clark–West vs Diebold–Mariano

Toàn bộ các phép kiểm định cặp đôi ngoài mẫu được thực thi độc lập và có thể tái lập từ tệp dự báo `out_of_sample_predictions_all_7_models_harmonized_754.csv` qua kịch bản `run_reproducible_clark_west_dm.py`.

#### 1. Bảng quy chuẩn Giả thuyết không ($H_0$), Mức ý nghĩa ($\alpha$) và Quy ước Kiểm định

| Phép kiểm định | Cặp mô hình | Giả thuyết không ($H_0$) | Giả thuyết đối ($H_1$) | Quy ước đuôi kiểm định | Mức ý nghĩa $\alpha$ | Thống kê tính toán | Giá trị $p$-value | Kết luận thống kê |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Clark & West (2007)** | M5 vs M4 | $\\text{MSPE}_{M4} \\le \\text{MSPE}_{M5} - \\text{adj}$ (Biến lọc dầu không giảm MSPE) | $\\bar{f} > 0$ (M5 có MSPE hiệu chỉnh thấp hơn) | **Một phía (One-sided)** | 5% | $\\mathbf{CW = +1.9688}$ | $\\mathbf{p = 0.0245}$ | **Bác bỏ $H_0$ ở mức 5%** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (Hàm mất mát bình phương MSE bằng nhau) | $E[d_t] < 0$ (M5 có MSE nhỏ hơn M4) | **Một phía (One-sided)** | 5% | $DM = -0.7748$ | $p = 0.2194$ | **Không thể bác bỏ $H_0$** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (Hàm mất mát bình phương MSE bằng nhau) | $E[d_t] \\ne 0$ (Hai mô hình có MSE khác nhau) | **Hai phía (Two-sided)** | 5% | $DM = -0.7748$ | $p = 0.4387$ | **Không thể bác bỏ $H_0$** |
| **Diebold-Mariano (HLN)**| M5 vs M4 | $E[d_t] = 0$ (Hàm mất mát tuyệt đối MAE bằng nhau) | $E[d_t] < 0$ (M5 có MAE nhỏ hơn M4) | **Một phía (One-sided)** | 10% | $DM = -1.3088$ | $p = 0.0955$ | **Bác bỏ $H_0$ ở mức 10%** |
| **Clark & West (2007)** | M3 vs M2 | $\\text{MSPE}_{M2} \\le \\text{MSPE}_{M3} - \\text{adj}$ (Bất đối xứng không giảm MSPE) | $\\bar{f} > 0$ (M3 có MSPE hiệu chỉnh thấp hơn) | **Một phía (One-sided)** | 5% | $CW = -0.3436$ | $p = 0.6344$ | **Không thể bác bỏ $H_0$** |
| **Pesaran-Timmermann**  | M5 | Hướng đi thực tế và hướng dự báo độc lập ngẫu nhiên | Tỷ lệ đoán đúng vượt trội kỳ vọng biên | **Một phía (One-sided)** | 1% | $PT = +11.2063$ | $p < 10^{-28}$ | **Bác bỏ $H_0$ ở mức 1%** |

#### 2. Giải thích vì sao Clark–West có ý nghĩa 5% ($p = 0.0245$) nhưng Diebold–Mariano Squared Loss không có ý nghĩa ($p = 0.2194$)?
Đây là một kết quả kinh điển trong kinh tế lượng tài chính đã được làm rõ bởi **Clark & West (2007, *Journal of Econometrics*)** và **McCracken (2007)**:
- Mô hình M4 ($K=10$ biến) là mô hình con lồng ghép hoàn toàn trong mô hình M5 ($K=15$ biến).
- Dưới giả thuyết vô hiệu $H_0$ rằng 5 biến kinh tế lọc dầu hạ nguồn không có năng lực dự báo, mô hình lớn M5 vẫn phải ước lượng thêm các tham số tương ứng trong quá trình Walk-forward. Việc ước lượng này tạo ra **nhiễu ước lượng tham số (parameter estimation noise)**, làm phương sai sai số ngoài mẫu của mô hình lớn bị đội lên một lượng xấp xỉ $\\frac{1}{P} \\sum (\\hat{y}_{M4} - \\hat{y}_{M5})^2 = +0.02624$.
- Kiểm định Diebold–Mariano tiêu chuẩn **hoàn toàn bỏ qua số hạng bù nhiễu này**, dẫn đến thống kê DM bị **chệch âm nghiêm trọng (severely undersized)** và ưu ái quá mức cho mô hình nhỏ M4.
- Kiểm định Clark & West (2007) đưa vào số hạng hiệu chỉnh chính xác:
  $$\\hat{f}_{t+1} = e_{M4, t+1}^2 - \\left[ e_{M5, t+1}^2 - (\\hat{y}_{M4, t+1} - \\hat{y}_{M5, t+1})^2 \\right] = 2 e_{M4, t+1} (\\hat{y}_{M5, t+1} - \\hat{y}_{M4, t+1})$$
  Số hạng hiệu chỉnh phục hồi phân phối tiệm cận chuẩn, đem lại năng lực kiểm định chính xác và cho thấy M5 thực sự cải thiện chất lượng dự báo ngoài mẫu có ý nghĩa thống kê ($CW = +1.9688, p = 0.0245 < 0.05$)."""

# Replace Section 4.4 in content
pattern_pw = r"### 4\.4\. Kiểm định Cặp đôi Tái lập[\s\S]*?mức ý nghĩa biên 10%\)\."
match_pw = re.search(pattern_pw, content)
if match_pw:
    content = content[:match_pw.start()] + pw_explanation + content[match_pw.end():]

# 4. Clarify Section 4.5: Directional Accuracy is NOT direct economic proof
da_clarification = """### 4.5. Cơ chế Lan tỏa Thông tin qua Múi giờ và Giới hạn Diễn giải Kinh tế

#### 1. Bản chất thống kê của Tỷ lệ đoán đúng chiều hướng ~70% (Timezone Information Spillover):
Cần đặc biệt nhấn mạnh rằng con số **$\\text{DA} \\approx 70.4\\% - 70.8\\%$ KHÔNG phải là bằng chứng trực tiếp chứng minh cho bất kỳ cơ chế kinh tế vi mô nội sinh nào**. Về mặt bản chất thống kê, đây là kết quả của **sự lan tỏa thông tin do chênh lệch múi giờ giao dịch liên lục địa (Cross-Timezone Information Alignment)**:

```
[16:30 SGT ngày t] ────────► [03:30 SGT sáng t+1] ───────► [08:30 SGT sáng t+1] ──────► [16:30 SGT chiều t+1]
 Singapore đóng phiên         London chốt sàn Brent         Mốc Cutoff đóng băng          Singapore chốt phiên mới
  (Chốt giá ngày cũ)           (London có tin chấn động!)   (Mô hình đọc sốc Brent đêm)   (Cái cần dự báo)
```

1. Phiên giao dịch Platts FOB Singapore ngày $t$ khép lại lúc 16:30 SGT.
2. Sàn ICE Brent London tiếp tục giao dịch theo múi giờ Châu Âu và Bắc Mỹ, thanh toán vào 19:30 giờ London (tương đương 03:30 SGT sáng hôm sau $t+1$).
3. Tại điểm chốt Cutoff 08:30 SGT sáng ngày $t+1$, biến động giá dầu Brent đêm qua (`brent_return_pct_aligned`) đã được phản ánh đầy đủ vào tập thông tin của mô hình.
4. Vì dầu thô chiếm hơn 80% cấu thành chi phí lọc dầu, cú sốc đêm tại London tạo ra lực kéo quán tính rất mạnh lên kỳ vọng của các thương nhân Châu Á trong phiên chiều ngày $t+1$.
👉 **Kết luận chuẩn mực:** DA ~70% chứng minh **sự truyền dẫn thông tin có hiệu lực cao qua múi giờ**, chứ không phải là bằng chứng vi mô về hành vi độc quyền hay cấu trúc thị trường xăng dầu. Bằng chứng kinh tế thực chất nằm ở việc các biến biên lọc dầu trong M5 vượt qua kiểm định Clark–West ($p = 0.0245$) khi đối đầu với mô hình kỹ thuật M4."""

pattern_da = r"### 4\.5\. Giải mã Cơ chế Timezone Spillover[\s\S]*?trong phiên chiều ngày \$t\+1\$\."
match_da = re.search(pattern_da, content)
if match_da:
    content = content[:match_da.start()] + da_clarification + content[match_da.end():]

# 5. Add Section 5.3: Explicit Limitations (Hạn chế của nghiên cứu)
limitations_block = """### 5.3. Các Giới hạn của Nghiên cứu (Research Limitations)

Để bảo đảm tính khách quan học thuật trước hội đồng bảo vệ, nghiên cứu thẳng thắn ghi nhận 3 giới hạn phương pháp luận trọng yếu:
1. **Hạn chế về Timestamp Quy ước (Rule-Based Market Proxy Timestamps):**
   Do chuỗi dữ liệu lịch sử giá cuối ngày (EOD) 2008–2025 không lưu trữ bản ghi log máy chủ thời gian thực (tick-by-tick arrival timestamps), toàn bộ các mốc thời gian nội nhật (16:30 SGT cho Platts, 03:30 SGT cho ICE Brent, 08:30 SGT cho Cutoff) được xây dựng dựa trên **quy ước phiên giao dịch của sàn (Rule-Based Proxies)**. Mặc dù các quy tắc kiểm tra logic đều đạt 100% tuân thủ, nghiên cứu không tuyên bố đã xác minh log tick thời gian thực từ máy chủ phân phối dữ liệu.
2. **Hạn chế về Phạm vi Dữ liệu và Thị trường (Data Scope Limitation):**
   Nghiên cứu tập trung chuyên biệt vào thị trường bán buôn hàng rời quốc tế tại cảng Singapore (Platts FOB Singapore Mogas 95) và giá chuẩn dầu thô ICE Brent. Do đó, các kết luận về tính đối xứng hoàn hảo trong truyền dẫn giá phản ánh thị trường đầu mối có tính cạnh tranh cao và thanh khoản tập trung.
3. **Giới hạn về Khả năng Khái quát hóa sang Thị trường Bán lẻ (Generalizability Caution):**
   Kết quả bác bỏ hiện tượng "Tên lửa và Lông vũ" ở thị trường bán buôn quốc tế **không thể tự động suy diễn cho thị trường bán lẻ nội địa (như tại Việt Nam, Hoa Kỳ hay EU)**. Tại thị trường bán lẻ, chu kỳ điều hành giá nhà nước (Nghị định 80/2023/NĐ-CP, Quỹ Bình ổn giá BOG), chi phí kinh doanh định mức, thuế bảo vệ môi trường và cấu trúc cạnh tranh bán lẻ có thể tạo ra các đặc tính phi đối xứng hoàn toàn khác biệt."""

if "### 5.3. Các Giới hạn của Nghiên cứu" not in content:
    content = content.replace("### 5.3. Bảng mã băm SHA-256", limitations_block + "\n\n### 5.4. Bảng mã băm SHA-256")
    content = content.replace("### 5.4. Hướng mở rộng nghiên cứu tương lai", "### 5.5. Hướng mở rộng nghiên cứu tương lai")

md_workspace.write_text(content, encoding="utf-8")
if md_artifact.parent.exists():
    md_artifact.write_text(content, encoding="utf-8")
print("Updated SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md with limitations, hypotheses, and caveats.")

