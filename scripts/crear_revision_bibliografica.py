"""Renderiza la revisión bibliográfica en PDF desde su fuente Markdown.

Uso: python3 scripts/crear_revision_bibliografica.py
Requiere reportlab. Conserva los datos crudos y los entregables anteriores.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs/Revision_Bibliografica_TWS.md"
OUTPUT = ROOT / "output/pdf/Revision_Bibliografica_y_Seleccion_Modelos_TWS.pdf"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
INK = colors.HexColor("#1B2834")
ACCENT = colors.HexColor("#17656A")
MUTED = colors.HexColor("#52616C")


def register_fonts() -> None:
    for name, file in [
        ("Review", "Arial.ttf"), ("Review-Bold", "Arial Bold.ttf"),
        ("Review-Italic", "Arial Italic.ttf"),
        ("Review-BoldItalic", "Arial Bold Italic.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
    pdfmetrics.registerFontFamily(
        "Review", normal="Review", bold="Review-Bold",
        italic="Review-Italic", boldItalic="Review-BoldItalic",
    )


def rich(text: str) -> str:
    text = html.escape(text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda m: f'<link href="{m[2]}" color="#17656A">{m[1]}</link>', text,
    )
    text = re.sub(r"`([^`]+)`", r'<font color="#17656A">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)


def make_styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName="Review", textColor=INK, fontSize=10.8, leading=15.0)
    styles = {
        "body": ParagraphStyle("Body", alignment=TA_JUSTIFY, spaceAfter=9, **base),
        "h1": ParagraphStyle("Heading1", fontName="Review-Bold", fontSize=17,
                             leading=21, textColor=ACCENT, spaceAfter=17,
                             keepWithNext=True),
        "h2": ParagraphStyle("Heading2", fontName="Review-Bold", fontSize=12.5,
                             leading=17, textColor=INK, spaceAfter=9,
                             keepWithNext=True),
        "h3": ParagraphStyle("Heading3", fontName="Review-Bold", fontSize=11.2,
                             leading=15, textColor=ACCENT, spaceBefore=5,
                             spaceAfter=6, keepWithNext=True),
        "title": ParagraphStyle("Title", fontName="Review-Bold", fontSize=25,
                                leading=31, textColor=INK, spaceAfter=15),
        "subtitle": ParagraphStyle("Subtitle", fontName="Review", fontSize=16,
                                   leading=21, textColor=ACCENT, spaceAfter=22),
        "meta": ParagraphStyle("Meta", fontName="Review", fontSize=10.8,
                               leading=15, textColor=MUTED, spaceAfter=8),
        "note": ParagraphStyle("Note", fontName="Review", fontSize=9.2,
                               leading=12.7, textColor=MUTED, spaceAfter=10),
        "ref": ParagraphStyle("Reference", fontName="Review", fontSize=10.6,
                              leading=20.8, textColor=INK, alignment=TA_LEFT,
                              leftIndent=1.27 * cm, firstLineIndent=-1.27 * cm,
                              spaceAfter=10, splitLongWords=True),
        "cell": ParagraphStyle("Cell", fontName="Review", fontSize=8.9,
                               leading=12.0, textColor=INK),
        "cellhead": ParagraphStyle("CellHead", fontName="Review-Bold", fontSize=9,
                                   leading=12, textColor=colors.white),
        "caption": ParagraphStyle("Caption", fontName="Review", fontSize=9.8,
                                  leading=13.5, textColor=INK, spaceAfter=8,
                                  keepWithNext=True),
    }
    return styles


class ReviewDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"Heading1", "Title"}:
            title = flowable.getPlainText()
            key = f"section-{self.page}-{len(title)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, 0, False)


def decoration(canvas, doc) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setTitle("Revisión bibliográfica y selección preliminar de modelos de TWS")
    canvas.setAuthor("Proyecto 2 | CC3084 - Data Science")
    canvas.setSubject("Literatura científica sobre GRACE y propuesta de modelos de pronóstico")
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.0)
    canvas.line(doc.leftMargin, height - 1.35 * cm, width - doc.rightMargin, height - 1.35 * cm)
    canvas.setFont("Review", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, height - 1.12 * cm, "CC3084 · PROYECTO 2")
    canvas.drawRightString(width - doc.rightMargin, height - 1.12 * cm, "PRONÓSTICO DEL ALMACENAMIENTO DE AGUA")
    canvas.setStrokeColor(colors.HexColor("#CBD6D8"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 1.40 * cm, width - doc.rightMargin, 1.40 * cm)
    canvas.setFont("Review", 8)
    canvas.drawString(doc.leftMargin, 0.95 * cm, "Revisión bibliográfica · 11 de octubre de 2026")
    canvas.drawRightString(width - doc.rightMargin, 0.95 * cm, str(doc.page))
    canvas.restoreState()


def make_table(lines, styles, width):
    parsed = [line.strip().strip("|").split("|") for line in lines]
    rows = [parsed[0]] + parsed[2:]
    first = "Estudio" in rows[0][0]
    fractions = [0.205, 0.235, 0.255, 0.305] if first else [0.215, 0.275, 0.20, 0.31]
    cells = [[Paragraph(rich(c.strip()), styles["cellhead" if i == 0 else "cell"])
              for c in row] for i, row in enumerate(rows)]
    t = Table(cells, colWidths=[width * f for f in fractions], repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0F5F5"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, ACCENT),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#CBD6D8")),
    ]))
    return t


def build() -> None:
    register_fonts()
    styles = make_styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ReviewDoc(str(OUTPUT), pagesize=A4, leftMargin=2.15 * cm,
                    rightMargin=2.15 * cm, topMargin=1.95 * cm,
                    bottomMargin=1.9 * cm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="Review", frames=frame, onPage=decoration)])
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    page = 1
    references = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- pagebreak -->":
            story.append(PageBreak())
            page += 1
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:]
            if title.startswith("8. Referencias"):
                references = True
            if title.startswith("Anexo"):
                references = False
            story.append(Paragraph(rich(title), styles["title" if page == 1 else "h1"]))
            i += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(rich(line[3:]), styles["subtitle" if page == 1 else "h2"]))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(rich(line[4:]), styles["h3"]))
            i += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.extend([make_table(table_lines, styles, doc.width), Spacer(1, 9)])
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "<!--")):
            paragraph.append(lines[i].strip())
            i += 1
        text = " ".join(paragraph)
        if text.startswith("**Tabla"):
            style = "caption"
        elif text.startswith(("*Nota.", "*Nota bibliográfica.")):
            style = "note"
        elif references:
            style = "ref"
        elif page == 1 and not text.startswith(("Este documento", "Para el proyecto", "**Palabras", "Problema y")):
            style = "meta"
        else:
            style = "body"
        story.append(Paragraph(rich(text), styles[style]))
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
