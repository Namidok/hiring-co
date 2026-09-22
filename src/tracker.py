"""
Agent 5, part 1: the application tracker. A single CSV file
(results/applications.csv) is the source of truth for every posting
that's gone through this pipeline, one row per posting.

Two stages:
- "ready_to_apply": auto-logged the moment a CV/cover letter is
  generated (generate_cvs_batch.py calls mark_ready() for every
  posting it produces files for) - no manual step needed for this part.
- "applied": you flip it yourself, after you've actually submitted the
  application, via `python src/mark_applied.py <referenznummer>`. This
  stays manual on purpose - generating a CV isn't the same as deciding
  to apply, and the tracker should reflect what you actually sent.

check_inbox.py updates status further (interview_invite / rejected /
assessment_received) once you're past "applied".
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

TRACKER_PATH = Path("results/applications.csv")
FIELDNAMES = [
    "referenznummer", "company", "title", "fit_score", "verdict",
    "date_generated", "date_applied", "cv_file", "cover_letter_file",
    "status", "last_updated",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def mark_ready(posting: dict, cv_file: str = "", cover_letter_file: str = "") -> dict:
    """
    Auto-called whenever a CV/cover letter is generated for a posting.
    Logs it as "ready_to_apply". Never downgrades a row that's already
    past that stage (applied / interview_invite / etc.) - regenerating
    files for an already-applied posting shouldn't reset its status.
    """
    rows = _read_rows()
    ref = str(posting.get("referenznummer", ""))
    now = _now()

    for i, existing in enumerate(rows):
        if existing["referenznummer"] == ref:
            if existing.get("status") not in ("", "ready_to_apply"):
                return existing  # already applied or further along - leave it alone
            rows[i].update({
                "company": posting.get("company", ""),
                "title": posting.get("title", ""),
                "fit_score": posting.get("fit_score", ""),
                "verdict": posting.get("verdict", ""),
                "date_generated": now,
                "cv_file": cv_file,
                "cover_letter_file": cover_letter_file,
                "status": "ready_to_apply",
                "last_updated": now,
            })
            _write_rows(rows)
            return rows[i]

    row = {
        "referenznummer": ref,
        "company": posting.get("company", ""),
        "title": posting.get("title", ""),
        "fit_score": posting.get("fit_score", ""),
        "verdict": posting.get("verdict", ""),
        "date_generated": now,
        "date_applied": "",
        "cv_file": cv_file,
        "cover_letter_file": cover_letter_file,
        "status": "ready_to_apply",
        "last_updated": now,
    }
    rows.append(row)
    _write_rows(rows)
    return row


def mark_applied(referenznummer: str, cv_file: str = "", cover_letter_file: str = "") -> dict:
    """
    Flips an existing "ready_to_apply" row to "applied" and stamps
    date_applied - call this yourself, by hand, right after you actually
    submit an application. If the posting was never auto-tracked (e.g.
    a CV generated outside the normal pipeline), creates a fresh row
    instead, using whatever cv_file/cover_letter_file you pass in.
    """
    rows = _read_rows()
    ref = str(referenznummer)
    now = _now()

    for row in rows:
        if row["referenznummer"] == ref:
            row["status"] = "applied"
            row["date_applied"] = now
            row["last_updated"] = now
            if cv_file:
                row["cv_file"] = cv_file
            if cover_letter_file:
                row["cover_letter_file"] = cover_letter_file
            _write_rows(rows)
            return row

    row = {
        "referenznummer": ref,
        "company": "",
        "title": "",
        "fit_score": "",
        "verdict": "",
        "date_generated": "",
        "date_applied": now,
        "cv_file": cv_file,
        "cover_letter_file": cover_letter_file,
        "status": "applied",
        "last_updated": now,
    }
    rows.append(row)
    _write_rows(rows)
    return row


def update_status(referenznummer: str, new_status: str) -> bool:
    """Updates the status of an already-tracked application. Returns
    False if no row matches that referenznummer."""
    rows = _read_rows()
    ref = str(referenznummer)
    updated = False
    now = _now()
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
    print(f"{len(rows)} tracked posting(s)")
    for r in rows:
        print(f"  [{r['status']:15}] {r['company']} - {r['title']} ({r['referenznummer']})")