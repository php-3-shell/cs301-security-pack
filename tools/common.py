"""Shared helpers and team data for the CS301 artefact generators."""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = os.environ.get("CS301_OUT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEAM_NAME = "php3shell"
REPO = "[GITHUB REPOSITORY URL]"
EGON = "Egon Hashani"
VESANJA = "Vesanja Bregasi"
GH = {EGON: "eszvc", VESANJA: "[GITHUB USERNAME]"}
def who(n): return f"{n} ({GH[n]})"

CASE = "MUDT AI Learning Assistant and Management Platform (hybrid on-premises / cloud)"
VERSION = "v0.1 draft for team review"
DATE = "2026-10-30"

ACCENT = "1F4E5F"
ACCENT_LIGHT = "DCE9EE"
GREY = "F2F2F2"

PRIO_FILL = {"Critical": "C00000", "High": "ED7D31", "Medium": "FFC000", "Low": "70AD47"}
PRIO_FONT = {"Critical": "FFFFFF", "High": "FFFFFF", "Medium": "000000", "Low": "FFFFFF"}

def priority(score):
    return "Critical" if score >= 16 else "High" if score >= 10 else "Medium" if score >= 5 else "Low"

# ---------------------------------------------------------------- docx helpers
def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)

def new_doc(title, subtitle, artefact_id, story_ids, owner, landscape=False):
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    if landscape:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for lvl, size in ((1, 15), (2, 12.5), (3, 11)):
        h = d.styles[f"Heading {lvl}"]; h.font.name = "Calibri"; h.font.size = Pt(size)
        h.font.color.rgb = RGBColor.from_string(ACCENT)
    p = d.add_paragraph(); r = p.add_run(title); r.bold = True; r.font.size = Pt(22)
    r.font.color.rgb = RGBColor.from_string(ACCENT)
    p = d.add_paragraph(); r = p.add_run(subtitle); r.italic = True; r.font.size = Pt(12)
    kv(d, [("Artefact ID", artefact_id), ("Case", CASE), ("User stories", story_ids),
           ("Artefact owner", owner), ("Team", f"{TEAM_NAME} – {EGON}, {VESANJA}"),
           ("Version / date", f"{VERSION} / {DATE}")])
    fp = sec.footer.paragraphs[0]; fp.text = f"CS301 Basics of Information Security · {artefact_id} · {VERSION}"
    fp.runs[0].font.size = Pt(8); fp.runs[0].font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    return d

def table(d, header, rows, widths=None, font=9, zebra=True, prio_col=None):
    t = d.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True
        r.font.size = Pt(font); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); _shade(c, ACCENT)
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            c = cells[i]; c.text = ""
            for li, line in enumerate(str(v).split("\n")):
                p = c.paragraphs[0] if li == 0 else c.add_paragraph()
                bold = line.startswith("**") and line.endswith("**") and len(line) > 4
                r = p.add_run(line[2:-2] if bold else line); r.font.size = Pt(font); r.bold = bold
            if prio_col is not None and i == prio_col and v in PRIO_FILL:
                _shade(c, PRIO_FILL[v]); run = c.paragraphs[0].runs[0]
                run.font.color.rgb = RGBColor.from_string(PRIO_FONT[v]); run.bold = True
            elif zebra and ri % 2 == 1:
                _shade(c, GREY)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph()
    return t

def kv(d, pairs, widths=(4.2, 12.8)):
    t = d.add_table(rows=0, cols=2); t.style = "Table Grid"
    for k, v in pairs:
        c = t.add_row().cells
        c[0].text = ""; r = c[0].paragraphs[0].add_run(k); r.bold = True; r.font.size = Pt(9.5); _shade(c[0], ACCENT_LIGHT)
        c[1].text = ""
        for li, line in enumerate(str(v).split("\n")):
            p = c[1].paragraphs[0] if li == 0 else c[1].add_paragraph()
            p.add_run(line).font.size = Pt(9.5)
    for row in t.rows:
        row.cells[0].width, row.cells[1].width = Cm(widths[0]), Cm(widths[1])
    d.add_paragraph()

def bullets(d, items, style="List Bullet"):
    for it in items:
        p = d.add_paragraph(style=style)
        if it.startswith("**") and "**" in it[2:]:
            b, rest = it[2:].split("**", 1); p.add_run(b).bold = True; p.add_run(rest)
        else:
            p.add_run(it)

def para(d, text, italic=False, bold=False, size=None):
    p = d.add_paragraph(); r = p.add_run(text); r.italic = italic; r.bold = bold
    if size: r.font.size = Pt(size)
    return p

def note(d, text):
    p = d.add_paragraph(); r = p.add_run(text); r.italic = True; r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

def image(d, path, width_cm):
    d.add_picture(path, width=Cm(width_cm))

def save_doc(d, rel):
    path = os.path.join(OUT, rel); os.makedirs(os.path.dirname(path), exist_ok=True); d.save(path); print("wrote", rel)

# ---------------------------------------------------------------- xlsx helpers
THIN = Side(style="thin", color="BFBFBF")
def sheet(wb, name, header, rows, widths, title=None, meta=None, prio_col=None, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name
    r0 = 1
    if title:
        ws.cell(1, 1, title).font = Font(bold=True, size=14, color=ACCENT)
        if meta:
            ws.cell(2, 1, meta).font = Font(italic=True, size=9, color="595959")
        r0 = 4
    for i, h in enumerate(header, 1):
        c = ws.cell(r0, i, h); c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor=ACCENT)
        c.alignment = Alignment(wrap_text=True, vertical="center"); c.border = Border(THIN, THIN, THIN, THIN)
    for ri, row in enumerate(rows, r0 + 1):
        for ci, v in enumerate(row, 1):
            c = ws.cell(ri, ci, v); c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = Border(THIN, THIN, THIN, THIN)
            if prio_col is not None and ci - 1 == prio_col and v in PRIO_FILL:
                c.fill = PatternFill("solid", fgColor=PRIO_FILL[v]); c.font = Font(bold=True, color=PRIO_FONT[v])
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(r0 + 1, 2)
    ws.auto_filter.ref = f"A{r0}:{get_column_letter(len(header))}{r0 + len(rows)}"
    return ws

def save_wb(wb, rel):
    path = os.path.join(OUT, rel); os.makedirs(os.path.dirname(path), exist_ok=True); wb.save(path); print("wrote", rel)
