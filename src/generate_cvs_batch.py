"""
Agent 4 batch mode: given a file of ranked postings (one JSON object per
line, as written by rank_jobs.rank_all() to results/ranked/{date}.jsonl,
or by run_loop.run_once() to results/new/{timestamp}.jsonl), generate one
CV PDF per posting.

Filenames follow: cv_{company}_{role}.pdf

IMPORTANT / current limitation: this does NOT yet do per-role bullet
selection. Every generated PDF currently renders the full, unfiltered
cv_structure() - same content, different filename per posting. Real
per-role customization (choosing/reordering bullets to match each job's
emphasis) is a follow-up; wiring it in later only means swapping the
`structure` passed to render_cv() per posting for a trimmed one - the
naming/plumbing here does not need to change.

Usage:
    python src/generate_cvs_batch.py
        -> finds the most recent file under results/ranked/, falls back
           to the most recent file under results/new/ if ranked/ is empty
    python src/generate_cvs_batch.py path/to/postings.jsonl
        -> uses that file explicitly

Postings with verdict "not_a_fit" are skipped by default (no point
generating a CV for a role that isn't a fit) - pass --all to generate
for every posting in the file regardless of verdict.
"""
import json
import re
import sys
from pathlib import Path

from cv_structure import load_cv_structure
from generate_cv import render_cv

RANKED_DIR = Path("results/ranked")
NEW_DIR = Path("results/new")
OUTPUT_DIR = Path("results/cvs")


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


def generate_batch(input_path: str | None = None, include_all: bool = False) -> list[Path]:
    path = _resolve_input_path(input_path)
    postings = _load_postings(path)

    if not include_all:
        postings = [p for p in postings if p.get("verdict") != "not_a_fit"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    structure = load_cv_structure()

    written = []
    seen_names = set()
    for posting in postings:
        company = _sanitize(posting.get("company", "unknown"))
        role = _sanitize(posting.get("title", "unknown"))
        base_name = f"cv_{company}_{role}.pdf"

        # avoid silently overwriting when two postings sanitize to the
        # same name (e.g. two postings at the same company with the same
        # title) - append the referenznummer to disambiguate.
        name = base_name
        if name in seen_names:
            ref = _sanitize(str(posting.get("referenznummer", "")))
            name = f"cv_{company}_{role}_{ref}.pdf"
        seen_names.add(name)

        out_path = OUTPUT_DIR / name
        render_cv(structure, str(out_path))
        written.append(out_path)

    return written


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    include_all = "--all" in sys.argv
    if arg == "--all":
        arg = None

    results = generate_batch(arg, include_all=include_all)
    print(f"wrote {len(results)} CV(s) to {OUTPUT_DIR}/")
    for p in results:
        print(f"  {p}")