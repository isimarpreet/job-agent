"""Turn a tailored resume written in Markdown into a PDF for uploading.

Run: python resume_tailoring/resume_pdf.py resume_tailoring/tailored/some-job.md resume_tailoring/tailored/some-job.pdf

Understands only what a resume needs: # and ## headings, - bullets and **bold**.
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Table, TableStyle

FONT_FOLDER = Path("/System/Library/Fonts/Supplemental")
# Matches a bold title followed by dates, like: **Engineer - Acme** (03/2025 - 2026)
DATED_LINE = re.compile(r"^(\*\*.+\*\*) \((\d{2}/\d{4} - .+)\)$")


def _register_fonts() -> tuple[str, str]:
    regular, bold = FONT_FOLDER / "Arial.ttf", FONT_FOLDER / "Arial Bold.ttf"
    if not (regular.exists() and bold.exists()):
        return "Helvetica", "Helvetica-Bold"  # Built in, but fewer characters.
    pdfmetrics.registerFont(TTFont("ResumeRegular", regular))
    pdfmetrics.registerFont(TTFont("ResumeBold", bold))
    pdfmetrics.registerFontFamily(
        "ResumeRegular",
        normal="ResumeRegular",
        bold="ResumeBold",
        italic="ResumeRegular",
        boldItalic="ResumeBold",
    )
    return "ResumeRegular", "ResumeBold"


def _inline(text: str) -> str:
    # Escape first, because reportlab treats & and < in text as markup.
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(text))


def _dated_row(title: str, dates: str, width: float, title_style, date_style) -> Table:
    """A job title on the left with its dates aligned to the right margin."""
    date_width = 35 * mm
    row = Table(
        [[Paragraph(_inline(title), title_style), Paragraph(escape(dates), date_style)]],
        colWidths=[width - date_width, date_width],
    )
    row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return row


def build_pdf(source: Path, target: Path) -> None:
    regular, bold = _register_fonts()
    document = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=10 * mm,
        bottomMargin=8 * mm,
    )
    width = document.width - 12  # The page frame keeps 6 points of padding each side.

    body = ParagraphStyle("body", fontName=regular, fontSize=8.8, leading=10.2, spaceAfter=1)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=9, bulletIndent=1)
    name = ParagraphStyle(
        "name", fontName=bold, fontSize=16, leading=19, alignment=TA_CENTER, spaceAfter=1
    )
    header = ParagraphStyle("header", parent=body, alignment=TA_CENTER)
    section = ParagraphStyle("section", fontName=bold, fontSize=10.5, leading=12.5, spaceBefore=4)
    dates = ParagraphStyle("dates", parent=body, alignment=TA_RIGHT)

    story = []
    in_header = False
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        dated = DATED_LINE.match(line)
        if not line:
            continue
        if line.startswith("## "):
            in_header = False
            story.append(Paragraph(_inline(line[3:]), section))
            story.append(HRFlowable(width="100%", thickness=0.6, color=black, spaceAfter=2))
        elif line.startswith("# "):
            in_header = True
            story.append(Paragraph(_inline(line[2:]), name))
        elif in_header:
            story.append(Paragraph(_inline(line), header))
        elif dated:
            story.append(_dated_row(dated[1], dated[2], width, body, dates))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(_inline(line[2:]), bullet, bulletText="\u2022"))
        else:
            story.append(Paragraph(_inline(line), body))

    document.build(story)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python resume_tailoring/resume_pdf.py input.md output.pdf")
    build_pdf(Path(sys.argv[1]), Path(sys.argv[2]))
