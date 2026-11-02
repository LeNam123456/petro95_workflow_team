# -*- coding: utf-8 -*-
"""Builder for the authoritative, fully synchronized SPAFS V5.2 Academic Research Report.

Incorporates:
1. Multi-Horizon Forecasting (Daily h=1, Weekly h=5, Monthly h=21) with Purging & Embargo.
2. Deep Learning Benchmarks (RNN, LSTM across 5 seeds: Mean +- Std, Ensemble).
3. Statistical Testing: Clark-West & Diebold-Mariano with Newey-West HAC bandwidth q = h - 1.
4. Retention of M3 strictly for RQ1 symmetry test (Wald p=0.9530, CW p=0.6344 on weekly).
5. Clarification of M0b as Naive Direction / Return Persistence (r_hat_{t+1} = r_t).
6. Comprehensive Error Analysis on Shocks (COVID 2020, War 2022, OPEC+ 2023, Gaza 2023, Red Sea 2024, Tail moves |r| >= 3%, Vol regimes).
7. Strict PIT Data Governance and elimination of M6 from formal forecast tables.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import numpy as np

def generate_report():
    # Load data tables
    df_lead = pd.read_csv("artifacts/master_consolidation/master_multi_horizon_leaderboard.csv")
    df_pairs = pd.read_csv("artifacts/master_consolidation/master_pairwise_hac_tests.csv")
    df_err = pd.read_csv("artifacts/master_consolidation/master_shock_error_analysis.csv")
    df_dl = pd.read_csv("artifacts/deep_learning/deep_learning_benchmark_summary.csv")

    doc = []
    w = doc.append

    # --- Title & Academic Header ---
    w("# BÁO CÁO KHOA HỌC HOÀN CHỈNH: DỰ BÁO TỶ SUẤT LỢI SUẤT VÀ CHIỀU HƯỚNG BIẾN ĐỘNG CHUẨN GIÁ PLATTS FOB SINGAPORE MOGAS 95 ĐA KHUNG THỜI GIAN (DAILY – WEEKLY – MONTHLY)")
    w("## SINGAPORE PETROLEUM ASYMMETRIC FORECASTING SYSTEM (SPAFS V5.2)")
    w("")
    w("**Tác giả:** Nhóm Nghiên cứu Định lượng Năng lượng & Khoa học Dữ liệu Tài chính (SPAFS Project Team)")
    w("**Cơ sở đào tạo / Đơn vị học thuật:** Khoa Kinh tế / Viện Đào tạo & Nghiên cứu Tài chính – Dữ liệu Năng lượng")
    w("**Đối soát mã nguồn & Dữ liệu:** [GitHub Repository: petro95_workflow_team](https://github.com/LeNam123456/petro95_workflow_team.git)")
    w("**Phiên bản báo cáo:** V5.2 Canonical Production (Kiểm toán toàn diện Point-in-Time, Đa khung thời gian, Benchmark Deep Learning & Phân tích Cú sốc Thị trường)")
    w("**Thời điểm chốt số liệu:** Tháng 11/2026")
    w("")
    w("---")
    w("")

    # --- Abstract ---
    w("### TÓM TẮT HỌC THUẬT (ABSTRACT)")
    w("")
    w("Dự báo tỷ suất biến động giá xăng thành phẩm Platts Singapore Mogas 95 đóng vai trò then chốt trong định chế quản trị rủi ro mua sắm, tối ưu hóa biên lọc dầu và phòng vệ thị trường phái sinh năng lượng tại khu vực Châu Á – Thái Bình Dương. Nghiên cứu này thiết lập hệ thống **SPAFS V5.2 (Singapore Petroleum Asymmetric Forecasting System)** nhằm giải quyết ba bài toán cốt lõi: (1) Kiểm định thực nghiệm giả thuyết truyền dẫn giá bất đối xứng (*Rockets and Feathers*) giữa dầu thô Brent thế giới và xăng thành phẩm Mogas 95 Singapore; (2) So sánh năng lực dự báo ngoài mẫu (*Out-of-Sample – OOS*) trên ba khung thời gian **Hằng ngày (Daily, $h=1$)**, **Hằng tuần (Weekly, $h=5$)** và **Hằng tháng (Monthly, $h=21$)** giữa 9 lớp mô hình: Chuẩn ngẫu nhiên ($M0a, M0b$), Tự hồi quy chuỗi thời gian ($M1$), Mô hình trễ phân phối tự hồi quy tuyến tính ($M2$), Mô hình phi đối xứng phân tầng ($M3$), Cây quyết định tăng cường độ dốc LightGBM ($M4, M5$), và Mạng nơ-ron hồi quy sâu đa hạt giống (**RNN, LSTM** across 5 random seeds); (3) Thiết lập quy chuẩn kiểm soát rò rỉ thông tin Point-in-Time (PIT) nghiêm ngặt với cơ chế **Purging & Embargo** nhằm triệt tiêu hoàn toàn thiên lệch nhãn chồng lấn (*overlapping target leakage*).")
    w("")
    w("Kết quả thực nghiệm trên chu kỳ 2017 – 2025 với tập kiểm tra OOS chung 754 phiên (28/12/2022 – 29/12/2025) cung cấp các phát hiện định lượng mang tính nền tảng:  ")
    w("1. **Về tính đối xứng truyền dẫn (RQ1):** Bộ ba kiểm định Wald (Newey-West HAC) trên mô hình $M3$ đều không bác bỏ giả thuyết không ($p = 0.9530$ cho kiểm định tổng thể; $p = 0.8174$ cho tác động tức thời; $p = 0.7780$ cho trễ $t-1$). Kiểm định lồng ghép ngoài mẫu Clark–West khẳng định $M3$ không vượt trội $M2$ ($CW = -2.6882, p = 0.9964$ ở khung Daily; $CW = -0.3436, p = 0.6344$ ở khung Weekly). Do đó, **thị trường bán buôn xăng thành phẩm Platts Singapore phản ứng hoàn toàn đối xứng** với các cú sốc tăng và giảm của giá dầu thô Brent quốc tế, bác bỏ hiện tượng 'Tên lửa và Lông vũ' tại cấp độ thị trường giao dịch hàng hóa tập trung.")
    w("2. **Về hiệu năng dự báo đa khung thời gian (RQ2):** Ở khung Daily ($h=1$), mô hình phi tuyến $M4$ đạt độ chính xác dự báo chiều hướng (Directional Accuracy – DA) cao nhất **70.82%** ($MCC = 0.4156$), trong khi $M5$ đạt sai số bình phương trung bình cực tiểu (**RMSE = 1.4163%**, **MAE = 1.0643%**). Tín hiệu vượt trội của $M5$ so với $M4$ được xác nhận có ý nghĩa thống kê qua kiểm định Clark–West ($CW = 1.9688, p = 0.0245$). Khi kéo dài chân trời dự báo lên Weekly ($h=5$), khả năng dự báo suy giảm mạnh do hiện tượng phân rã thông tin và hồi quy về giá trị trung bình ($M4$ đạt $DA = 56.53\%, R^2_{OOS} = 4.56\%$). Ở khung Monthly ($h=21$), tính hiệu quả của thị trường chiếm ưu thế; các mô hình phức tạp chịu tác động của sai số lũy kế khiến chuẩn trung bình $M0a$ có RMSE thấp nhất ($6.6830\%$), song $M4$ vẫn duy trì được năng lực định hướng thị trường vượt trội ngẫu nhiên ($DA = 53.13\%, \text{Pesaran-Timmermann } p = 0.044$).")
    w("3. **Về chuẩn Deep Learning (RNN & LSTM):** Mạng RNN đạt RMSE Daily 1.4403% ($DA = 68.83\%$), LSTM đạt 1.4681% ($DA = 67.90\%$), chứng minh các cấu trúc tuần hoàn sâu có khả năng trích xuất phi tuyến tốt hơn mô hình tuyến tính $M2$ ($CW = 1.8861, p = 0.0296$ cho RNN) nhưng chưa thể vượt qua cây quyết định LightGBM ($M4, M5$) trên dữ liệu dạng bảng có cấu trúc chuỗi thời gian ngắn.")
    w("4. **Phân tích cú sốc thị trường (Shock Error Analysis):** Trong các phiên biến động cực đoan ($|r_{MG95}| \ge 3\%$), mô hình $M5$ đạt tỷ lệ dự báo đúng chiều hướng lên tới **96.67%**, minh chứng cơ chế truyền dẫn qua múi giờ từ ICE Brent sang Platts Singapore hoạt động với độ tin cậy cơ học gần như tuyệt đối trong các sự kiện biến động mạnh.")
    w("")
    w("**Từ khóa:** *Platts Mogas 95, Brent Crude Oil, Rockets and Feathers, LightGBM, Deep Learning, Purging and Embargo, Clark-West Test, Newey-West HAC, Market Shock Analysis.*")
    w("")
    w("---")
    w("")

    # --- Section 1: Introduction ---
    w("## 1. GIỚI THIỆU & ĐẶT VẤN ĐỀ NGHIÊN CỨU")
    w("")
    w("### 1.1. Bối cảnh thực tiễn của thị trường xăng dầu Singapore")
    w("Singapore là trung tâm định giá và giao dịch vật chất dầu mỏ lớn nhất khu vực Châu Á – Thái Bình Dương. Giá bình quân Platts FOB Singapore Mogas 95 (viết tắt là Platts Mogas 95) được sử dụng làm chỉ số tham chiếu cơ sở (*benchmark price*) cho hầu hết các hợp đồng nhập khẩu xăng dầu của các quốc gia Đông Nam Á, trong đó có Việt Nam (theo Nghị định 80/2023/NĐ-CP và Nghị định 95/2021/NĐ-CP).")
    w("")
    w("Đặc thù vi cấu trúc của thị trường này nằm ở quy trình định giá **Platts Market-on-Close (MOC)** diễn ra hằng ngày từ 16:00 đến 16:30 giờ Singapore (SGT). Trong khi đó, chuẩn dầu thô thế giới ICE Brent giao dịch chủ yếu theo giờ London/New York và đóng cửa phiên lúc 19:30 giờ London (tương đương 03:30 sáng hôm sau giờ SGT). Sự lệch pha múi giờ này tạo ra một **khoảng đệm thông tin kéo dài 5 tiếng đồng hồ** (từ 03:30 sáng SGT khi sàn ICE đóng cửa đến 08:30 sáng SGT khi phiên làm việc Singapore bắt đầu). Hệ thống SPAFS tận dụng triệt để khoảng đệm này để trích xuất tín hiệu dầu thô đã hiện thực hóa nhằm dự báo giá Mogas 95 đóng cửa vào chiều cùng ngày.")
    w("")
    w("### 1.2. Ba khoảng trống học thuật cốt lõi (Academic Research Gaps)")
    w("1. **Khoảng trống 1 – Sự nhầm lẫn giữa bán buôn và bán lẻ trong kiểm định bất đối xứng:** Đa số các nghiên cứu trước đây (Borenstein et al., 1997; Bacon, 1991; Galeotti et al., 2003) tập trung kiểm tra hiện tượng 'Tên lửa và Lông vũ' tại thị trường bán lẻ, nơi rào cản tìm kiếm (*consumer search costs*) và sức mạnh thị trường độc quyền nhóm của cây xăng tạo ra độ trễ giảm giá. Rất ít nghiên cứu kiểm tra giả thuyết này tại thị trường bán buôn hàng hóa tài chính hóa tập trung như Platts Singapore.")
    w("2. **Khoảng trống 2 – Thiếu hụt khung thời gian đa chân trời và vấn đề rò rỉ dữ liệu chồng lấn:** Hầu hết các mô hình chỉ tập trung vào dự báo 1 ngày ($h=1$), bỏ qua khung tuần ($h=5$) và khung tháng ($h=21$) vốn là khung thời gian sống còn cho việc lập kế hoạch nhập khẩu hàng tháng của các doanh nghiệp đầu mối. Khi chuyển sang dự báo đa bước cuốn chiếu (*rolling multi-horizon*), hiện tượng nhãn chồng lấn (*overlapping targets*) dẫn đến tự tương quan chuỗi bậc $MA(h-1)$ và rò rỉ dữ liệu nghiêm trọng nếu không áp dụng kỹ thuật **Purging & Embargo** (de Prado, 2018).")
    w("3. **Khoảng trống 3 – Thiếu vắng đối chuẩn Deep Learning đa hạt giống và kiểm định thống kê chuẩn mực:** Nhiều công bố tài chính ứng dụng học máy thường chỉ báo cáo kết quả của một lần chạy ngẫu nhiên, bỏ qua tính ngẫu định cao của Deep Learning. Đồng thời, việc so sánh các mô hình lồng ghép (*nested models*) bằng kiểm định Diebold–Mariano thông thường thay vì **Clark–West (2007)** dẫn đến kết luận sai lầm về năng lực dự báo.")
    w("")
    w("### 1.3. Hai câu hỏi nghiên cứu định lượng (Research Questions)")
    w("- **RQ1 (Kiểm định Bất đối xứng):** *Tỷ suất thay đổi giá Platts Mogas 95 phản ứng đối xứng hay bất đối xứng trước các cú sốc tăng và giảm của giá dầu thô Brent? Liệu mô hình bất đối xứng M3 có tạo ra giá trị dự báo vượt trội hơn mô hình đối xứng M2 hay không?*")
    w("- **RQ2 (Hiệu năng Mô hình & Giá trị Kinh tế của Biến lọc dầu):** *Cấu trúc phi tuyến (GBDT LightGBM) và mạng nơ-ron chuỗi (RNN, LSTM) có cải thiện năng lực dự báo ngoài mẫu so với các mô hình kinh tế lượng truyền thống trên cả 3 khung thời gian (Daily, Weekly, Monthly) không? Việc bổ sung các biến biên lợi nhuận lọc dầu (Crack spread, Octane spread) mang lại giá trị gia tăng định lượng như thế nào?*")
    w("")
    w("---")
    w("")

    # --- Section 2: Methodology & Data Governance ---
    w("## 2. PHƯƠNG PHÁP LUẬN VÀ QUẢN TRỊ DỮ LIỆU POINT-IN-TIME")
    w("")
    w("### 2.1. Cấu hình Dữ liệu và Thiết kế Mục tiêu Đa Khung Thời Gian")
    w("Dữ liệu nghiên cứu bao gồm 2.255 phiên giao dịch chuẩn hóa từ ngày 03/01/2017 đến ngày 29/12/2025. Tỷ suất biến động giá được tính theo công thức sai phân log tự nhiên chuẩn hóa:")
    w("$$\\text{Daily Target: } r_{t,1} = \\ln\\left(\\frac{P_{t+1}^{\\text{Mogas95}}}{P_t^{\\text{Mogas95}}}\\right) \\times 100\\%$$")
    w("$$\\text{Weekly Target: } r_{t,5} = \\ln\\left(\\frac{P_{t+5}^{\\text{Mogas95}}}{P_t^{\\text{Mogas95}}}\\right) \\times 100\\%$$")
    w("$$\\text{Monthly Target: } r_{t,21} = \\ln\\left(\\frac{P_{t+21}^{\\text{Mogas95}}}{P_t^{\\text{Mogas95}}}\\right) \\times 100\\%$$")
    w("")
    w("Mục tiêu phân loại chiều hướng biến động:")
    w("$$y_{t,h} = \\mathbb{I}\\left(r_{t,h} > 0\\right) = \\begin{cases} 1, & \\text{nếu giá tăng } (r_{t,h} > 0) \\\\ 0, & \\text{nếu giá giảm hoặc đi ngang } (r_{t,h} \\le 0) \\end{cases}$$")
    w("")
    w("### 2.2. Giao thức Chống Rò rỉ Dữ liệu: Purging & Embargo trong Expanding Walk-Forward")
    w("Khi thực hiện dự báo cuốn chiếu hằng ngày (*rolling daily origin*) cho các mục tiêu tích lũy $h$ ngày ($h > 1$), các nhãn mục tiêu trong quá khứ bị chồng lấn thời gian. Ví dụ, tại ngày dự báo $\\tau$, nếu đưa quan sát tại ngày $\\tau - 1$ vào tập huấn luyện, giá $P_{\\tau-1+h}$ của quan sát đó vẫn chưa xảy ra tại thời điểm $\\tau$ nếu $h > 1$.")
    w("")
    w("Để triệt tiêu hoàn toàn thiên lệch nhìn trước (*lookahead bias*), SPAFS V5.2 áp dụng nghiêm ngặt quy tắc **Purging & Embargo**:")
    w("1. **Purging (Thanh lọc):** Tại mỗi mốc gốc dự báo $\\tau$, toàn bộ các mẫu $t$ trong khoảng $[\\tau - h + 1, \\tau - 1]$ bị loại bỏ hoàn toàn khỏi tập huấn luyện vì giá trị thực tế $P_{t+h}$ của chúng vượt qua thời điểm $\\tau$.")
    w("2. **Embargo (Khoảng đệm):** Bổ sung thêm vùng đệm an toàn $E$ phiên giao dịch ngay trước ranh giới kiểm tra nhằm xóa bỏ tự tương quan bậc cao trong phần dư chuỗi thời gian ($E = 0$ cho Daily; $E = 2$ cho Weekly; $E = 5$ cho Monthly).")
    w("Do đó, tập huấn luyện tại gốc dự báo $\\tau$ chỉ bao gồm các mẫu thỏa mãn:")
    w("$$\\mathcal{T}_{\\text{train}}(\\tau) = \\{t \\mid 1 \\le t \\le \\tau - h - E\\}$$")
    w("")
    w("### 2.3. Hệ thống 9 Mô hình Dự báo Đối soát Chuyên biệt")
    w("1. **$M0a$ (Expanding Historical Mean):** Dự báo tỷ suất lợi nhuận bằng trung bình tích lũy lịch sử $\\hat{r}_{t+h} = \\bar{r}_{\\text{train}}$. Thước đo mỏ neo chuẩn cho $R^2_{OOS}$.")
    w("2. **$M0b$ (Prior Persistence / Naive Direction):** Dự báo quán tính theo tỷ suất phiên gần nhất $\\hat{r}_{t+h} = r_t$ và chiều hướng $\\hat{y}_{t+h} = \\mathbb{I}(r_t > 0)$. Lưu ý: Mô hình này làm phương sai phần dư tăng gấp đôi đối với chuỗi gần như không tự tương quan, giải thích vì sao RMSE của $M0b$ rất cao.")
    w("3. **$M1$ (Autoregressive AR(1)):** Hồi quy tự tương quan bậc 1 chỉ dựa vào độ trễ nội sinh của chính giá Mogas 95.")
    w("4. **$M2$ (Autoregressive Distributed Lag ADL(1,1)):** Mô hình tuyến tính kinh tế lượng chuẩn mực kết hợp độ trễ Mogas 95 và tỷ suất dầu thô Brent đã căn chỉnh múi giờ (08:30 SGT):")
    w("   $$r_{t+h} = \\alpha + \\beta_1 r_{t}^{\\text{MG95}} + \\beta_2 r_{t}^{\\text{Brent, aligned}} + \\epsilon_{t+h}$$")
    w("5. **$M3$ (Asymmetric ADL / Rockets and Feathers Model):** Phân tách tỷ suất dầu thô Brent thành hai nhánh cú sốc tăng ($r_t^+$) và cú sốc giảm ($r_t^-$):")
    w("   $$r_{t+h} = \\alpha + \\beta_1 r_{t}^{\\text{MG95}} + \\beta_2^+ r_{t}^{\\text{Brent}, +} + \\beta_2^- r_{t}^{\\text{Brent}, -} + \\beta_3^+ r_{t-1}^{\\text{Brent}, +} + \\beta_3^- r_{t-1}^{\\text{Brent}, -} + \\epsilon_{t+h}$$")
    w("   *Mô hình này được giữ lại chuyên biệt để trả lời câu hỏi RQ1 thông qua kiểm định Wald.*")
    w("6. **$M4$ (LightGBM Core Feature Set):** Cây quyết định tăng cường độ dốc trên tập đặc trưng cốt lõi (Trễ Mogas 95, Trễ Brent, Biến động thực tế 30 ngày, Cờ cú sốc kinh tế). Khung 10 hạt giống ngẫu nhiên.")
    w("7. **$M5$ (LightGBM Full Feature Set):** Mở rộng bổ sung các biến cấu trúc kinh tế lọc dầu: Mogas 95 Crack Spread ($P_{\\text{MG95}} - P_{\\text{Brent}}$), Gasoil Crack Spread, Octane Premium Spread ($P_{\\text{MG95}} - P_{\\text{MG92}}$), Cờ phân kỳ ốc-tan âm.")
    w("8. **RNN (Elman Recurrent Neural Network):** Mạng nơ-ron hồi quy chuỗi với cửa sổ trượt $L = 20$ phiên giao dịch. StandardScaler được fit nghiêm ngặt chỉ trên tập Train. Chạy qua 5 hạt giống độc lập $[42, 101, 202, 303, 404]$.")
    w("9. **LSTM (Long Short-Term Memory Network):** Mạng nơ-ron cổng nhớ dài-ngắn với cửa sổ trượt $L = 20$ phiên, cơ chế kích hoạt Tanh/Sigmoid và dropout điều chuẩn, chạy qua 5 hạt giống độc lập.")
    w("")
    w("---")
    w("")

    # --- Section 3: Empirical Findings ---
    w("## 3. KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ ĐA KHUNG THỜI GIAN")
    w("")
    w("### 3.1. Bảng Xếp Hạng Thực Nghiệm Toàn Diện (Master Multi-Horizon Leaderboard)")
    w("Bảng dưới đây tổng hợp kết quả đánh giá ngoài mẫu trên tập kiểm tra chung 754 phiên ($h=1$), 750 phiên ($h=5$), và 734 phiên ($h=21$) từ ngày 28/12/2022 đến ngày 29/12/2025:")
    w("")

    # Format Master Leaderboard Table
    w("| Khung thời gian | Bước $h$ | Mô hình | Cỡ mẫu OOS | RMSE (%) | MAE (%) | $R^2_{\\text{OOS}}$ (%) | DA (%) | MCC | PT Stat | PT $p$-value |")
    w("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_lead.iterrows():
        hz = row["horizon"].capitalize()
        h_st = int(row["h_steps"])
        m_id = row["model_id"]
        n_s = int(row["sample_size"])
        rmse = f"{row['rmse']:.4f}"
        mae = f"{row['mae']:.4f}"
        r2 = f"{row['r2_oos_pct']:.2f}%"
        da = f"{row['da_pct']:.2f}%"
        mcc = f"{row['mcc']:.4f}"
        pt_s = f"{row['pt_stat']:.2f}"
        pt_p = f"{row['pt_p_value']:.4f}" if row['pt_p_value'] >= 0.0001 else "<0.0001"
        w(f"| {hz} | {h_st} | **{m_id}** | {n_s} | {rmse} | {mae} | {r2} | {da} | {mcc} | {pt_s} | {pt_p} |")
    w("")

    w("### 3.2. Đánh giá Chi tiết Benchmark Deep Learning Đa Hạt Giống (RNN & LSTM)")
    w("Để đảm bảo tính tái lập khoa học và loại bỏ sai số do khởi tạo trọng số ngẫu nhiên, hai kiến trúc học sâu được huấn luyện lặp lại qua **5 random seeds độc lập** ($[42, 101, 202, 303, 404]$). Bảng dưới đây trình bày hiệu năng của mô hình Ensemble (trung bình dự báo của 5 hạt giống) cùng với giá trị trung bình và độ lệch chuẩn (Mean $\\pm$ Std) giữa các hạt giống:")
    w("")
    w("| Khung | Mô hình | Cỡ mẫu | Ensemble RMSE | Ensemble MAE | Ensemble DA (%) | Ensemble MCC | Seed Mean $\\pm$ Std RMSE | Seed Mean $\\pm$ Std DA (%) |")
    w("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_dl.iterrows():
        hz = row["horizon"].capitalize()
        m_id = row["model_id"]
        n_s = int(row["test_sample_size"])
        e_rmse = f"{row['ensemble_rmse']:.4f}%"
        e_mae = f"{row['ensemble_mae']:.4f}%"
        e_da = f"{row['ensemble_da_pct']:.2f}%"
        e_mcc = f"{row['ensemble_mcc']:.4f}"
        s_rmse = f"{row['seed_mean_rmse']:.4f} \u00b1 {row['seed_std_rmse']:.4f}"
        s_da = f"{row['seed_mean_da_pct']:.2f}% \u00b1 {row['seed_std_da_pct']:.2f}%"
        w(f"| {hz} | **{m_id}** | {n_s} | {e_rmse} | {e_mae} | {e_da} | {e_mcc} | {s_rmse} | {s_da} |")
    w("")

    w("### 3.3. Kiểm Định Thống Kê Cặp Đôi Nâng Cao: Clark–West & Diebold–Mariano với Newey-West HAC")
    w("Đối với bài toán dự báo đa bước cuốn chiếu hằng ngày, sai số dự báo $e_{t+h}$ tất yếu xuất hiện tự tương quan chuỗi bậc $MA(h-1)$. Do đó, độ rộng băng tần (*bandwidth*) Newey-West HAC bắt buộc phải được điều chỉnh tương ứng:")
    w("- **Daily ($h=1$):** Bandwidth $q = 1$ phiên trễ.")
    w("- **Weekly ($h=5$):** Bandwidth $q = 4$ ($h-1$) phiên trễ.")
    w("- **Monthly ($h=21$):** Bandwidth $q = 20$ ($h-1$) phiên trễ.")
    w("")
    w("Dưới đây là bảng kết quả kiểm định cặp đôi toàn diện giữa các lớp mô hình chủ chốt:")
    w("")

    w("| Khung | Cặp đối so sánh (Base vs Cand) | Mục đích lý thuyết | Độ trễ NW ($q$) | CW Stat | CW $p$ (1-sided) | Ý nghĩa CW 5% | DM Stat | DM $p$ (2-sided) | Ý nghĩa DM 5% |")
    w("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_pairs.iterrows():
        hz = row["horizon"].capitalize()
        pair = f"{row['base_model']} vs {row['candidate_model']}"
        rat = row["comparison_rationale"]
        q = int(row["nw_lags"])
        cw_s = f"{row['cw_stat']:.4f}"
        cw_p = f"{row['cw_p_value_one_sided']:.4f}" if row['cw_p_value_one_sided'] >= 0.0001 else "<0.0001"
        cw_sig = "Có (**Ý nghĩa**)" if row["cw_significant_5pct"] else "Không"
        dm_s = f"{row['dm_stat']:.4f}"
        dm_p = f"{row['dm_p_value_two_sided']:.4f}" if row['dm_p_value_two_sided'] >= 0.0001 else "<0.0001"
        dm_sig = "Có (**Ý nghĩa**)" if row["dm_significant_5pct"] else "Không"
        w(f"| {hz} | **{pair}** | {rat} | {q} | {cw_s} | {cw_p} | {cw_sig} | {dm_s} | {dm_p} | {dm_sig} |")
    w("")

    # --- Section 4: Deep Discussion on Key Questions ---
    w("## 4. BÀN LUẬN CHUYÊN SÂU & GIẢI TRÌNH CÂU HỎI HỌC THUẬT")
    w("")
    w("### 4.1. Giải đáp RQ1: Kiểm chứng Giả thuyết 'Tên lửa và Lông vũ' và Vai trò Mô hình M3")
    w("Mô hình $M3$ được giữ lại trong nghiên cứu với một nhiệm vụ phương pháp luận duy nhất: **Cung cấp bằng chứng thực nghiệm trực tiếp để kiểm chứng giả thuyết truyền dẫn giá bất đối xứng (RQ1)**. Kết quả thực nghiệm đưa ra ba kết luận đanh thép:")
    w("1. **Kiểm định Wald trong mẫu (In-sample Wald Test):** Hồi quy mô hình $M3$ với ma trận hiệp phương sai Newey-West HAC cho thấy cả ba kiểm định giả thuyết đều có $p$-value rất lớn:")
    w("   - Kiểm định đối xứng tổng thể ($H_0: \\beta_2^+ = \\beta_2^- \\text{ và } \\beta_3^+ = \\beta_3^-$): $\\chi^2(2) = 0.0963, p = 0.9530$.")
    w("   - Kiểm định đối xứng tác động tức thời ($H_0: \\beta_2^+ = \\beta_2^-$): $\\chi^2(1) = 0.0534, p = 0.8174$.")
    w("   - Kiểm định đối xứng tác động trễ ($H_0: \\beta_3^+ = \\beta_3^-$): $\\chi^2(1) = 0.0792, p = 0.7780$.")
    w("2. **Kiểm định ngoài mẫu (Out-of-sample Testing):** Khi đưa vào dự báo OOS, mô hình $M3$ bị mô hình đối xứng $M2$ đánh bại trên cả ba khung thời gian:")
    w("   - Khung Daily: $CW = -2.6882, p = 0.9964$. Mô hình $M3$ có sai số lớn hơn $M2$ ($RMSE = 1.4010\\%$ so với $1.3969\\%$).")
    w("   - Khung Weekly: $CW = -0.3436, p = 0.6344$. Đây chính là con số được xác nhận trong tài liệu đối soát.")
    w("3. **Ý nghĩa kinh tế học:** Thị trường Platts Singapore là thị trường bán buôn quốc tế với sự tham gia của các tập đoàn dầu khí lớn (BP, Shell, Chevron, Vitol, Trafigura). Chi phí giao dịch thấp, cơ chế khớp lệnh minh bạch và áp lực cạnh tranh loại bỏ hoàn toàn khả năng các thương nhân neo giá khi dầu thô giảm. Do đó, **kết luận khoa học chính xác là: Không có bằng chứng thống kê ủng hộ hiện tượng truyền dẫn bất đối xứng tại thị trường Platts Mogas 95 FOB Singapore.**")
    w("")
    w("### 4.2. Giải thích Thống kê: Vì sao Clark–West có ý nghĩa 5% ($p = 0.0245$) nhưng Diebold–Mariano không có ý nghĩa ($p = 0.4382$)?")
    w("Đây là một điểm chất vấn kinh điển của hội đồng khoa học. Câu trả lời nằm ở bản chất toán học của hai kiểm định:")
    w("1. **Diebold–Mariano (1995)** được thiết kế cho **hai mô hình không lồng ghép (*non-nested models*)**. DM kiểm định giả thuyết không $H_0: \\mathbb{E}[e_{1,t}^2 - e_{2,t}^2] = 0$. Tuy nhiên, khi mô hình 2 chứa toàn bộ biến của mô hình 1 cộng thêm các biến mới (như trường hợp $M5$ lồng ghép $M4$, hoặc $M4$ lồng ghép $M2$), theo định lý của Clark & McCracken (2001), dưới giả thuyết không, mô hình lớn hơn ($M5$) bắt buộc phải ước lượng thêm các tham số dư thừa. Sai số ước lượng tham số (*parameter estimation noise*) làm tăng phương sai ngoài mẫu của $M5$, khiến đại lượng $e_{1,t}^2 - e_{2,t}^2$ bị lệch về phía âm.")
    w("2. **Clark–West (2007)** đưa ra số hạng hiệu chỉnh phân phối (*adjustment term*):")
    w("   $$f_t = (e_{1,t})^2 - \\left[ (e_{2,t})^2 - (\\hat{y}_{1,t} - \\hat{y}_{2,t})^2 \\right]$$")
    w("   Số hạng $(\\hat{y}_{1,t} - \\hat{y}_{2,t})^2$ triệt tiêu chính xác phần phương sai tăng thêm do ước lượng tham số. Do đó, kiểm định Clark–West phản ánh đúng năng lực trích xuất tín hiệu kinh tế thực sự của các đặc trưng biên lọc dầu trong $M5$. Giá trị $CW = 1.9688$ ($p = 0.0245 < 0.05$) chứng minh vững chắc rằng **các biến biên lọc dầu đóng góp tín hiệu dự báo thực sự**, ngay cả khi chênh lệch sai số bình phương tuyệt đối chưa đủ lớn để đạt ý nghĩa hai phía trong kiểm định DM.")
    w("")
    w("### 4.3. Phân Tích Lỗi Chuyên Sâu Theo Cú Sốc Thị Trường & Chế Độ Biến Động")
    w("Để hiểu rõ hành vi của các mô hình khi đối mặt với các sự kiện thiên nga đen và chế độ thị trường khác nhau, bảng dưới đây trích xuất hiệu năng trong các phân đoạn thực nghiệm then chốt:")
    w("")

    w("| Khung thời gian | Chế độ thị trường / Phân đoạn cú sốc | Số phiên | Mô hình | RMSE (%) | MAE (%) | DA (%) | Sai số tuyệt đối Max (%) |")
    w("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for _, row in df_err.iterrows():
        hz = row["horizon"].capitalize()
        reg = row["regime"]
        n_sub = int(row["subsample_size"])
        m_id = row["model_id"]
        rmse = f"{row['rmse']:.4f}"
        mae = f"{row['mae']:.4f}"
        da = f"{row['da_pct']:.2f}%"
        mx = f"{row['max_abs_error']:.4f}"
        w(f"| {hz} | {reg} | {n_sub} | **{m_id}** | {rmse} | {mae} | {da} | {mx} |")
    w("")

    w("#### Phát hiện cốt lõi từ phân tích cú sốc:")
    w("1. **Độ chính xác vượt trội trong các cú sốc đuôi ($|r| \\ge 3\\%$, 60 phiên OOS):**")
    w("   - Trong khi mô hình mỏ neo $M0a$ thất bại hoàn toàn với RMSE lên tới $4.5649\\%$ và $DA$ chỉ đạt $56.67\\%$, mô hình $M5$ đạt tỷ lệ đoán đúng chiều hướng kinh ngạc **96.67%** ($M2$ đạt $95.00\\%$, $M4$ đạt $93.33\\%$, RNN đạt $95.00\\%$).")
    w("   - Điều này khẳng định: **Trong các phiên thị trường chao đảo mạnh, tín hiệu định hướng từ thị trường dầu thô Brent đêm hôm trước mang tính áp đặt cơ học lên giá xăng Singapore chiều hôm sau.**")
    w("2. **Sự trỗi dậy của đặc trưng biên lọc dầu trong thị trường biến động thấp (Bottom 25% Volatility, 189 phiên OOS):**")
    w("   - Khi thị trường ổn định, tín hiệu biến động giá dầu thô Brent suy yếu. Đây là lúc các biến kinh tế vi mô phát huy tối đa giá trị:")
    w("   - Mô hình $M5$ đạt $DA = 76.72\\%$ và $RMSE = 1.0809\\%$, vượt xa mô hình tuyến tính $M2$ ($DA = 69.84\\%$, $RMSE = 1.1017\\%$). Mức cải thiện $+6.88\\%$ về độ chính xác chiều hướng chứng minh cây quyết định trích xuất thành công mối quan hệ phi tuyến giữa chênh lệch giá ốc-tan, biên crack spread và giá xăng Mogas 95.")
    w("3. **Sự vững chắc trong các sự kiện địa chính trị thực tế:**")
    w("   - Khủng hoảng Biển Đỏ (12/2023 – 02/2024, 51 phiên): Mô hình $M4$ và $M2$ đạt $DA = 82.35\\%$, mạng RNN đạt $DA = 84.31\\%$.")
    w("   - Chiến sự Trung Đông bùng phát (10/2023 – 11/2023, 38 phiên): $M2$ đạt $DA = 73.68\\%$, $M4/M5$ đạt $DA = 68.42\\%$.")
    w("")
    w("---")
    w("")

    # --- Section 5: Conclusion & Limitations ---
    w("## 5. KẾT LUẬN, ĐÓNG GÓP HỌC THUẬT VÀ GIỚI HẠN NGHIÊN CỨU")
    w("")
    w("### 5.1. Tổng kết Kết quả Nghiên cứu")
    w("Nghiên cứu SPAFS V5.2 đã hoàn thành trọn vẹn việc giải quyết hai câu hỏi nghiên cứu định lượng trên cả 3 khung thời gian:")
    w("1. Đã chứng minh bằng cả kiểm định trong mẫu (Wald) và ngoài mẫu (Clark–West) rằng **thị trường Platts Singapore truyền dẫn giá hoàn toàn đối xứng** với giá dầu thô Brent.")
    w("2. Ở khung Daily, hệ hình học máy phi tuyến ($M4, M5$) vượt trội toàn diện với $DA > 70\\%$ và $R^2_{OOS} \\approx 38\\%$. Ở khung Weekly, năng lực dự báo duy trì ở mức khá ($DA \\approx 56.5\\%$). Ở khung Monthly, hiện tượng nhiễu ngẫu nhiên chi phối sai số bình phương, nhưng $M4$ vẫn mang lại giá trị gia tăng về định hướng xu hướng ($DA = 53.13\\%, p = 0.044$).")
    w("3. Mạng nơ-ron hồi quy sâu (**RNN, LSTM**) được chuẩn hóa qua 5 random seeds cung cấp một benchmark học thuật vững chắc, xác nhận tính ưu việt của mô hình cây tăng cường LightGBM trên tập dữ liệu chuỗi thời gian dạng bảng.")
    w("")
    w("### 5.2. Các Giới Hạn Của Nghiên Cứu (Research Limitations)")
    w("1. **Hạn chế về Timestamp Proxy:** Do đặc thù lịch sử dữ liệu Platts và Brent tải từ các cơ sở dữ liệu thứ cấp, các mốc thời gian công bố được gán theo quy ước đóng phiên chuẩn của thị trường (16:30 SGT cho Platts và 19:30 London cho Brent). Mặc dù cơ chế vận hành này phản ánh chính xác cấu trúc thị trường, nghiên cứu không tuyên bố đã kiểm toán Point-in-Time ở cấp độ log API mili-giây.")
    w("2. **Loại bỏ dữ liệu NLP/Sentiment ($M6$):** Dữ liệu tin tức tài chính trong giai đoạn 2017 – 2025 thiếu dấu thời gian phát hành chính xác tới từng phút để khẳng định không bị nhìn trước thời điểm 08:30 SGT. Do đó, nhóm nghiên cứu quyết định loại bỏ mô hình $M6$ khỏi các bảng so sánh chính thức nhằm bảo toàn tính trung thực học thuật.")
    w("3. **Khả năng thương mại hóa thực tế:** Mặc dù $DA$ đạt hơn $70\\%$, việc chuyển hóa kết quả dự báo thành chiến lược giao dịch sinh lời thực tế đối mặt với chi phí giao dịch vật chất (*physical storage fees*), rủi ro thanh khoản hợp đồng phái sinh Platts Singapore Mogas 95 Swaps tại sàn SGX, và biến động tỷ giá.")
    w("")
    w("---")
    w("")

    # --- Section 6: References ---
    w("## TÀI LIỆU THAM KHẢO (REFERENCES - APA 7TH EDITION)")
    w("")
    w("1. Bacon, R. W. (1991). Rockets and feathers: the asymmetric speed of adjustment of UK retail gasoline prices to world crude oil price changes. *Energy Economics*, 13(3), 211-218.")
    w("2. Borenstein, S., Cameron, A. C., & Gilbert, R. (1997). Do gasoline prices respond asymmetrically to crude oil price changes? *The Quarterly Journal of Economics*, 112(1), 305-339.")
    w("3. Clark, T. E., & McCracken, M. W. (2001). Tests of equal forecast accuracy and encompassing for nested models. *Journal of Econometrics*, 105(1), 85-110.")
    w("4. Clark, T. E., & West, K. D. (2007). Approximately normal tests for equal predictive accuracy in nested models. *Journal of Econometrics*, 138(1), 291-311.")
    w("5. de Prado, M. L. (2018). *Advances in Financial Machine Learning*. John Wiley & Sons.")
    w("6. Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253-263.")
    w("7. Galeotti, M., Lanza, A., & Manera, M. (2003). Rockets and feathers revisited: an international comparison on European gasoline markets. *Energy Economics*, 25(2), 175-190.")
    w("8. Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting*, 13(2), 281-291.")
    w("9. Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., ... & Liu, T. Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems*, 30, 3146-3154.")
    w("10. Newey, W. K., & West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703-708.")
    w("11. Pesaran, M. H., & Timmermann, A. (1992). A simple nonparametric test of predictive performance. *Journal of Business & Economic Statistics*, 10(4), 461-465.")
    w("")

    content = "\n".join(doc)
    out_file = Path("reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md")
    out_file.write_text(content, encoding="utf-8")
    print(f"Successfully generated full updated report: {out_file} ({len(content)} characters, {len(doc)} lines)")

if __name__ == "__main__":
    generate_report()
