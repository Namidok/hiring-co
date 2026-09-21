import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extract_profile import extract_profile


def test_extraction_against_known_cv():
    """
    Regression test: locks in the fix for two bugs found during development -
    years_experience under-counting (only summed one role, not both) and
    current_role_type including the company name instead of just the title.
    Requires Ollama running locally with qwen3:8b pulled.
    """
    data = extract_profile("profiles/cv.pdf")

    assert data["name"] == "SRIKAR KODI"
    assert "@" in data["email"]
    assert data["years_experience"] >= 3.0, (
        f"expected >=3.0 (CV states 3 years), got {data['years_experience']} "
        "- possible regression in the years_experience prompt rule"
    )
    assert data["current_role_type"] == "Application Developer", (
        f"expected bare job title, got {data['current_role_type']!r} "
        "- possible regression: company name leaking back into the field"
    )
    assert data["degree_status"].startswith("expected") or data["degree_status"] == "in_progress"