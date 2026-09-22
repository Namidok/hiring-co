"""
Per-posting bullet selection: reorders (never invents or rewrites) each
CV entry's bullets by relevance to a specific job posting's title and
ranking reasoning, so the most relevant bullets under each job/project
surface first for that particular role. Content is 100% unchanged from
the real CV - only order changes. Deterministic keyword-overlap scoring,
no LLM involved, so results are reproducible and auditable.
"""
import re

_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
    "is", "are", "we", "you", "our", "your", "as", "at", "by", "be", "will",
    "this", "that", "have", "has", "from", "into", "such", "including",
    "etc", "job", "role", "position", "work", "team", "years", "experience",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.]*")


def _tokenize(text: str) -> set[str]:
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _posting_keywords(posting: dict) -> set[str]:
    parts = [
        posting.get("title", ""),
        posting.get("description", ""),
        posting.get("reasoning", ""),
    ]
    return _tokenize(" ".join(p for p in parts if p))


def _score_bullet(bullet_text: str, keywords: set[str]) -> int:
    return len(_tokenize(bullet_text) & keywords)


def _reorder_bullets(bullets: list[str], keywords: set[str]) -> list[str]:
    scored = list(enumerate(bullets))
    scored.sort(key=lambda pair: (-_score_bullet(pair[1], keywords), pair[0]))
    return [b for _, b in scored]


def customize_structure(structure: dict, posting: dict) -> dict:
    """
    Returns a NEW structure dict (does not mutate the input) with every
    experience/project entry's bullets reordered, most relevant to this
    posting first. Entry order, headers, skills and education are left
    untouched - this is emphasis, not rewriting.
    """
    keywords = _posting_keywords(posting)
    if not keywords:
        return structure

    new_structure = dict(structure)
    new_structure["experience"] = [
        {**entry, "bullets": _reorder_bullets(entry["bullets"], keywords)}
        for entry in structure["experience"]
    ]
    new_structure["projects"] = [
        {**entry, "bullets": _reorder_bullets(entry["bullets"], keywords)}
        for entry in structure["projects"]
    ]
    return new_structure