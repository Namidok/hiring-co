"""
Builds cover-letter content for a specific job posting from the
candidate's real CV structure - never invents facts, only selects and
lightly reframes-as-a-sentence the same bullet text used on the CV, plus
the CV's own summary. Output is a dict of plain-text sections;
generate_cover_letter.py renders it to a PDF that matches the CV's style.
"""
from select_bullets import _posting_keywords, _score_bullet


def _top_bullets(structure: dict, keywords: set[str], count: int) -> list[str]:
    """
    Pools every experience + project bullet from the real CV and returns
    the `count` most relevant to this posting's keywords. Falls back to
    the first `count` bullets in CV order if there are no keyword
    matches at all, so a letter is still produced.
    """
    pool = []
    for entry in structure["experience"]:
        pool.extend(entry["bullets"])
    for entry in structure["projects"]:
        pool.extend(entry["bullets"])

    if not keywords:
        return pool[:count]

    scored = [(i, b, _score_bullet(b, keywords)) for i, b in enumerate(pool)]
    scored.sort(key=lambda t: (-t[2], t[0]))

    top = [b for _, b, score in scored if score > 0][:count]
    if len(top) < count:
        used = set(top)
        for _, b, _ in scored:
            if b not in used:
                top.append(b)
                used.add(b)
            if len(top) == count:
                break
    return top


def _lead_lower(text: str) -> str:
    """Lowercases the leading word so a CV bullet reads naturally after
    'I have' / 'I also' instead of as a standalone bulleted fragment."""
    if not text:
        return text
    return text[0].lower() + text[1:]


def build_cover_letter(structure: dict, posting: dict) -> dict:
    company = posting.get("company", "").strip() or "your team"
    role = posting.get("title", "").strip() or "this role"
    keywords = _posting_keywords(posting)

    top = _top_bullets(structure, keywords, count=3)

    greeting = f"Dear {company} Hiring Team,"

    first_sentence = structure["summary"].split(".")[0].strip()
    opening = (
        f"I am writing to apply for the {role} position at {company}. "
        f"{first_sentence}."
    )

    body_paragraphs = []
    if len(top) >= 1:
        body_paragraphs.append(f"In my most recent role, I {_lead_lower(top[0])}")
    if len(top) >= 2:
        body_paragraphs.append(f"I have also {_lead_lower(top[1])}")
    if len(top) >= 3:
        body_paragraphs.append(f"Outside of my professional work, {_lead_lower(top[2])}")

    closing = (
        f"I would welcome the opportunity to bring this experience to {company} "
        f"as part of my mandatory internship (Pflichtpraktikum), and I am able "
        f"to start according to your programme's requirements. Thank you for "
        f"considering my application - I look forward to the possibility of "
        f"speaking with you."
    )

    return {
        "greeting": greeting,
        "opening": opening,
        "body_paragraphs": body_paragraphs,
        "closing": closing,
        "signoff": "Sincerely,",
    }