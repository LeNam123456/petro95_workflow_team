# -*- coding: utf-8 -*-
"""Update academic report and regenerate Word Docx with harmonized OOS table and PIT audit."""

import re
import shutil
import subprocess
from pathlib import Path

# Paths
md_workspace = Path("reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md")
md_artifact = Path("C:/Users/LeeNam/.gemini/antigravity/brain/c95a4cf9-b685-49db-8f18-df5994910785/SPAFS_V5_2_BAO_CAO_HOAN_CHINH.md")
docx_workspace = Path("reports/SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx")
docx_downloads = Path("C:/Users/LeeNam/Downloads/SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx")

content = md_workspace.read_text(encoding="utf-8")

replacement_block = """#### Bảng 4.2: Bảng xếp hạng Stream 2 — Nhánh Học máy Phi tuyến ($N_{OOS} = 754$ phiên giao dịch ngoài mẫu, 2022 – 2025)

| Model ID | Tên mô hình | Số biến ($K$) | RMSE (%/ngày) | MAE (%/ngày) | Directional Acc. (DA) | MCC | PT-Stat | $p$-Value | So sánh cặp đôi |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **M4** | Technical LightGBM | 10 | 1.4221 | 1.0712 | **70.82%** | **0.4156** | 11.2737 | $< 10^{-28}$ | Vượt trội M2/M3 (RMSE giảm từ 1.71% $\to$ 1.42%) |
| **M5** | Economic LightGBM | 15 | **1.4163** | **1.0643** | 70.42% | 0.4078 | 11.1743 | $< 10^{-28}$ | **Clark-West vs M4: $CW = +1.9688, p = 0.0245$** |
| **M6** | Multimodal News LGBM| 18 | *(Roadmap)* | *(Roadmap)* | *(Roadmap)* | — | — | — | Kế hoạch tích hợp News Sentiment FinBERT |

#### Bảng 4.3: Bảng xếp hạng Đánh giá Ngoài mẫu Chung Thống nhất (Harmonized Common OOS Sample, $N_{OOS} = 754$ phiên, 28/12/2022 – 29/12/2025)

Để đảm bảo tính khách quan tuyệt đối và loại trừ mọi chênh lệch về thời kỳ kiểm định giữa hai nhánh, toàn bộ 7 mô hình được đánh giá song song trên cùng một tập mẫu kiểm định chung gồm đúng **754 phiên giao dịch liên tục**:

| Model ID | Phân nhóm mô hình | Số biến ($K$) | RMSE (%/ngày) | MAE (%/ngày) | $R^2_{OOS}$ (%) | DA (%) | PT-Stat | $p$-Value (PT) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M0a** | Naive Zero Return Benchmark | 0 | 1.8004% | 1.3390% | 0.00% | 48.41% | -0.0000 | 0.5000 |
| **M0b** | Historical Expanding Mean | 1 | 2.5393% | 1.9087% | -98.94% | 51.19% | +0.6288 | 0.2648 |
| **M1** | Univariate ARMA(1,1) Đơn biến | 2 | 1.8004% | 1.3395% | -0.01% | 48.41% | -0.0000 | 0.5000 |
| **M2** | Linear Dynamic ADL Tuyến tính | 8 | **1.3880%** | **1.0517%** | **+40.56%** | 70.29% | +11.2115 | $< 10^{-28}$ |
| **M3** | Asymmetric ADL Bất đối xứng | 10 | 1.3888% | 1.0517% | +40.50% | 70.29% | +11.2191 | $< 10^{-28}$ |
| **M4** | Technical LightGBM GBDT Ensemble | 10 | 1.4221% | 1.0712% | +37.61% | **70.82%** | **+11.4202** | $< 10^{-28}$ |
| **M5** | Economic Refining LightGBM Ensemble | 15 | 1.4163% | 1.0643% | +38.12% | 70.42% | +11.2063 | $< 10^{-28}$ |

### 4.3. Xác minh Điểm chốt Thời gian Point-in-Time (PIT) Cấp bản ghi
Trước khi chốt các kết luận thực nghiệm, một đợt kiểm toán tự động độc lập đã được thực thi trên toàn bộ **2,255 bản ghi** của tập dữ liệu Stream 2 thông qua kịch bản `audit_record_level_pit.py`:
- **Invariant 1 ($\text{observation\_datetime} < \text{forecast\_origin\_datetime}$):** Đạt 2,255 / 2,255 bản ghi (**100.0%**).
- **Invariant 2 ($\text{availability\_datetime} \le \text{forecast\_origin\_datetime}$):** Đạt 2,255 / 2,255 bản ghi (**100.0%**). Dữ liệu Platts Mogas 95 khả dụng lúc 03:30 SGT, cách mốc cutoff 08:30 SGT đúng 5.0 giờ an toàn.
- **Invariant 3 ($\text{brent\_availability\_datetime} \le \text{forecast\_origin\_datetime}$):** Đạt 2,255 / 2,255 bản ghi (**100.0%**). Giá thanh toán dầu Brent từ sàn ICE London có sẵn từ 03:30 SGT, cách mốc cutoff đúng 5.0 giờ an toàn.
- **Invariant 4 ($\text{forecast\_origin\_datetime} < \text{target\_realization\_datetime}$):** Đạt 2,255 / 2,255 bản ghi (**100.0%**). Dự báo được phát ra lúc 08:30 SGT, dẫn trước thời điểm đóng phiên thực tế của Platts Mogas 95 (16:30 SGT) đúng **8.0 giờ giao dịch**.
- **Tổng số vi phạm rò rỉ dữ liệu (Lookahead Violations):** **0 bản ghi (0.00%)**.

### 4.4. Kiểm định Cặp đôi Tái lập (Reproducible Pairwise Tests: Clark–West & Diebold–Mariano)
Để đánh giá năng lực dự báo một cách chặt chẽ nhất, hệ thống triển khai kiểm định thống kê cặp đôi trên chuỗi sai số ngoài mẫu đồng bộ ($N_{OOS} = 754$ phiên) thông qua kịch bản tái lập `run_reproducible_clark_west_dm.py`:

#### 1. Kiểm định Clark & West (2007) cho các mô hình lồng ghép (Nested Models):
Công thức hiệu chỉnh nhiễu tham số MSPE:
$$\hat{f}_{t+1} = (e_{\\text{small}, t+1})^2 - \\left[ (e_{\\text{large}, t+1})^2 - (\\hat{y}_{\\text{small}, t+1} - \\hat{y}_{\\text{large}, t+1})^2 \\right] = 2 e_{\\text{small}, t+1} (\\hat{y}_{\\text{large}, t+1} - \\hat{y}_{\\text{small}, t+1})$$

- **M5 (Economic LGBM) vs M4 (Technical LGBM) — Kiểm định RQ2:**
  - $\\text{MSPE}(M5) = 2.005770$ vs $\\text{MSPE}(M4) = 2.022245$ ($\\Delta \\text{MSPE} = +0.016475$).
  - Số hạng bù nhiễu Clark–West: $(\\hat{y}_{M4} - \\hat{y}_{M5})^2 = +0.026240$.
  - Độ lệch hiệu chỉnh trung bình $\\bar{f} = +0.042716$.
  - **Thống kê Clark–West (Newey-West HAC $q=1$): $\\mathbf{CW = +1.9688}$ với $\\mathbf{p = 0.0245} < 0.05$**.
  - **Kết luận:** **Bác bỏ giả thuyết vô hiệu $H_0$ ở mức ý nghĩa 5%**. Các đặc trưng kinh tế học lọc dầu bổ sung mang lại giá trị dự báo vượt trội có ý nghĩa thống kê thực chất.
- **M3 (Asymmetric ADL) vs M2 (Symmetric ADL) — Kiểm định OOS cho RQ1:**
  - $\\text{MSPE}(M3) = 1.928641$ vs $\\text{MSPE}(M2) = 1.926456$ ($\\Delta \\text{MSPE} = -0.002185$).
  - Độ lệch hiệu chỉnh Clark–West $\\bar{f} = -0.001186$.
  - **Thống kê Clark–West: $\\mathbf{CW = -0.3436}$ với $\\mathbf{p = 0.6344}$**.
  - **Kết luận:** **Không thể bác bỏ $H_0$ ($p = 0.6344$)**. Mô hình bất đối xứng M3 hoàn toàn không vượt trội hơn mô hình đối xứng M2 ngoài mẫu, tái khẳng định một cách độc lập và nhất quán kết quả của các kiểm định Wald trong mẫu ($W_F = 0.0035, p = 0.9530$).
- **M5 vs M0a (Zero Benchmark):** $\\mathbf{CW = +10.0129}, p < 10^{-20}$ (Bác bỏ $H_0$ ở mức tuyệt đối).
- **M4 vs M0a (Zero Benchmark):** $\\mathbf{CW = +10.1821}, p < 10^{-20}$ (Bác bỏ $H_0$ ở mức tuyệt đối).

#### 2. Kiểm định Diebold & Mariano (HLN 1997):
- **M5 vs M4 (Squared Loss - MSE):** $\\text{DM}_{\\text{HLN}} = -0.7748, p = 0.2194$. (Kiểm định DM chuẩn bị thiên lệch âm do hai mô hình lồng nhau, củng cố sự cần thiết của kiểm định Clark–West).
- **M5 vs M4 (Absolute Loss - MAE):** $\\text{DM}_{\\text{HLN}} = -1.3088, p = \\mathbf{0.0955} < 0.10$. (M5 vượt trội M4 về sai số tuyệt đối ở mức ý nghĩa biên 10%).

> [!TIP]
> **KẾT LUẬN HỌC THUẬT QUAN TRỌNG (RQ2):** Giả thuyết vô hiệu $H_0$ bị **bác bỏ dứt khoát ở mức ý nghĩa 5%**. Kết quả chứng minh rằng việc bổ sung các biến kinh tế lọc dầu hạ nguồn (Crack Spread, Phí Octane và Chênh lệch Xăng-Diesel) mang lại năng lực dự báo vượt trội có ý nghĩa thống kê thực chất so với việc chỉ dựa vào các chỉ báo kỹ thuật động lượng thuần túy."""

# Regex replace from "#### Bảng 4.2: Bảng xếp hạng Stream 2" to "> [!TIP]...thuần túy."
pattern = r"#### Bảng 4\.2: Bảng xếp hạng Stream 2[\s\S]*?> \[!TIP\][\s\S]*?thuần túy\."
match = re.search(pattern, content)
if match:
    new_content = content[:match.start()] + replacement_block + content[match.end():]
    md_workspace.write_text(new_content, encoding="utf-8")
    if md_artifact.parent.exists():
        md_artifact.write_text(new_content, encoding="utf-8")
    print("Successfully updated Markdown report!")
else:
    print("Error: Could not find regex match for replacement block.")

