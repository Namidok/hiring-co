"""
Manual command for after you've actually submitted an application: flips
that posting's tracker row from "ready_to_apply" to "applied" and stamps
the date. Normally the row already exists (auto-logged by
generate_cvs_batch.py when the CV/cover letter were generated) - this
just confirms you actually sent it.

If the posting was never auto-tracked for some reason (e.g. you
generated a CV outside the normal pipeline), falls back to looking it
up in the most recent ranked/new postings file and creating the row
fresh, same as before.

Usage:
    python src/mark_applied.py <referenznummer>
"""
import sys

from generate_cvs_batch import (
    _resolve_input_path, _load_postings, _sanitize,
    CV_OUTPUT_DIR, COVER_OUTPUT_DIR,
)
from tracker import mark_applied, load_tracker


def main(referenznummer: str) -> None:
    already_tracked = any(r["referenznummer"] == referenznummer for r in load_tracker())

    if already_tracked:
        row = mark_applied(referenznummer)
        print(f"marked applied: {row['company']} - {row['title']} ({referenznummer})")
        return

    # not auto-tracked (unusual) - fall back to looking the posting up directly
    path = _resolve_input_path(None)
    postings = _load_postings(path)
    posting = next(
        (p for p in postings if str(p.get("referenznummer")) == referenznummer),
        None,
    )
    if posting is None:
        print(f"no posting with referenznummer {referenznummer} found in tracker or in {path}")
        return

    company = _sanitize(posting.get("company", "unknown"))
    role = _sanitize(posting.get("title", "unknown"))
    cv_file = CV_OUTPUT_DIR / f"cv_{company}_{role}.pdf"
    cover_file = COVER_OUTPUT_DIR / f"cover_{company}_{role}.pdf"

    row = mark_applied(
        referenznummer,
        cv_file=str(cv_file) if cv_file.is_file() else "",
        cover_letter_file=str(cover_file) if cover_file.is_file() else "",
    )
    print(f"marked applied: {posting.get('company')} - {posting.get('title')} ({referenznummer})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python src/mark_applied.py <referenznummer>")
        sys.exit(1)
    main(sys.argv[1])