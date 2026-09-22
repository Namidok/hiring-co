"""
Full structural parser for the candidate's real CV text: name/contact
header, summary paragraph, skills categories, experience/project
entries (each with a bold title/name + normal location-and-dates or
description, plus bullets), and education entries.

This is the ground truth for generate_cv.py, which re-renders the same
visual template with a different bullet selection per job posting.
Reads profiles/cv_raw_text.txt at runtime - never hardcode CV content
into src/, since src/ is committed to git and this is personal data.
"""
import re
from pathlib import Path

SECTION_HEADERS = [
    "SUMMARY",
    "TECHNICAL SKILLS",
    "PROFESSIONAL EXPERIENCE",
    "PROJECTS",
    "EDUCATION",
]

BULLET = chr(0x2022)
EM_DASH = chr(0x2014)
HEADER_PATTERN = re.compile(f"[{EM_DASH}|]")


def _join(a: str, b: str) -> str:
    if a.endswith("-"):
        return a + b
    return f"{a} {b}".strip()


def _split_columns(line: str) -> tuple[str, str]:
    """
    Splits a two-column line ("Bold left part    normal right part") on
    the run of 2+ spaces the original PDF used to separate a
    right-aligned date/location column. Returns (left, right); right is
    "" if there's no such gap.
    """
    parts = re.split(r" {2,}", line, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return line.strip(), ""


def _parse_entries(lines: list[str]) -> list[dict]:
    """
    Generic grouping for PROFESSIONAL EXPERIENCE / PROJECTS: repeated
    (header, bullets) blocks. Mirrors cv_bullets.py's state machine so
    the two parsers can never disagree about entry boundaries.
    """
    entries = []
    pending_header = None
    bullets_since_header = 0

    for line in lines:
        if line.startswith(BULLET):
            if pending_header is not None:
                entries.append({"header": pending_header, "bullets": []})
                pending_header = None
            entries[-1]["bullets"].append(line.lstrip(BULLET).strip())
            bullets_since_header += 1
            continue

        is_header_line = bool(HEADER_PATTERN.search(line))

        if bullets_since_header == 0:
            pending_header = _join(pending_header, line) if pending_header else line
        elif is_header_line:
            pending_header = line
            bullets_since_header = 0
        else:
            entries[-1]["bullets"][-1] = _join(entries[-1]["bullets"][-1], line)

    return entries


def _structure_experience(entries: list[dict]) -> list[dict]:
    out = []
    for e in entries:
        left, right = _split_columns(e["header"])
        out.append({"title_company": left, "location_dates": right, "bullets": e["bullets"]})
    return out


def _structure_projects(entries: list[dict]) -> list[dict]:
    out = []
    for e in entries:
        header = e["header"]
        if EM_DASH in header:
            name, rest = header.split(EM_DASH, 1)
            name, rest = name.strip(), rest.strip()
        else:
            name, rest = header, ""
        out.append({"name": name, "description": rest, "bullets": e["bullets"]})
    return out


def _parse_education(lines: list[str]) -> list[dict]:
    entries = []
    for line in lines:
        is_header_line = bool(re.search(r" {2,}", line))
        if is_header_line or not entries:
            left, right = _split_columns(line)
            entries.append({"degree": left, "dates": right, "institution": None})
        else:
            if entries[-1]["institution"] is None:
                entries[-1]["institution"] = line
            else:
                entries[-1]["institution"] = _join(entries[-1]["institution"], line)
    return entries


def load_cv_structure(text_path: str = "profiles/cv_raw_text.txt") -> dict:
    path = Path(text_path)
    raw_lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]

    header_lines = []
    i = 0
    while i < len(raw_lines) and raw_lines[i] not in SECTION_HEADERS:
        header_lines.append(raw_lines[i])
        i += 1
    header = {
        "name": header_lines[0] if len(header_lines) > 0 else "",
        "subtitle": header_lines[1] if len(header_lines) > 1 else "",
        "contact_line": header_lines[2] if len(header_lines) > 2 else "",
    }

    sections: dict[str, list[str]] = {h: [] for h in SECTION_HEADERS}
    current = None
    for line in raw_lines[i:]:
        if line in SECTION_HEADERS:
            current = line
            continue
        if current:
            sections[current].append(line)

    summary = ""
    for line in sections["SUMMARY"]:
        summary = _join(summary, line) if summary else line

    skill_texts = []
    for line in sections["TECHNICAL SKILLS"]:
        if line.startswith(BULLET):
            skill_texts.append(line.lstrip(BULLET).strip())
        elif skill_texts:
            skill_texts[-1] = _join(skill_texts[-1], line)

    skills = []
    for text in skill_texts:
        if ":" in text:
            category, items = text.split(":", 1)
            skills.append({"category": category.strip(), "items": items.strip()})

    experience = _structure_experience(_parse_entries(sections["PROFESSIONAL EXPERIENCE"]))
    projects = _structure_projects(_parse_entries(sections["PROJECTS"]))
    education = _parse_education(sections["EDUCATION"])

    return {
        "header": header,
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(load_cv_structure(), indent=2))