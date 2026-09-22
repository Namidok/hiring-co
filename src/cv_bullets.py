"""
Parses the candidate's real CV text into a structured "bullet bank":
one entry per bullet point, tagged with which section and which
employer/project it belongs to.

This is deterministic parsing, not LLM extraction - the bullet bank is
the ground truth Agent 4 (draft_application.py) is allowed to quote
from. No bullet content lives in this file or anywhere under src/; it's
read from profiles/cv_raw_text.txt at runtime, which is gitignored.

PDF text extraction wraps long lines (a bullet or a header can span two
physical lines with no marker). To reassemble correctly we track
"bullets_since_header": while it's 0, a non-bullet line is still part of
the current context header (append to it) - this handles wrapped
headers like a project name + tech stack spilling onto a second line.
Once at least one bullet has been emitted for the current context, a
non-bullet line is either (a) a continuation of that bullet's wrapped
text, appended to it, or (b) the start of a genuinely new context, if
it matches the header pattern this CV consistently uses (an em dash
for a title/company or project name, or a "|" before a date range).
This is calibrated against this specific CV's real formatting, not a
general-purpose CV parser - verify against `python src/cv_bullets.py`
output whenever the source CV text changes.
"""
import re
from pathlib import Path

SECTION_HEADERS = {
    "SUMMARY",
    "TECHNICAL SKILLS",
    "PROFESSIONAL EXPERIENCE",
    "PROJECTS",
    "EDUCATION",
}

HEADER_PATTERN = re.compile(chr(0x2014) + "|\\|")  # em dash or pipe


def _join(a: str, b: str) -> str:
    """
    Joins two wrapped fragments. If the previous fragment ends in a
    hyphen (e.g. "page-" wrapping to "load" -> "page-load"), close the
    gap without a space, keeping the hyphen intact - it's part of the
    real word, not punctuation to discard. Otherwise join with a space.
    """
    if a.endswith("-"):
        return a + b
    return f"{a} {b}".strip()


def load_bullet_bank(text_path: str = "profiles/cv_raw_text.txt") -> list[dict]:
    """
    Returns a list of:
        {"id": "b001", "section": "PROJECTS", "context": "...",
         "text": "Built a reproducible benchmarking harness..."}

    id is stable across calls given unchanged CV text, so it's safe to
    reference in downstream drafts.
    """
    path = Path(text_path)
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]

    bullets = []
    current_section = None
    current_context = None
    bullets_since_header = 0
    bullet_num = 0
    BULLET = chr(0x2022)

    for line in lines:
        if line in SECTION_HEADERS:
            current_section = line
            current_context = None
            bullets_since_header = 0
            continue

        if line.startswith(BULLET):
            bullet_num += 1
            bullets.append({
                "id": f"b{bullet_num:03d}",
                "section": current_section or "UNKNOWN",
                "context": current_context or current_section or "UNKNOWN",
                "text": line.lstrip(BULLET).strip(),
            })
            bullets_since_header += 1
            continue

        is_header_line = bool(HEADER_PATTERN.search(line))

        if bullets_since_header == 0:
            current_context = _join(current_context, line) if current_context else line
        elif is_header_line:
            current_context = line
            bullets_since_header = 0
        else:
            if bullets:
                bullets[-1]["text"] = _join(bullets[-1]["text"], line)

    return bullets


if __name__ == "__main__":
    bank = load_bullet_bank()
    print(f"parsed {len(bank)} bullets\n")
    for b in bank:
        print(f"[{b['id']}] ({b['section']} / {b['context'][:60]})")
        print(f"   {b['text']}\n")