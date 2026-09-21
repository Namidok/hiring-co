import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rank_jobs import _is_nationwide, rank_posting
from conftest import requires_ollama


def test_is_nationwide_true_for_germany():
    assert _is_nationwide("Germany") is True


def test_is_nationwide_true_for_none():
    assert _is_nationwide(None) is True


def test_is_nationwide_false_for_specific_city():
    assert _is_nationwide("Berlin") is False


@requires_ollama
def test_rank_posting_nationwide_omits_location_language():
    profile = {
        "name": "Test Candidate",
        "years_experience": 3,
        "current_role_type": "Application Developer",
        "target_roles": ["Software Engineering Praktikum", "Data Engineering Praktikum"],
        "target_location": "Germany",
        "career_stage": "student_with_experience",
    }
    posting = {
        "stellenangebotsTitel": "Werkstudent Software Engineering",
        "firma": "Test GmbH",
        "stellenangebotsart": "PRAKTIKUM_TRAINEE",
        "stellenlokationen": [{"adresse": {"ort": "Munich"}}],
    }
    result = rank_posting(profile, posting)
    reasoning_lower = result["reasoning"].lower()
    forbidden = ["location", "city", "munich", "germany", "berlin", "country"]
    for term in forbidden:
        assert term not in reasoning_lower, (
            f"nationwide ranking reasoning mentioned '{term}', which should have "
            f"been structurally excluded from the prompt: {result['reasoning']}"
        )


@requires_ollama
def test_rank_posting_returns_valid_shape():
    profile = {
        "name": "Test Candidate",
        "years_experience": 3,
        "current_role_type": "Application Developer",
        "target_roles": ["Software Engineering Praktikum"],
        "target_location": "Germany",
        "career_stage": "student_with_experience",
    }
    posting = {
        "stellenangebotsTitel": "Praktikant HR",
        "firma": "Test GmbH",
        "stellenangebotsart": "PRAKTIKUM_TRAINEE",
        "stellenlokationen": [{"adresse": {"ort": "Hamburg"}}],
    }
    result = rank_posting(profile, posting)
    assert 0.0 <= result["fit_score"] <= 1.0
    assert result["verdict"] in {"strong_fit", "moderate_fit", "weak_fit", "not_a_fit"}
    assert len(result["reasoning"]) > 0