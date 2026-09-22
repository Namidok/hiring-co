"""
Renders the candidate's CV structure (cv_structure.py) back into a PDF
that visually matches the original template: centered navy name/title/
contact header, navy section headers with an underline rule, bold
"Title -- Company" left / normal "Location | Dates" right on the same
line for jobs and education, bold project name + normal description,
and bullet lists underneath.

This is a template renderer, not a redesign tool: given a full or
filtered cv_structure() dict, it produces a new PDF with the same
visual layout every time. Agent 4 (draft_application.py) will call this
per posting with a trimmed set of bullets/entries selected from the
real bullet bank - never with invented content.

Colors/fonts are a best-effort visual match using reportlab's built-in
fonts (no Calibri license bundled here) - compare the output against
the real cv.pdf and adjust the constants below if anything looks off.
"""
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle

from cv_structure import load_cv_structure

NAVY = HexColor("#1F4E79")
GRAY = HexColor("#595959")

MARGIN = 0.26 * inch
PAGE_WIDTH, PAGE_HEIGHT = LETTER
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

STYLES = {
    "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=18,
                            textColor=NAVY, alignment=TA_CENTER, leading=21),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10.5,
                                textColor=black, alignment=TA_CENTER, leading=13,
                                spaceAfter=0.5),
    "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=8,
                               textColor=GRAY, alignment=TA_CENTER, leading=10,
                               spaceAfter=2),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11.5,
                               textColor=NAVY, spaceBefore=1, spaceAfter=0.3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=8.8,
                            textColor=black, alignment=TA_JUSTIFY, leading=10.2,
                            spaceAfter=1),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=8.8,
                              textColor=black, leading=10.2, spaceAfter=0.1,
                              leftIndent=15, bulletIndent=2),
    "entry_bold": ParagraphStyle("entry_bold", fontName="Helvetica-Bold", fontSize=9.3,
                                  textColor=black, alignment=TA_LEFT, leading=10.6),
    "entry_normal": ParagraphStyle("entry_normal", fontName="Helvetica", fontSize=8.8,
                                    textColor=black, alignment=TA_RIGHT, leading=10.6),
    "project_line": ParagraphStyle("project_line", fontName="Helvetica", fontSize=8.8,
                                    textColor=black, leading=10.2, spaceAfter=0.1),
    "institution": ParagraphStyle("institution", fontName="Helvetica", fontSize=8.8,
                                   textColor=black, leading=10.2, spaceAfter=0.5),
}

BULLET_CHAR = chr(0x2022)


def _section_header(title: str) -> list:
    return [
        Paragraph(title, STYLES["section"]),
        HRFlowable(width="100%", thickness=0.75, color=NAVY, spaceAfter=0.5),
    ]


def _two_column_row(left_text: str, right_text: str) -> Table:
    left = Paragraph(left_text, STYLES["entry_bold"])
    right = Paragraph(right_text, STYLES["entry_normal"])
    table = Table([[left, right]], colWidths=[CONTENT_WIDTH * 0.62, CONTENT_WIDTH * 0.38])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
    ]))
    return table


def _bullets(items: list[str]) -> list:
    return [Paragraph(text, STYLES["bullet"], bulletText=BULLET_CHAR) for text in items]


def render_cv(structure: dict, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
    )

    story = []
    header = structure["header"]
    story.append(Paragraph(header["name"], STYLES["name"]))
    story.append(Paragraph(header["subtitle"], STYLES["subtitle"]))
    story.append(Paragraph(header["contact_line"], STYLES["contact"]))

    story += _section_header("SUMMARY")
    story.append(Paragraph(structure["summary"], STYLES["body"]))

    story += _section_header("TECHNICAL SKILLS")
    for skill in structure["skills"]:
        text = f"<b>{skill['category']}:</b> {skill['items']}"
        story.append(Paragraph(text, STYLES["bullet"], bulletText=BULLET_CHAR))

    story += _section_header("PROFESSIONAL EXPERIENCE")
    for entry in structure["experience"]:
        story.append(_two_column_row(entry["title_company"], entry["location_dates"]))
        story += _bullets(entry["bullets"])
        story.append(Spacer(1, 0.3))

    story += _section_header("PROJECTS")
    for proj in structure["projects"]:
        text = f"<b>{proj['name']}</b> {chr(0x2014)} {proj['description']}"
        story.append(Paragraph(text, STYLES["project_line"]))
        story += _bullets(proj["bullets"])
        story.append(Spacer(1, 0.3))

    story += _section_header("EDUCATION")
    for edu in structure["education"]:
        story.append(_two_column_row(edu["degree"], edu["dates"]))
        story.append(Paragraph(edu["institution"], STYLES["institution"]))

    doc.build(story)


if __name__ == "__main__":
    structure = load_cv_structure()
    out_path = "profiles/cv_generated_test.pdf"
    render_cv(structure, out_path)
    print(f"wrote {out_path}")