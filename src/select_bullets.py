"""
Per-posting content selection: reorders (never invents or rewrites) the
candidate's real CV content by relevance to a specific job posting's
title and ranking reasoning. Two levels of reordering:

1. Within each Professional Experience / Project entry, bullets are
   reordered so the most relevant one leads.
2. The PROJECTS entries themselves are reordered so the most relevant
   project (as a whole) appears first - Professional Experience is left
   in its original reverse-chronological order, since reordering actual
   job history is not a normal resume convention.

Content is 100% unchanged - only order changes. No LLM involved,
deterministic keyword overlap scoring, reproducible and auditable.
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


def _entry_score(entry: dict, keywords: set[str]) -> int:
    """An entry's relevance is its single most relevant bullet's score -
    one strong match should be enough to pull a project to the top."""
    if not entry["bullets"]:
        return 0
    return max(_score_bullet(b, keywords) for b in entry["bullets"])


def customize_structure(structure: dict, posting: dict) -> dict:
    """
    Returns a NEW structure dict (does not mutate the input):
    - experience: same entries, same order, bullets reordered within
      each entry only.
    - projects: bullets reordered within each entry AND the entries
      themselves reordered, most relevant project first.
    - skills and education are left untouched.
    If the posting yields no usable keywords, returns the structure
    unchanged (nothing to rank against).
    """
    keywords = _posting_keywords(posting)
    if not keywords:
        return structure

    new_structure = dict(structure)

    new_structure["experience"] = [
        {**entry, "bullets": _reorder_bullets(entry["bullets"], keywords)}
        for entry in structure["experience"]
    ]

    projects_reordered_bullets = [
        {**entry, "bullets": _reorder_bullets(entry["bullets"], keywords)}
        for entry in structure["projects"]
    ]
    scored_projects = list(enumerate(projects_reordered_bullets))
    scored_projects.sort(key=lambda pair: (-_entry_score(pair[1], keywords), pair[0]))
    new_structure["projects"] = [entry for _, entry in scored_projects]

    return new_structure