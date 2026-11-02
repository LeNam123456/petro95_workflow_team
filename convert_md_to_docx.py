# -*- coding: utf-8 -*-
"""Convert Markdown academic report to beautifully formatted Word Docx with XML sanitization."""

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

sys.stdout.reconfigure(encoding='utf-8')

md_path = Path("reports/SPAFS_V5_2_BAO_CAO_KHOA_HOC_HOAN_CHINH.md")
docx_path_workspace = Path("reports/SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx")
docx_path_downloads_named = Path("C:/Users/LeeNam/Downloads/SPAFS_V5_2_Bao_Cao_Hoan_Chinh.docx")
docx_path_downloads_spafs = Path("C:/Users/LeeNam/Downloads/SPAFS.docx")

doc = Document()

# Set standard 1-inch margins
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Set base font
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(11)
font.color.rgb = RGBColor(0x22, 0x22, 0x22)

def sanitize_text(text: str) -> str:
    """Remove illegal XML control characters."""
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

lines = md_path.read_text(encoding="utf-8").splitlines()

i = 0
in_code_block = False
code_lines = []

while i < len(lines):
    line = lines[i]
    stripped = sanitize_text(line.strip())

    # Code block toggle
    if stripped.startswith("```"):
        if in_code_block:
            in_code_block = False
            code_text = sanitize_text("\n".join(code_lines))
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(code_text)
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            code_lines = []
        else:
            in_code_block = True
            code_lines = []
        i += 1
        continue

    if in_code_block:
        code_lines.append(line)
        i += 1
        continue

    # Tables
    if stripped.startswith("|") and stripped.endswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
            table_lines.append(sanitize_text(lines[i].strip()))
            i += 1

        rows_data = []
        for tl in table_lines:
            cells = [c.strip() for c in tl.split("|")[1:-1]]
            if all(re.match(r'^:?-+:?$', c) for c in cells):
                continue
            rows_data.append(cells)

        if rows_data:
            num_rows = len(rows_data)
            num_cols = max(len(r) for r in rows_data)
            tbl = doc.add_table(rows=num_rows, cols=num_cols)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_borders(tbl)

            for r_idx, row in enumerate(rows_data):
                for c_idx in range(num_cols):
                    cell = tbl.cell(r_idx, c_idx)
                    val = row[c_idx] if c_idx < len(row) else ""
                    clean_val = re.sub(r'\*\*(.*?)\*\*', r'\1', val)
                    clean_val = re.sub(r'[\$\\]', '', clean_val)
                    clean_val = sanitize_text(clean_val)
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    run = p.add_run(clean_val)
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(9.5)

                    if r_idx == 0:
                        set_cell_background(cell, "003366")
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:
                        if r_idx % 2 == 1:
                            set_cell_background(cell, "F8FAFC")
                        else:
                            set_cell_background(cell, "FFFFFF")
                        if c_idx == 0 or "**" in val:
                            run.font.bold = True
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
        continue

    # Headings
    if stripped.startswith("# "):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(sanitize_text(stripped[2:]))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(20)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x00, 0x2B, 0x49)
    elif stripped.startswith("## "):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(sanitize_text(stripped[3:]))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    elif stripped.startswith("### "):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(sanitize_text(stripped[4:]))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    elif stripped.startswith("#### "):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(sanitize_text(stripped[5:]))
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    elif stripped.startswith("> [!"):
        alert_type = re.search(r'> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', stripped)
        alert_title = alert_type.group(1) if alert_type else "NOTE"
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"[{alert_title}] ")
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x00, 0x33, 0x66)
    elif stripped.startswith("> "):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        text = sanitize_text(stripped[2:])
        run = p.add_run(text)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    elif stripped.startswith("- ") or stripped.startswith("* "):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        text = sanitize_text(stripped[2:])
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                r = p.add_run(sanitize_text(part[2:-2]))
                r.font.bold = True
            else:
                p.add_run(sanitize_text(part))
    elif stripped == "---":
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run("―" * 55)
        r.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    elif stripped:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        parts = re.split(r'(\*\*.*?\*\*)', stripped)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                r = p.add_run(sanitize_text(part[2:-2]))
                r.font.bold = True
            else:
                p.add_run(sanitize_text(part))
    
    i += 1

doc.save(docx_path_workspace)
doc.save(docx_path_downloads_named)
doc.save(docx_path_downloads_spafs)
print(f"Successfully generated clean DOCX at:\n  {docx_path_workspace}\n  {docx_path_downloads_named}\n  {docx_path_downloads_spafs}")
