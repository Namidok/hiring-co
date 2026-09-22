"""
Quick manual command for after you've actually submitted an application:
finds the posting by referenznummer in the most recent ranked/new
postings file, and records it in the tracker along with the CV/cover-
letter files that were generated for it (if they exist).

Usage:
    python src/mark_applied.py <referenznummer>
"""
import sys

from generate_cvs_batch import (
    _resolve_input_path, _load_postings, _sanitize,
    CV_OUTPUT_DIR, COVER_OUTPUT_DIR,
)
from tracker import mark_applied


def main(referenznummer: str) -> None:
    path = _resolve_input_path(None)
    postings = _load_postings(path)
    posting = next(
        (p for p in postings if str(p.get("referenznummer")) == referenznummer),
        None,
    )
    if posting is None:
        print(f"no posting with referenznummer {referenznummer} found in {path}")
        return

    company = _sanitize(posting.get("company", "unknown"))
    role = _sanitize(posting.get("title", "unknown"))
    cv_file = CV_OUTPUT_DIR / f"cv_{company}_{role}.pdf"
    cover_file = COVER_OUTPUT_DIR / f"cover_{company}_{role}.pdf"

    row = mark_applied(
        posting,
        cv_file=str(cv_file) if cv_file.is_file() else "",
        cover_letter_file=str(cover_file) if cover_file.is_file() else "",
    )
    print(f"tracked: {row['company']} - {row['title']} ({row['referenznummer']}) as 'applied'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python src/mark_applied.py <referenznummer>")
        sys.exit(1)
    main(sys.argv[1])