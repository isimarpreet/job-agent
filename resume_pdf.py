"""Turn a tailored resume written in Markdown into a PDF for uploading.

Run: python resume_pdf.py tailored/some-job.md tailored/some-job.pdf

Understands only what a resume needs: # and ## headings, - bullets and **bold**.
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

FONT_FOLDER = Path("/System/Library/Fonts/Supplemental")


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


def build_pdf(source: Path, target: Path) -> None:
    regular, bold = _register_fonts()
    body = ParagraphStyle("body", fontName=regular, fontSize=10, leading=13.5, spaceAfter=3)
    name = ParagraphStyle(
        "name", fontName=bold, fontSize=17, leading=21, alignment=TA_CENTER, spaceAfter=6
    )
    section = ParagraphStyle(
        "section", fontName=bold, fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=3
    )
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=11, bulletIndent=1)

    story = []
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("## "):
            story.append(Paragraph(_inline(line[3:]), section))
        elif line.startswith("# "):
            story.append(Paragraph(_inline(line[2:]), name))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph(_inline(line[2:]), bullet, bulletText="•"))
        else:
            story.append(Paragraph(_inline(line), body))

    document = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    document.build(story)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python resume_pdf.py input.md output.pdf")
    build_pdf(Path(sys.argv[1]), Path(sys.argv[2]))
