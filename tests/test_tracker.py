import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import tracker


def _use_tmp_tracker(tmp_path, monkeypatch):
    tmp_file = tmp_path / "applications.csv"
    monkeypatch.setattr(tracker, "TRACKER_PATH", tmp_file)
    return tmp_file


def test_mark_applied_creates_row(tmp_path, monkeypatch):
    _use_tmp_tracker(tmp_path, monkeypatch)
    posting = {
        "referenznummer": "123", "company": "Acme", "title": "Intern",
        "fit_score": 0.9, "verdict": "strong_fit",
    }
    row = tracker.mark_applied(posting, cv_file="cv.pdf", cover_letter_file="cover.pdf")
    assert row["status"] == "applied"
    rows = tracker.load_tracker()
    assert len(rows) == 1
    assert rows[0]["company"] == "Acme"


def test_mark_applied_updates_existing_row_instead_of_duplicating(tmp_path, monkeypatch):
    _use_tmp_tracker(tmp_path, monkeypatch)
    posting = {"referenznummer": "123", "company": "Acme", "title": "Intern"}
    tracker.mark_applied(posting)
    tracker.mark_applied(posting, cv_file="cv2.pdf")
    rows = tracker.load_tracker()
    assert len(rows) == 1
    assert rows[0]["cv_file"] == "cv2.pdf"


def test_update_status_changes_matching_row(tmp_path, monkeypatch):
    _use_tmp_tracker(tmp_path, monkeypatch)
    posting = {"referenznummer": "123", "company": "Acme", "title": "Intern"}
    tracker.mark_applied(posting)
    result = tracker.update_status("123", "interview_invite")
    assert result is True
    rows = tracker.load_tracker()
    assert rows[0]["status"] == "interview_invite"


def test_update_status_returns_false_when_not_found(tmp_path, monkeypatch):
    _use_tmp_tracker(tmp_path, monkeypatch)
    assert tracker.update_status("does-not-exist", "rejected") is False


def test_find_by_company_is_case_insensitive(tmp_path, monkeypatch):
    _use_tmp_tracker(tmp_path, monkeypatch)
    tracker.mark_applied({"referenznummer": "1", "company": "Acme Corp", "title": "Intern"})
    results = tracker.find_by_company("acme corp")
    assert len(results) == 1