"""
Agent 4 batch mode: given a file of ranked postings (one JSON object per
line, as written by rank_jobs.rank_all() to results/ranked/{date}.jsonl,
or by run_loop.run_once() / hiring_co.py to results/new/{timestamp}.jsonl),
generate one CV + one cover letter per posting, both customized per role -
the CV's bullets/projects reordered by relevance (select_bullets), the
cover letter built from the same real content (cover_letter_content).
Content is always the real, verbatim CV content - only selection/order
changes per posting, nothing is invented.

Every generated posting is also auto-logged in the tracker
(tracker.mark_ready) as "ready_to_apply" - generating files doesn't mean
you've applied, so this never marks anything "applied" on its own; that
stays a manual step via mark_applied.py once you actually submit.

Filenames:
    results/cvs/cv_{company}_{role}.pdf
    results/covers/cover_{company}_{role}.pdf

Usage:
    python src/generate_cvs_batch.py
        -> finds the most recent file under results/ranked/, falls back
           to the most recent file under results/new/ if ranked/ is empty
    python src/generate_cvs_batch.py path/to/postings.jsonl
        -> uses that file explicitly

Postings with verdict "not_a_fit" are skipped by default (no point
generating an application for a role that isn't a fit) - pass --all to
generate for every posting in the file regardless of verdict.
"""
import json
import re
import sys
from pathlib import Path

from cv_structure import load_cv_structure
from generate_cv import render_cv
from select_bullets import customize_structure
from cover_letter_content import build_cover_letter
from generate_cover_letter import render_cover_letter
from tracker import mark_ready

RANKED_DIR = Path("results/ranked")
NEW_DIR = Path("results/new")
CV_OUTPUT_DIR = Path("results/cvs")
COVER_OUTPUT_DIR = Path("results/covers")


def _latest_file(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    files = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _resolve_input_path(cli_arg: str | None) -> Path:
    if cli_arg:
        path = Path(cli_arg)
        if not path.is_file():
            raise FileNotFoundError(f"no such file: {path}")
        return path
    path = _latest_file(RANKED_DIR)
    if path is not None:
        return path
    path = _latest_file(NEW_DIR)
    if path is not None:
        return path
    raise FileNotFoundError(
        "no postings file found - looked in results/ranked/ and results/new/"
    )


def _sanitize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _load_postings(path: Path) -> list[dict]:
    postings = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                postings.append(json.loads(line))
    return postings


def generate_batch(input_path: str | None = None, include_all: bool = False) -> list[dict]:
    """
    Returns a list of {"posting": dict, "cv_path": Path, "cover_path": Path}
    - one entry per posting a CV/cover letter was generated for, in the
    same order as the input file (after the not_a_fit filter). Each
    posting is also auto-logged in the tracker as "ready_to_apply".
    """
    path = _resolve_input_path(input_path)
    postings = _load_postings(path)

    if not include_all:
        postings = [p for p in postings if p.get("verdict") != "not_a_fit"]

    CV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    COVER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_structure = load_cv_structure()

    results = []
    seen_names = set()

    for posting in postings:
        company = _sanitize(posting.get("company", "unknown"))
        role = _sanitize(posting.get("title", "unknown"))
        base_key = f"{company}_{role}"

        key = base_key
        if key in seen_names:
            ref = _sanitize(str(posting.get("referenznummer", "")))
            key = f"{base_key}_{ref}"
        seen_names.add(key)

        structure = customize_structure(base_structure, posting)

        cv_path = CV_OUTPUT_DIR / f"cv_{key}.pdf"
        render_cv(structure, str(cv_path))

        letter = build_cover_letter(structure, posting)
        cover_path = COVER_OUTPUT_DIR / f"cover_{key}.pdf"
        render_cover_letter(letter, structure["header"], str(cover_path))

        mark_ready(posting, cv_file=str(cv_path), cover_letter_file=str(cover_path))

        results.append({"posting": posting, "cv_path": cv_path, "cover_path": cover_path})

    return results


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    include_all = "--all" in sys.argv
    if arg == "--all":
        arg = None

    results = generate_batch(arg, include_all=include_all)
    print(f"generated {len(results)} CV(s) + cover letter(s) (logged as ready_to_apply):")
    for r in results:
        p = r["posting"]
        print(f"  {p.get('company')} - {p.get('title')}")
        print(f"    {r['cv_path']}")
        print(f"    {r['cover_path']}")