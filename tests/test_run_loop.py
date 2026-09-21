import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_loop


def test_load_seen_returns_empty_set_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(run_loop, "SEEN_FILE", tmp_path / "seen.json")
    assert run_loop.load_seen() == set()


def test_save_and_load_seen_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(run_loop, "SEEN_FILE", tmp_path / "seen.json")
    run_loop.save_seen({"ref-1", "ref-2"})
    assert run_loop.load_seen() == {"ref-1", "ref-2"}


def test_run_once_skips_already_seen_postings(tmp_path, monkeypatch):
    monkeypatch.setattr(run_loop, "SEEN_FILE", tmp_path / "seen.json")
    monkeypatch.setattr(run_loop, "NEW_DIR", tmp_path / "new")

    all_postings = [
        {"referenznummer": "ref-1", "stellenangebotsTitel": "Old job"},
        {"referenznummer": "ref-2", "stellenangebotsTitel": "New job"},
    ]

    def fake_search_for_profile(target_roles, location):
        return all_postings

    captured = {}

    def fake_rank_all(profile, postings):
        captured["ranked_postings"] = postings
        return [
            {"fit_score": 0.9, "verdict": "strong_fit", "reasoning": "x",
             "title": p["stellenangebotsTitel"], "company": "?",
             "referenznummer": p["referenznummer"]}
            for p in postings
        ]

    monkeypatch.setattr(run_loop, "search_for_profile", fake_search_for_profile)
    monkeypatch.setattr(run_loop, "rank_all", fake_rank_all)

    profile = {"target_roles": ["Software Engineering"], "target_location": "Germany"}
    seen = {"ref-1"}  # ref-1 already seen, ref-2 is new

    updated_seen = run_loop.run_once(profile, seen)

    # only the new posting should have been ranked
    assert len(captured["ranked_postings"]) == 1
    assert captured["ranked_postings"][0]["referenznummer"] == "ref-2"

    # both postings are now marked seen after this run
    assert updated_seen == {"ref-1", "ref-2"}

    # seen file was persisted
    assert set(json.loads((tmp_path / "seen.json").read_text())) == {"ref-1", "ref-2"}


def test_run_once_writes_nothing_when_no_new_postings(tmp_path, monkeypatch):
    monkeypatch.setattr(run_loop, "SEEN_FILE", tmp_path / "seen.json")
    monkeypatch.setattr(run_loop, "NEW_DIR", tmp_path / "new")

    all_postings = [{"referenznummer": "ref-1", "stellenangebotsTitel": "Old job"}]
    monkeypatch.setattr(run_loop, "search_for_profile", lambda roles, loc: all_postings)

    def fake_rank_all(profile, postings):
        raise AssertionError("rank_all should not be called when there are no new postings")

    monkeypatch.setattr(run_loop, "rank_all", fake_rank_all)

    profile = {"target_roles": ["Software Engineering"], "target_location": "Germany"}
    seen = {"ref-1"}

    run_loop.run_once(profile, seen)

    assert not (tmp_path / "new").exists()