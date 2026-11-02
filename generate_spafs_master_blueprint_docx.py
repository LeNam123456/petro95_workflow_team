# -*- coding: utf-8 -*-
"""Generate Authoritative Master Research Document for SPAFS V5.2.

Covers all 6 Tasks:
- Task 1: Comprehensive Executive Summary of SPAFS V5.2.
- Task 2: 4-State Work Classification Table.
- Task 3: In-depth Technical & Research Threats to Validity (Target, Overlapping, Purging, PIT, Common OOS).
- Task 4: Prioritized Dependency Checklist.
- Task 5: 14-Day Actionable Implementation Roadmap with concrete outputs.
- Task 6: Required Files & Artifacts Checklist for Instructor / Advisor Verification.
"""

import os
import re
import sys
from pathlib import Path

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

sys.stdout.reconfigure(encoding="utf-8")

output_docx_downloads = Path("C:/Users/LeeNam/Downloads/SPAFS_V5_2_Master_Research_Plan_and_Audit.docx")
output_docx_workspace = Path("reports/SPAFS_V5_2_Master_Research_Plan_and_Audit.docx")

doc = Document()

# Set margins to 1 inch
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Configure default font
style = doc.styles["Normal"]
font = style.font
font.name = "Times New Roman"
font.size = Pt(11)
font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def sanitize_text(text: str) -> str:
    """Remove invalid XML control characters."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text))


def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def add_title(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(sanitize_text(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x2B, 0x49)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_subtitle(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(14)
    run = p.add_run(sanitize_text(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(13)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_heading_1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(sanitize_text(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x33, 0x66)


def add_heading_2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(sanitize_text(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(12.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)


def add_heading_3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(sanitize_text(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


def add_paragraph(text, bold_prefix="", italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(sanitize_text(bold_prefix))
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    r = p.add_run(sanitize_text(text))
    r.italic = italic
    return p


def add_bullet(text, bold_prefix=""):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(sanitize_text(bold_prefix))
        r_pre.bold = True
    p.add_run(sanitize_text(text))
    return p


def add_callout(title, text, alert_type="NOTE"):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.right_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    r_tag = p.add_run(f"[{alert_type}] {title}\n")
    r_tag.bold = True
    if alert_type == "WARNING" or alert_type == "CAUTION":
        r_tag.font.color.rgb = RGBColor(0xB9, 0x1C, 0x1C)
    elif alert_type == "IMPORTANT":
        r_tag.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    else:
        r_tag.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)
    r_text = p.add_run(sanitize_text(text))
    r_text.italic = True


def add_table_data(headers, rows_data):
    num_rows = len(rows_data) + 1
    num_cols = len(headers)
    tbl = doc.add_table(rows=num_rows, cols=num_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl)

    # Headers
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(sanitize_text(h))
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_background(cell, "003366")

    # Data rows
    for r_idx, row in enumerate(rows_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx + 1, c_idx)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(sanitize_text(str(val)))
            run.font.size = Pt(9.0)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            else:
                set_cell_background(cell, "FFFFFF")
            if c_idx == 0:
                run.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ==============================================================================
# DOCUMENT GENERATION
# ==============================================================================

# Cover & Title
add_title("BÁO CÁO TỔNG QUAN KHOA HỌC & KẾ HOẠCH NGHIÊN CỨU TOÀN DIỆN")
add_subtitle("Hệ thống Dự báo Giá Xăng Platts FOB Singapore Mogas 95 với Ba Khung Thời gian Daily – Weekly – Monthly (SPAFS V5.2)")

add_paragraph(
    "Tài liệu này được biên soạn bởi vai trò Trợ lý Nghiên cứu Khoa học (Research Assistant) "
    "nhằm đáp ứng trọn vẹn yêu cầu định hướng đề tài, chuẩn hóa phương pháp luận kinh tế lượng & học máy, "
    "kiểm toán dữ liệu độc lập, phân định rạch ròi các trạng thái nghiên cứu và lập lộ trình 14 ngày "
    "hoàn thiện bài báo khoa học (Research Paper) gửi hội đồng học thuật.",
    bold_prefix="Bối cảnh & Tôn chỉ Nghiên cứu: "
)

add_callout(
    "NGUYÊN TẮC HỌC THUẬT BẤT DI BẤT DỊCH (ACADEMIC GROUND RULES)",
    "1. Tuyệt đối không tự ý bịa kết quả, số liệu, độ đo hay citation.\n"
    "2. Không mặc định những số liệu cũ là chính xác khi chưa chạy lại kịch bản kiểm chứng độc lập.\n"
    "3. Không kết luận một mô hình tốt hơn toàn diện nếu chưa có kiểm định thống kê chính quy và phân tích đánh đổi đa mục tiêu.\n"
    "4. Bóc tách minh bạch giữa timestamp proxy quy ước thị trường và log tick vật lý thời gian thực.\n"
    "5. Kiểm soát chặt chẽ rò rỉ thông tin (Lookahead Leakage) do cửa sổ mục tiêu chồng lấn (Overlapping Horizons).",
    alert_type="CAUTION"
)

# ------------------------------------------------------------------------------
# TASK 1: SUMMARY OF SPAFS
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 1: TÓM TẮT TOÀN DIỆN DỰ ÁN NGHIÊN CỨU SPAFS V5.2")

add_heading_2("1.1. Tên đề tài & Mục tiêu Nghiên cứu Cốt lõi")
add_paragraph(
    "Forecasting the Return and Direction of Platts FOB Singapore Mogas 95 Prices: "
    "A Multi-Horizon Econometric and Machine Learning Framework (SPAFS V5.2).",
    bold_prefix="Tên đề tài chính thức: "
)
add_paragraph(
    "Nghiên cứu tập trung giải quyết hai câu hỏi khoa học nền tảng cùng một định hướng mở rộng đa khung thời gian:",
    bold_prefix="Ba Mục tiêu Nghiên cứu: "
)
add_bullet("Phân tích cơ chế truyền dẫn biến động từ giá dầu thô chuẩn quốc tế (ICE Brent Futures) sang giá xăng thành phẩm bán buôn tại Singapore (Platts FOB Singapore Mogas 95), kiểm tra khả năng tồn tại phản ứng bất đối xứng giữa các cú sốc chi phí tăng và giảm (Kiểm định giả thuyết 'Tên lửa và Lông vũ' - Rockets and Feathers).", bold_prefix="Mục tiêu 1 (RQ1 - Econometric Inference): ")
add_bullet("Đánh giá xem việc tích hợp các đặc trưng kinh tế học lọc dầu hạ nguồn (Refining Economics: Gasoline Crack Spread, Octane Quality Premium 95/92, Gasoil/Diesel Substitution Margin) có mang lại giá trị thông tin dự báo gia tăng vượt trội so với các chỉ báo kỹ thuật động lượng thuần túy (Technical Momentum Features) hay không.", bold_prefix="Mục tiêu 2 (RQ2 - Predictive Incremental Value): ")
add_bullet("Mở rộng kiến trúc dự báo cuốn chiếu (Rolling-Origin Forecasting) đồng thời trên 3 khung thời gian theo yêu cầu mới của giảng viên: Daily (1 ngày, h=1), Weekly (1 tuần, h=5), và Monthly (1 tháng, h=21 phiên giao dịch).", bold_prefix="Mục tiêu 3 (Multi-Horizon Extension): ")

add_heading_2("1.2. Dữ liệu & Quy tắc Thời gian Point-in-Time (PIT Control Plane)")
add_bullet("Platts FOB Singapore Mogas 95 (MG95): Dữ liệu giá giao dịch giao ngay hàng rời tại cảng Singapore, thời điểm chốt giá thị trường (Market-on-Close) ghi nhận khoảng 16:30 giờ Singapore (SGT).", bold_prefix="Chuỗi giá xăng mục tiêu: ")
add_bullet("ICE Brent Crude Oil Futures (BZ=F): Biến đại diện cho chi phí đầu vào lọc dầu toàn cầu, thời điểm thanh toán phiên tại sàn London khoảng 19:30 giờ London, tương đương 02:30–03:30 SGT sáng ngày hôm sau.", bold_prefix="Chuỗi giá dầu thô: ")
add_bullet("Mốc đóng băng thông tin cố định lúc 08:30 SGT sáng ngày t+1. Toàn bộ đặc trưng đưa vào mô hình phải sẵn sàng trước 08:30 SGT, dẫn trước thời điểm đóng phiên thực tế của Platts chiều hôm đó (16:30 SGT) đúng 8.0 giờ giao dịch.", bold_prefix="Mốc Cutoff Dự báo: ")
add_bullet("Dữ liệu lịch sử cuối ngày (EOD) sử dụng các mốc giờ quy chuẩn theo phiên giao dịch của sàn (16:30 SGT Platts, 03:30 SGT Brent, 08:30 SGT Cutoff). Mặc dù toàn bộ 2,255 bản ghi Stream 2 đều đạt 100% tuân thủ quy tắc logic nội nhật, nghiên cứu không tuyên bố đã xác minh log tick thời gian thực từ máy chủ phân phối feed.", bold_prefix="Minh bạch Timestamp Proxy: ")

add_heading_2("1.3. Câu hỏi Nghiên cứu & Chuẩn mực Kết luận Thống kê")
add_paragraph(
    "Does Brent price transmission to Singapore Mogas 95 exhibit asymmetric responses to positive and negative shocks? "
    "Mô hình đối chiếu: M2 (Linear Dynamic ADL) và M3 (Asymmetric Dynamic ADL). "
    "Bộ 3 kiểm định Wald Newey-West HAC trên mẫu 17.5 năm (N = 4,425 phiên) ghi nhận p-value lần lượt là 0.9530 (tức thời), 0.6360 (tích lũy 2 ngày), và 0.8833 (ràng buộc chung). Kiểm định ngoài mẫu Clark-West ghi nhận CW = -0.3436 (p = 0.6344). "
    "Kết luận học thuật chuẩn mực: Các kiểm định hiện tại chưa cung cấp đủ bằng chứng thống kê để bác bỏ giả thuyết đối xứng theo đặc tả nghiên cứu; mô hình đối xứng M2 vẫn là đặc tả phù hợp và tiết kiệm tham số hơn.",
    bold_prefix="Câu hỏi RQ1: "
)
add_paragraph(
    "Do refining economics features provide additional predictive value beyond technical features in forecasting Mogas 95 price returns and directions? "
    "Mô hình đối chiếu: M4 (Technical LightGBM, 10 biến) và M5 (Economic LightGBM, 15 biến) trên mẫu ngoài OOS 754 phiên chung. "
    "Kết quả kiểm định lồng ghép Clark & West (2007) đạt CW = +1.9688 (p = 0.0245 < 0.05), bác bỏ giả thuyết vô hiệu H0 ở mức 5%. "
    "Tuy nhiên, kiểm định Diebold-Mariano với MSE ghi nhận DM = -0.7748 (p = 0.2194, không bác bỏ ở 5% do DM bị chệch âm khi lồng nhau). "
    "Về đa tiêu chí: M5 đạt sai số biên độ thấp hơn (RMSE 1.4163% vs 1.4221%; MAE 1.0643% vs 1.0712%), trong khi M4 nhỉnh hơn về độ chính xác định hướng (DA 70.82% vs 70.42%) và hệ số Matthews (MCC 0.4156 vs 0.4078). "
    "Kết luận học thuật chuẩn mực: Không kết luận M5 tốt hơn toàn diện trên mọi tiêu chí, mà tồn tại sự đánh đổi giữa kiểm soát tổn thất biên độ và tỷ lệ đoán đúng hướng.",
    bold_prefix="Câu hỏi RQ2: "
)

add_heading_2("1.4. Hệ thống Mô hình Dự báo Phân tầng (Model Framework)")
add_bullet("M0a: Naive Zero Return Benchmark (Dự báo tỷ suất sinh lời bằng 0, mỏ neo cơ sở).", bold_prefix="Mô hình Đối chứng Cơ sở: ")
add_bullet("M0b: Naive Directional Benchmark (Dự báo dấu biến động, cần xác minh rõ mã nguồn xem sử dụng sign của lag1 hay running mean).", bold_prefix="Mô hình Đối chứng Chiều hướng: ")
add_bullet("M1: ARMA(1,1) đơn biến (Động lượng chuỗi thời gian nội sinh thuần túy).", bold_prefix="Mô hình Chuỗi Thời gian: ")
add_bullet("M2: Linear Dynamic Autoregressive Distributed Lag (Tuyến tính đối xứng, 5 biến).", bold_prefix="Mô hình Kinh tế lượng Tuyến tính: ")
add_bullet("M3: Asymmetric Dynamic ADL (Tách biệt cú sốc Brent dương/âm, 7 biến).", bold_prefix="Mô hình Kinh tế lượng Bất đối xứng: ")
add_bullet("M4: Technical LightGBM Ensemble (Phi tuyến tính, 10 biến kỹ thuật & chế độ biến động).", bold_prefix="Mô hình Học máy Kỹ thuật: ")
add_bullet("M5: Economic Refining LightGBM Ensemble (15 biến: 10 biến M4 + 5 biến biên lọc dầu hạ nguồn).", bold_prefix="Mô hình Học máy Kinh tế: ")
add_bullet("RNN & LSTM: Hai mô hình học sâu chuỗi thời gian (Deep Sequence Models) được bổ sung như nhóm đối chuẩn benchmark hiện đại.", bold_prefix="Mô hình Học sâu Bổ sung: ")
add_bullet("M6 (Multimodal News Sentiment): Để ở phần Thảo luận Mở rộng Tương lai (Future Work), không đưa vào bảng kết quả chính thức do chưa có dự báo OOS cùng kỳ được kiểm chứng.", bold_prefix="Mô hình Tin tức NLP: ")

# ------------------------------------------------------------------------------
# TASK 2: 4-STATE CLASSIFICATION TABLE
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 2: BẢNG PHÂN LOẠI CÔNG VIỆC THEO BỐN TRẠNG THÁI MINH BẠCH")

headers_task2 = ["STT", "Hạng mục Công việc", "Trạng thái", "Chi tiết Kỹ thuật Hiện tại", "Bằng chứng / File Đối chiếu"]
rows_task2 = [
    [
        "1",
        "Tiền xử lý chuỗi giá Platts & Brent, lịch giao dịch",
        "ĐÃ THỰC HIỆN",
        "Đồng bộ hóa 2008–2025, xử lý 129 ngày nghỉ lễ, forward-fill giá trị gần nhất hợp lệ.",
        "data/processed/stream1_econometric_2008_2025.parquet"
    ],
    [
        "2",
        "Kiểm toán PIT Invariants cấp bản ghi trên Stream 2",
        "ĐÃ THỰC HIỆN",
        "2,255 bản ghi đạt 100% tuân thủ quy tắc thời gian logic nội nhật dựa trên market proxies.",
        "stream2_record_level_pit_audit.json"
    ],
    [
        "3",
        "Ước lượng M2, M3 và kiểm định Wald trong mẫu (RQ1)",
        "ĐÃ THỰC HIỆN",
        "Bộ 3 kiểm định Wald Newey-West 5 lags trên 4,425 phiên; không bác bỏ giả thuyết đối xứng.",
        "01_run_m3_asymmetric_adl_and_wald_test.py, rq1_wald_tests.json"
    ],
    [
        "4",
        "Huấn luyện Walk-Forward M4, M5 Daily (754 OOS)",
        "ĐÃ THỰC HIỆN",
        "Expanding window (tau_0=1500, refit=20 ngày, 10 seeds). M4 RMSE 1.4221, M5 RMSE 1.4163.",
        "pred_M4_stream2.parquet, pred_M5_stream2.parquet"
    ],
    [
        "5",
        "Kiểm định Clark-West & Diebold-Mariano M5 vs M4 Daily",
        "ĐÃ THỰC HIỆN",
        "Clark-West CW=+1.9688 (p=0.0245); DM MSE stat=-0.7748 (p=0.2194); DM MAE stat=-1.3088 (p=0.0955).",
        "run_reproducible_clark_west_dm.py, reproducible_statistical_tests.json"
    ],
    [
        "6",
        "Đóng gói 7 file dự báo OOS và tạo CSV 754 ngày chung",
        "ĐÃ THỰC HIỆN",
        "Xuất file CSV chứa dự báo và phần dư của cả 7 mô hình M0a..M5 trên 754 phiên OOS.",
        "out_of_sample_predictions_all_7_models_harmonized_754.csv"
    ],
    [
        "7",
        "Xác minh định nghĩa hình thức và mã nguồn mô hình M0b",
        "CẦN XÁC MINH",
        "Kiểm tra xem M0b dự báo continuous return hay binary sign, và cách tính sai số trong leaderboard.",
        "src/models/econometric/naive.py, runner_econometric.py"
    ],
    [
        "8",
        "Thống kê mô tả log return và kiểm định tính dừng (ADF/PP)",
        "CẦN XÁC MINH",
        "Cần tính lại chính xác mean, std, skewness, kurtosis, Jarque-Bera từ file canonical cuối cùng.",
        "stream1_econometric_2008_2025.parquet"
    ],
    [
        "9",
        "Tính ổn định tham số siêu mô hình LightGBM (Tuning vs Fixed)",
        "CẦN XÁC MINH",
        "Kiểm tra tham số leaves=15, lr=0.03 có bị overfitting hay phụ thuộc vào validation split.",
        "src/models/ml/lgbm.py"
    ],
    [
        "10",
        "Định nghĩa hình thức cho Weekly (h=5) và Monthly (h=21)",
        "ĐANG ĐỀ XUẤT",
        "Đề xuất tính theo số phiên giao dịch rolling: y(t,5) và y(t,21) log returns tích lũy.",
        "Chờ xác nhận chính thức từ giảng viên hướng dẫn"
    ],
    [
        "11",
        "Kiến trúc Purging và Embargo cho target chồng lấn",
        "ĐANG ĐỀ XUẤT",
        "Thiết lập khoảng trống an toàn gap >= 5 phiên (Weekly) và gap >= 21 phiên (Monthly).",
        "Thiết kế phương pháp luận mục 13"
    ],
    [
        "12",
        "Kiến trúc Sequence Models RNN và LSTM đơn mục tiêu",
        "ĐANG ĐỀ XUẤT",
        "Đề xuất mô hình riêng cho từng horizon, lookback 20–30 ngày, fit scaler trên Train only.",
        "Thiết kế phương pháp luận mục 14"
    ],
    [
        "13",
        "Tạo dataset và chia split Purged/Embargoed cho 3 horizons",
        "CHƯA THỰC HIỆN",
        "Chưa viết code tạo target rolling cho h=5 và h=21, chưa tạo manifest split có purge.",
        "Cần triển khai ở Giai đoạn 2"
    ],
    [
        "14",
        "Chạy hồi quy M0..M5 trên khung Weekly và Monthly",
        "CHƯA THỰC HIỆN",
        "Chưa có chuỗi dự báo ngoài mẫu cho M0..M5 ở khung h=5 và h=21.",
        "Cần triển khai ở Giai đoạn 3"
    ],
    [
        "15",
        "Huấn luyện, tuning và checkpointing cho RNN & LSTM",
        "CHƯA THỰC HIỆN",
        "Chưa lập trình pipeline huấn luyện PyTorch/TensorFlow, chưa lưu epoch loss và checkpoints.",
        "Cần triển khai ở Giai đoạn 3"
    ],
    [
        "16",
        "Kiểm định Newey-West HAC hiệu chỉnh lag cho forecast errors h>1",
        "CHƯA THỰC HIỆN",
        "Cần áp dụng bandwidth q >= h-1 để khắc phục tự tương quan sai số do target chồng lấn.",
        "Cần triển khai ở Giai đoạn 4"
    ],
    [
        "17",
        "Phân tích lỗi chuyên sâu (Error Analysis) và Robustness checks",
        "CHƯA THỰC HIỆN",
        "Chưa mổ xẻ các ngày dự báo sai lớn nhất, giai đoạn sốc địa chính trị và seed stability.",
        "Cần triển khai ở Giai đoạn 4"
    ],
    [
        "18",
        "Tích hợp mô hình NLP M6 (FinBERT Sentiment)",
        "CHƯA THỰC HIỆN",
        "Dữ liệu tin tức chưa có dự báo OOS cùng kỳ hoàn chỉnh; để lại cho Future Work.",
        "Định hướng bài báo khoa học"
    ]
]
add_table_data(headers_task2, rows_task2)

# ------------------------------------------------------------------------------
# TASK 3: TECHNICAL THREATS TO VALIDITY
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 3: CÁC VẤN ĐỀ KỸ THUẬT & NGHIÊN CỨU ẢNH HƯỞNG TÍNH HỢP LỆ")

add_heading_2("3.1. Vấn đề Định nghĩa Target (Target Construction) & Phiên Giao dịch vs Lịch")
add_paragraph(
    "Khi mở rộng sang Weekly và Monthly, sự khác biệt giữa phiên giao dịch (Trading Days) và ngày lịch (Calendar Days) "
    "ảnh hưởng trực tiếp đến tính nhất quán toán học của biến mục tiêu:",
    bold_prefix="Bản chất Kỹ thuật: "
)
add_bullet("Tuần giao dịch thực tế thường có 5 phiên (từ Thứ Hai đến Thứ Sáu), nhưng nếu có ngày nghỉ lễ (Singapore National Day, Chinese New Year, Good Friday), tuần đó chỉ có 3 hoặc 4 phiên. Do đó, định nghĩa target tích lũy 5 phiên giao dịch: y(t, 5) = ln(P_{t+5} / P_t) sẽ đại diện cho đúng thời lượng nắm giữ vị thế của thương nhân, nhưng ngày t+5 có thể rơi sang Thứ Hai hoặc Thứ Ba của tuần kế tiếp.", bold_prefix="Weekly Target: ")
add_bullet("Tương tự, 1 tháng giao dịch quy ước trung bình gồm 21 phiên: y(t, 21) = ln(P_{t+21} / P_t). Nếu định nghĩa theo tháng lịch (Calendar Month-End), số phiên trong tháng dao động từ 19 đến 23 phiên, gây ra sự biến thiên phương sai nhân tạo (heteroskedasticity).", bold_prefix="Monthly Target: ")
add_paragraph(
    "Kiến nghị lựa chọn định nghĩa thống nhất theo số phiên giao dịch rolling: Daily (h=1), Weekly (h=5), Monthly (h=21). "
    "Bắt buộc phải lưu trữ đồng thời hai cột thời gian: forecast_origin_date (ngày phát tín hiệu) và target_realization_date (ngày kết thúc vị thế để so sánh giá).",
    bold_prefix="Khuyến nghị Nghiên cứu: "
)

add_heading_2("3.2. Cửa sổ Dự báo Chồng lấn (Overlapping Horizons) & Tự tương quan Sai số")
add_paragraph(
    "Trong thiết kế Rolling-Origin dự báo hằng ngày cho horizon h > 1, cửa sổ thời gian mục tiêu [t, t+h] của phiên hôm nay "
    "sẽ chồng lấn với cửa sổ [t+1, t+1+h] của phiên ngày mai một khoảng thời gian bằng h - 1 phiên.",
    bold_prefix="Cơ chế Gây nhiễu: "
)
add_bullet("Theo định lý cổ điển của Hansen & Hodrick (1980) và Brown & Maital (1981), ngay cả khi mô hình dự báo là hoàn hảo và không bị thiên lệch, chuỗi phần dư dự báo e_{t+h} bắt buộc phải có cấu trúc tự tương quan ít nhất là bậc MA(h - 1).", bold_prefix="Hệ quả Kinh tế lượng: ")
add_bullet("Với Daily (h=1), h-1 = 0 nên phần dư không bị tự tương quan chồng lấn. Nhưng với Weekly (h=5), phần dư có tự tương quan MA(4); và với Monthly (h=21), phần dư có tự tương quan MA(20).", bold_prefix="Độ trễ MA: ")
add_bullet("Nếu sử dụng kiểm định Diebold-Mariano hoặc OLS chuẩn mà không hiệu chỉnh ma trận hiệp phương sai nhất quán Newey-West HAC với số độ trễ tối thiểu q >= h - 1, sai số chuẩn của thống kê kiểm định sẽ bị đánh giá thấp nghiêm trọng, thổi phồng thống kê t và dẫn đến kết luận có ý nghĩa thống kê giả tạo (Type I Error).", bold_prefix="Rủi ro Nghiên cứu: ")

add_heading_2("3.3. Rò rỉ Dữ liệu Ranh giới & Cơ chế Purging / Embargoing")
add_paragraph(
    "Khi chia tập dữ liệu thành Train, Validation và Test để huấn luyện các mô hình Machine Learning hoặc Deep Learning, "
    "các mẫu quan sát ở cuối tập Train sẽ có target window kéo dài sang tập Validation:",
    bold_prefix="Nguy cơ Data Leakage: "
)
add_bullet("Purging (Thanh lọc ranh giới): Bắt buộc phải loại bỏ khỏi tập Train bất kỳ quan sát t nào có target_realization_date vượt qua ngày bắt đầu của tập Validation. Đối với Monthly (h=21), phải cắt bỏ đúng 21 quan sát cuối cùng của tập Train.", bold_prefix="Quy tắc Purging: ")
add_bullet("Embargoing (Khoảng đệm sau ranh giới): Do chuỗi lợi suất và đặc trưng kỹ thuật có tính tự tương quan (volatility clustering), cần tạo thêm một khoảng đệm an toàn sau khi kết thúc tập Train (ví dụ 5 phiên) trước khi bắt đầu lấy mẫu Validation.", bold_prefix="Quy tắc Embargoing: ")
add_bullet("Tất cả các bộ tiền xử lý (StandardScaler, RobustScaler, Imputer) bắt buộc phải được fit CHỈ trên tập Train đã được purge, sau đó dùng transform trên Validation và Test. Nghiêm cấm fit scaler trên toàn bộ dataset.", bold_prefix="Chuẩn hóa Dữ liệu: ")

add_heading_2("3.4. Giới hạn Kiểm toán Point-in-Time (PIT Audit Caveats)")
add_paragraph(
    "Dự án đã thiết lập quy trình kiểm toán 4 điều kiện bất biến (Invariants) trên 2,255 bản ghi Stream 2. "
    "Tuy nhiên, để bảo vệ tính trung thực học thuật trước hội đồng:",
    bold_prefix="Tuyên bố Minh bạch Cần thiết: "
)
add_bullet("100% các timestamp nội nhật (16:30 SGT Platts, 03:30 SGT Brent, 08:30 SGT Cutoff) là Proxy quy chuẩn theo quy ước hoạt động của thị trường hàng hóa.", bold_prefix="Bản chất Timestamp: ")
add_bullet("Dữ liệu lịch sử cuối ngày EOD không lưu trữ log tick nhận gói tin vật lý từ máy chủ API feed. Do đó, nghiên cứu khẳng định không vi phạm quy tắc logic theo proxy, nhưng KHÔNG TUYÊN BỐ đã loại trừ tuyệt đối lookahead bias ở cấp độ nano-giây hoặc log tick thực tế.", bold_prefix="Giới hạn Báo cáo: ")

add_heading_2("3.5. Tính Nhất quán của Tập Mẫu Ngoài Mẫu Chung (Common OOS Horizon)")
add_paragraph(
    "Một sai lầm phổ biến trong các nghiên cứu so sánh mô hình là đối chiếu metrics trên các tập ngày khác nhau:",
    bold_prefix="Nguyên tắc So sánh Công bằng: "
)
add_bullet("Mỗi khung thời gian (Daily, Weekly, Monthly) phải xây dựng một Common OOS Index riêng biệt. Tất cả các mô hình tham gia so sánh trong khung thời gian đó (từ M0a đến LSTM) phải được đánh giá trên cùng một tập các ngày forecast origin chính xác.", bold_prefix="Common Index theo Horizon: ")
add_bullet("Do Weekly mất h=5 phiên cuối và Monthly mất h=21 phiên cuối vì thiếu dữ liệu thực tế tương lai để tính target, số lượng mẫu OOS của Daily (754 phiên) sẽ lớn hơn số lượng mẫu OOS của Weekly (~750 phiên) và Monthly (~734 phiên). Điều này hoàn toàn tự nhiên và phải được giải trình rõ trong bài báo.", bold_prefix="Quy mô Mẫu Khác nhau: ")

# ------------------------------------------------------------------------------
# TASK 4: PRIORITIZED CHECKLIST
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 4: CHECKLIST CHI TIẾT TẤT CẢ VIỆC CẦN LÀM THEO THỨ TỰ ƯU TIÊN")

headers_task4 = ["Ưu tiên", "Giai đoạn", "Nhiệm vụ Cụ thể", "Phụ thuộc vào", "Tiêu chuẩn Nghiệm thu (Acceptance Criteria)"]
rows_task4 = [
    [
        "P0 (Khẩn cấp)",
        "Giai đoạn 1",
        "Xác nhận chính thức định nghĩa Weekly/Monthly với GV",
        "Ý kiến GVHD",
        "Văn bản chốt: số phiên (5/21) hay lịch, phạm vi mô hình và output."
    ],
    [
        "P0 (Khẩn cấp)",
        "Giai đoạn 1",
        "Xác minh và chuẩn hóa mã nguồn mô hình M0b",
        "Code hiện có",
        "Xác định rõ M0b dự báo return hay direction, khớp 100% giữa code và report."
    ],
    [
        "P0 (Khẩn cấp)",
        "Giai đoạn 1",
        "Khóa dữ liệu Canonical Panel & Thống kê mô tả",
        "data/processed",
        "Tạo tệp data_audit_summary.json ghi nhận đúng số dòng, missing=0, ADF test."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 2",
        "Xây dựng module Target Rolling h=1, h=5, h=21",
        "Giai đoạn 1",
        "Tạo ra 3 cột target riêng biệt kèm ngày origin và ngày realization."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 2",
        "Thiết lập cơ chế Purging & Embargoing cho 3 horizons",
        "Target module",
        "Kiểm tra không có bất kỳ target nào của Train đè sang Validation/Test."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 2",
        "Xác định Common OOS Dates riêng cho từng horizon",
        "Splits",
        "Lưu 3 tệp common_oos_dates_daily.parquet, weekly.parquet, monthly.parquet."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 3",
        "Ước lượng M0a..M5 cho Daily trên Common OOS (N=754)",
        "Giai đoạn 2",
        "Tái lập 100% metrics RMSE, MAE, DA, MCC và lưu prediction CSV."
    ],
    [
        "P2 (Mở rộng)",
        "Giai đoạn 3",
        "Ước lượng M0a..M5 cho Weekly (h=5) trên Common OOS",
        "Giai đoạn 2",
        "Lưu file pred_M0_M5_weekly.parquet, metrics leaderboard riêng."
    ],
    [
        "P2 (Mở rộng)",
        "Giai đoạn 3",
        "Ước lượng M0a..M5 cho Monthly (h=21) trên Common OOS",
        "Giai đoạn 2",
        "Lưu file pred_M0_M5_monthly.parquet, metrics leaderboard riêng."
    ],
    [
        "P2 (Mở rộng)",
        "Giai đoạn 3",
        "Lập trình & Huấn luyện RNN Benchmark trên 3 horizons",
        "Giai đoạn 2",
        "Lưu training loss, val loss per epoch, best checkpoint, seed variance."
    ],
    [
        "P2 (Mở rộng)",
        "Giai đoạn 3",
        "Lập trình & Huấn luyện LSTM Benchmark trên 3 horizons",
        "Giai đoạn 2",
        "Lưu training loss, val loss per epoch, best checkpoint, seed variance."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 4",
        "Kiểm định Clark-West & Diebold-Mariano với HAC hiệu chỉnh",
        "Predictions",
        "Áp dụng Newey-West lag q >= h-1 cho Weekly và Monthly. Xuất JSON chính quy."
    ],
    [
        "P2 (Mở rộng)",
        "Giai đoạn 4",
        "Thực hiện Phân tích Lỗi (Error Analysis) & Robustness",
        "Predictions",
        "Phân tích top 5% ngày sai lớn nhất, regime analysis, feature importance."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 5",
        "Soạn thảo Research Paper hoàn chỉnh theo chuẩn IEEE/Elsevier",
        "Kết quả GĐ 1-4",
        "Cấu trúc 8 phần học thuật, biểu đồ KaTeX, bảng biểu không có ô trống."
    ],
    [
        "P1 (Cốt lõi)",
        "Giai đoạn 5",
        "Đóng gói Deliverables Package & Lệnh tái lập 1-dòng",
        "Paper & Code",
        "Tệp ZIP chứa đầy đủ mã nguồn, dữ liệu, checkpoint và hướng dẫn tái lập."
    ]
]
add_table_data(headers_task4, rows_task4)

# ------------------------------------------------------------------------------
# TASK 5: 14-DAY ACTIONABLE IMPLEMENTATION ROADMAP
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 5: ĐỀ XUẤT KẾ HOẠCH TRIỂN KHAI THỰC TẾ TRONG 14 NGÀY")

add_paragraph(
    "Lộ trình 14 ngày được thiết kế cân bằng giữa tính khả thi và tính chặt chẽ học thuật, "
    "đảm bảo các mô hình cốt lõi (M0–M5) và kiểm định thống kê được hoàn tất vững chắc trước khi mở rộng Deep Learning:",
    bold_prefix="Nguyên tắc Phân bổ Lộ trình: "
)

headers_task5 = ["Ngày", "Trọng tâm Công việc", "Nội dung Thực hiện Chi tiết", "Đầu ra Cụ thể (Deliverables / Outputs)"]
rows_task5 = [
    [
        "Ngày 1",
        "Kiểm toán Dữ liệu, Mã nguồn & Chốt Quy chuẩn",
        "Kiểm toán canonical dataset 2008–2025; làm rõ định nghĩa M0b; gửi email xác nhận với giảng viên về Weekly (5 phiên) và Monthly (21 phiên); kiểm tra ADF test.",
        "data_audit_report.json, tài liệu xác nhận định nghĩa M0b và horizon."
    ],
    [
        "Ngày 2",
        "Kỹ nghệ Target Đa khung thời gian & Purged Splits",
        "Viết hàm tạo rolling target h=1, h=5, h=21; lập trình cơ chế Purging và Embargo tại ranh giới Train/Val/Test; tạo 3 bộ index Common OOS riêng biệt.",
        "multi_horizon_targets.parquet, split_manifest_purged.json, 3 tệp common_oos_dates."
    ],
    [
        "Ngày 3",
        "Huấn luyện & Dự báo Khung Daily (M0a đến M5)",
        "Chạy lại toàn bộ M0a, M0b, M1, M2, M3, M4, M5 cho Daily trên 754 phiên OOS; trích xuất feature importance của M5; kiểm tra tính đồng bộ 100%.",
        "pred_daily_all_models.csv, daily_metrics_leaderboard.json."
    ],
    [
        "Ngày 4",
        "Kiểm định Thống kê Khung Daily (RQ1 & RQ2)",
        "Chạy kiểm định Clark-West và Diebold-Mariano cho Daily; kiểm định Wald M2 vs M3; tạo biểu đồ phân tán sai số và lưu kết quả JSON chính quy.",
        "daily_statistical_tests.json, rq1_rq2_daily_summary.csv."
    ],
    [
        "Ngày 5",
        "Huấn luyện & Dự báo Khung Weekly (h=5)",
        "Chạy mô hình kinh tế lượng (M0a, M2, M3) và Machine Learning (M4, M5) trên target tích lũy 5 phiên; walk-forward refit định kỳ; xuất dự báo ngoài mẫu.",
        "pred_weekly_all_models.csv, weekly_metrics_leaderboard.json."
    ],
    [
        "Ngày 6",
        "Kiểm định Thống kê Khung Weekly với Newey-West HAC",
        "Chạy Clark-West và Diebold-Mariano cho Weekly với độ trễ HAC q >= 4 nhằm triệt tiêu tự tương quan MA(4); đánh giá tính ổn định của biên lọc dầu.",
        "weekly_statistical_tests.json, biểu đồ so sánh Daily vs Weekly."
    ],
    [
        "Ngày 7",
        "Huấn luyện & Dự báo Khung Monthly (h=21)",
        "Chạy M0a, M2, M3, M4, M5 trên target tích lũy 21 phiên; kiểm soát chặt chẽ hiện tượng co mẫu OOS cuối chu kỳ; xuất chuỗi dự báo ngoài mẫu.",
        "pred_monthly_all_models.csv, monthly_metrics_leaderboard.json."
    ],
    [
        "Ngày 8",
        "Kiểm định Thống kê Khung Monthly với Newey-West HAC",
        "Chạy Clark-West và Diebold-Mariano cho Monthly với độ trễ HAC q >= 20 nhằm khắc phục tự tương quan MA(20); tổng hợp bảng so sánh 3 khung thời gian.",
        "monthly_statistical_tests.json, multi_horizon_cross_table.csv."
    ],
    [
        "Ngày 9",
        "Xây dựng Kiến trúc & Huấn luyện RNN Benchmark",
        "Lập trình module RNN (PyTorch/TensorFlow); thiết lập lookback window 20 ngày; fit scaler trên Train only; early stopping theo Val; lưu loss log per epoch.",
        "src/models/dl/rnn_model.py, rnn_training_log.csv, checkpoints/rnn_best.pt."
    ],
    [
        "Ngày 10",
        "Xây dựng Kiến trúc & Huấn luyện LSTM Benchmark",
        "Lập trình module LSTM với cơ chế gating; huấn luyện trên 3 horizons; chạy 5 random seeds để đánh giá mean ± std; lưu model weights và loss curves.",
        "src/models/dl/lstm_model.py, lstm_training_log.csv, checkpoints/lstm_best.pt."
    ],
    [
        "Ngày 11",
        "Hợp nhất Bảng Leaderboard Tổng thể 3 Horizons",
        "Tập hợp dự báo của toàn bộ các mô hình (M0a..M5, RNN, LSTM) trên Common OOS của từng horizon; tính toán đầy đủ RMSE, MAE, R2, DA, MCC, PT-stat.",
        "master_multi_horizon_leaderboard.csv, master_leaderboard.json."
    ],
    [
        "Ngày 12",
        "Phân tích Độ nhạy (Robustness) & Phân tích Lỗi (Error Analysis)",
        "Thực hiện feature ablation (loại bỏ từng biến lọc dầu); phân tích sai số trong các cuộc khủng hoảng (COVID-19 2020, Nga-Ukraine 2022); kiểm tra seed variance.",
        "robustness_ablation_results.json, error_analysis_report.md."
    ],
    [
        "Days 13",
        "Soạn thảo Research Paper Hoàn chỉnh (8 Phần Chuẩn mực)",
        "Viết bản thảo bài báo khoa học: Abstract, Introduction, Related Work, Data & PIT, Methodology, Empirical Results, Error Analysis, Discussion & Limitations.",
        "SPAFS_V5_2_Full_Research_Paper.md, SPAFS_V5_2_Research_Paper.docx."
    ],
    [
        "Ngày 14",
        "Kiểm tra Tính Tái lập Độc lập & Đóng gói Deliverables",
        "Chạy test trên môi trường sạch bằng kịch bản 1-dòng lệnh; kiểm tra tính toàn vẹn mã băm SHA-256; đóng gói ZIP hoàn thiện và hướng dẫn nộp bài.",
        "SPAFS_V5_2_FINAL_PACKAGE.zip, README_REPRODUCIBILITY.md."
    ]
]
add_table_data(headers_task5, rows_task5)

# ------------------------------------------------------------------------------
# TASK 6: REQUIRED FILES & ARTIFACTS
# ------------------------------------------------------------------------------
add_heading_1("NHIỆM VỤ 6: DANH MỤC CÁC TỆP DỮ LIỆU & TÀI LIỆU CẦN ĐỐI CHIẾU")

add_paragraph(
    "Để Trợ lý Nghiên cứu Khoa học có thể hỗ trợ bạn kiểm chứng độc lập và đảm bảo bài báo "
    "không mắc bất kỳ lỗi phương pháp luận nào trước hội đồng, dưới đây là danh mục các tệp cần rà soát và cung cấp:",
    bold_prefix="Danh mục Cung cấp Phục vụ Kiểm định: "
)

add_heading_2("6.1. Nhóm Dữ liệu Thô và Tập Dữ liệu Đã Xử lý")
add_bullet("Tệp dữ liệu giá xăng Platts FOB Singapore thô ban đầu (kèm cột ngày và giá thanh toán) để đối chiếu số lượng dòng (4,560 vs 4,429 dòng).", bold_prefix="1. price_petroleum_platts.csv (Raw Platts): ")
add_bullet("Tệp giá dầu thô Brent thô (kèm thời điểm chốt phiên sàn ICE London) để kiểm tra khớp lịch giao dịch.", bold_prefix="2. brent_crude_daily.csv (Raw Brent): ")
add_bullet("Tập dữ liệu Stream 1 và Stream 2 Parquet hiện hành trong data/processed/ để xác minh các đặc trưng lọc dầu hạ nguồn (Crack, Octane, Diesel).", bold_prefix="3. Parquet Datasets: ")

add_heading_2("6.2. Nhóm Mã nguồn (Scripts & Notebooks) Cần Xác minh")
add_bullet("Kịch bản hoặc notebook hiện tại định nghĩa và huấn luyện mô hình M0b để làm rõ công thức toán học thực tế (Naive Direction vs Naive Mean).", bold_prefix="4. Mã nguồn M0b (naive.py): ")
add_bullet("Kịch bản thực thi M2, M3 và trích xuất ma trận hiệp phương sai Newey-West HAC (để kiểm tra khớp p-value Wald test 0.9530 và 0.6360).", bold_prefix="5. Script M3 (runner_econometric.py): ")
add_bullet("Mã nguồn hoặc notebook thử nghiệm trước đây về gom cụm dữ liệu theo tuần (nếu có, ví dụ weekly.py) để kế thừa định nghĩa tuần.", bold_prefix="6. Script Weekly cũ: ")

add_heading_2("6.3. Nhóm Tệp Dự báo (Prediction Files) & Kết quả Gốc")
add_bullet("Tệp out_of_sample_predictions_all_7_models_harmonized_754.csv đã xuất khẩu để đối soát số liệu RMSE 1.4221 (M4) và 1.4163 (M5).", bold_prefix="7. CSV Dự báo 7 Mô hình: ")
add_bullet("Các tệp JSON leaderboard và pairwise tests cũ để đối chiếu xem có bất kỳ sự sai lệch p-value nào giữa các lần chạy trước đây hay không.", bold_prefix="8. Metrics JSONs: ")

add_heading_2("6.4. Nhóm Ý kiến & Yêu cầu từ Giảng viên Hướng dẫn (Advisor Feedback)")
add_bullet("Ghi chú, email hoặc biên bản trao đổi của giảng viên hướng dẫn về yêu cầu 3 khung thời gian Daily – Weekly – Monthly (để đảm bảo hiểu đúng 100% mong muốn của thầy/cô về định nghĩa tuần/tháng và danh mục mô hình bắt buộc).", bold_prefix="9. Văn bản Feedback của Giảng viên: ")
add_bullet("Bản thảo báo cáo cũ (ví dụ SPAFS.docx hoặc các slide thuyết trình trước đây) để rà soát toàn bộ các câu chữ kết luận quá mạnh cần được làm mềm.", bold_prefix="10. Bản thảo Báo cáo Cũ: ")

# ------------------------------------------------------------------------------
# CONCLUSION & SUMMARY
# ------------------------------------------------------------------------------
add_heading_1("KẾT LUẬN & CAM KẾT ĐỒNG HÀNH NGHIÊN CỨU")
add_paragraph(
    "Dự án SPAFS V5.2 sở hữu nền tảng dữ liệu kinh tế học năng lượng phong phú và quy trình kiểm soát Point-in-Time chặt chẽ. "
    "Bằng việc xác lập rõ ràng 4 trạng thái công việc, nhận diện trước các cạm bẫy kỹ thuật về target chồng lấn và rò rỉ dữ liệu, "
    "cùng với việc tuân thủ nghiêm ngặt lộ trình 14 ngày, chúng ta sẽ hoàn thiện một bài báo khoa học chuẩn mực, "
    "bảo vệ thuyết phục trước hội đồng khoa học với những kết luận hoàn toàn dựa trên bằng chứng dữ liệu thực nghiệm trung thực.",
    bold_prefix="Thông điệp Đồng hành: "
)

# Save document to workspace and Downloads
doc.save(output_docx_workspace)
doc.save(output_docx_downloads)

print(f"Successfully generated Master Research Plan DOCX at:\n  {output_docx_workspace}\n  {output_docx_downloads}")

