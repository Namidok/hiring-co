import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classify_stage import classify

from conftest import requires_ollama

@requires_ollama
def test_student_with_experience_not_misclassified_as_graduate():
    ...

@requires_ollama
def test_completed_degree_with_experience_is_experienced_switching():
    ...

@requires_ollama
def test_no_experience_currently_studying_is_student_no_experience():
    ...


def test_student_with_experience_not_misclassified_as_graduate():
    """
    Regression test for a real bug: the model saw degree_status='expected_2027'
    and invented an unsupported claim ("final year of studies") to justify
    classifying as graduate_seeking_first_role. 'expected_<date>' means still
    studying now, regardless of how far the date is - this must never be
    treated as equivalent to 'completed'.
    """
    profile = {
        "name": "Test Person",
        "email": "test@example.com",
        "location": "Berlin, Germany",
        "years_experience": 3,
        "highest_degree": "MSc Computer Science",
        "degree_status": "expected_2027",
        "current_role_type": "Application Developer",
        "languages": [],
    }
    result = classify(profile)
    assert result["career_stage"] == "student_with_experience", (
        f"got {result['career_stage']!r} - possible regression of the "
        f"expected_2027-treated-as-completed bug. reasoning was: "
        f"{result['reasoning']!r}"
    )


def test_completed_degree_with_experience_is_experienced_switching():
    profile = {
        "name": "Test Person",
        "email": "test@example.com",
        "location": "Berlin, Germany",
        "years_experience": 5,
        "highest_degree": "BSc Computer Science",
        "degree_status": "completed",
        "current_role_type": "Software Engineer",
        "languages": [],
    }
    result = classify(profile)
    assert result["career_stage"] == "experienced_switching"


def test_no_experience_currently_studying_is_student_no_experience():
    profile = {
        "name": "Test Person",
        "email": "test@example.com",
        "location": "Berlin, Germany",
        "years_experience": 0,
        "highest_degree": "BSc Computer Science",
        "degree_status": "in_progress",
        "current_role_type": None,
        "languages": [],
    }
    result = classify(profile)
    assert result["career_stage"] == "student_no_experience"