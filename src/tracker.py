"""
Agent 5, part 1: the application tracker. A single CSV file
(results/applications.csv) is the source of truth for every application
sent - one row per posting, added when you actually submit an
application (never automatically - nothing in this project auto-
applies). check_inbox.py updates each row's `status` as replies come in.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

TRACKER_PATH = Path("results/applications.csv")
FIELDNAMES = [
    "referenznummer", "company", "title", "fit_score", "verdict",
    "date_applied", "cv_file", "cover_letter_file", "status", "last_updated",
]


def _read_rows() -> list[dict]:
    if not TRACKER_PATH.is_file():
        return []
    with TRACKER_PATH.open(newline="") as f:
        return list(csv.DictReader(f))


def _write_rows(rows: list[dict]) -> None:
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACKER_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def load_tracker() -> list[dict]:
    return _read_rows()


def mark_applied(posting: dict, cv_file: str = "", cover_letter_file: str = "") -> dict:
    """
    Records that you have submitted an application for this posting.
    Call this yourself, by hand, right after you actually click submit -
    nothing in this project does it for you. If the posting's
    referenznummer is already tracked, updates that row instead of
    duplicating it.
    """
    rows = _read_rows()
    ref = str(posting.get("referenznummer", ""))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    row = {
        "referenznummer": ref,
        "company": posting.get("company", ""),
        "title": posting.get("title", ""),
        "fit_score": posting.get("fit_score", ""),
        "verdict": posting.get("verdict", ""),
        "date_applied": now,
        "cv_file": cv_file,
        "cover_letter_file": cover_letter_file,
        "status": "applied",
        "last_updated": now,
    }

    for i, existing in enumerate(rows):
        if existing["referenznummer"] == ref:
            rows[i] = row
            _write_rows(rows)
            return row

    rows.append(row)
    _write_rows(rows)
    return row


def update_status(referenznummer: str, new_status: str) -> bool:
    """Updates the status of an already-tracked application. Returns
    False if no row matches that referenznummer."""
    rows = _read_rows()
    ref = str(referenznummer)
    updated = False
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for row in rows:
        if row["referenznummer"] == ref:
            row["status"] = new_status
            row["last_updated"] = now
            updated = True
    if updated:
        _write_rows(rows)
    return updated


def find_by_company(company: str) -> list[dict]:
    company_lower = company.strip().lower()
    return [r for r in _read_rows() if r["company"].strip().lower() == company_lower]


if __name__ == "__main__":
    rows = load_tracker()
    print(f"{len(rows)} tracked application(s)")
    for r in rows:
        print(f"  [{r['status']:10}] {r['company']} - {r['title']} ({r['referenznummer']})")