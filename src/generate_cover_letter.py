"""
Renders cover_letter_content.build_cover_letter() output into a PDF that
visually echoes the CV template (same navy name header, same fonts), so
the CV and cover letter read as a matched pair for a given application.
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

from cv_structure import load_cv_structure
from cover_letter_content import build_cover_letter

NAVY = HexColor("#1F4E79")
GRAY = HexColor("#595959")
MARGIN = 0.9 * inch
PAGE_WIDTH, PAGE_HEIGHT = LETTER

STYLES = {
    "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=16,
                            textColor=NAVY, alignment=TA_CENTER, leading=19),
    "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=8.5,
                               textColor=GRAY, alignment=TA_CENTER, leading=11,
                               spaceAfter=14),
    "greeting": ParagraphStyle("greeting", fontName="Helvetica", fontSize=10.3,
                                textColor=black, alignment=TA_LEFT, leading=14.5,
                                spaceAfter=10),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.3,
                            textColor=black, alignment=TA_JUSTIFY, leading=14.5,
                            spaceAfter=10),
}


def render_cover_letter(letter: dict, header: dict, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
    )

    story = [
        Paragraph(header["name"], STYLES["name"]),
        Paragraph(header["contact_line"], STYLES["contact"]),
        Paragraph(letter["greeting"], STYLES["greeting"]),
        Paragraph(letter["opening"], STYLES["body"]),
    ]
    for para in letter["body_paragraphs"]:
        story.append(Paragraph(para, STYLES["body"]))
    story.append(Paragraph(letter["closing"], STYLES["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(letter["signoff"], STYLES["body"]))
    story.append(Paragraph(header["name"], STYLES["body"]))

    doc.build(story)


if __name__ == "__main__":
    structure = load_cv_structure()
    sample_posting = {
        "company": "Example GmbH",
        "title": "AI Engineering Intern",
        "reasoning": "Looking for Python, RAG, and LLM experience.",
    }
    letter = build_cover_letter(structure, sample_posting)
    out_path = "profiles/cover_letter_generated_test.pdf"
    render_cover_letter(letter, structure["header"], out_path)
    print(f"wrote {out_path}")