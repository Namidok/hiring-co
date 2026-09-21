import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from search_jobs import search_jobs, _role_keyword


def _api_reachable() -> bool:
    try:
        search_jobs("Data Engineer", "Berlin", size=1)
        return True
    except Exception:
        return False


requires_api = pytest.mark.skipif(
    not _api_reachable(),
    reason="Arbeitsagentur API not reachable - network required, not run in CI.",
)


def test_role_keyword_strips_praktikum_noise():
    """
    Regression: the API's `was` param behaves like a phrase match, not
    keyword OR-search. 'Software Engineer Praktikum' returned ZERO results
    even though internships for that role definitely exist - stacking terms
    collapses recall. Filtering happens via angebotsart instead, so these
    words must never reach the free-text query.
    """
    assert _role_keyword("Pflichtpraktikum Software Engineer") == "Software Engineer"
    assert _role_keyword("Data Engineering Praktikum") == "Data Engineering"
    assert _role_keyword("Werkstudent Data Engineering") == "Data Engineering"


@requires_api
def test_angebotsart_filter_returns_only_internship_type_roles():
    """
    Regression: verifies angebotsart=34 actually filters server-side rather
    than being a no-op - every result must be tagged PRAKTIKUM_TRAINEE.
    """
    results = search_jobs("Data Engineer", "Berlin", size=10)
    assert len(results) > 0
    assert all(job["stellenangebotsart"] == "PRAKTIKUM_TRAINEE" for job in results)


@requires_api
def test_single_keyword_returns_more_than_combined_phrase():
    """
    Regression: combined multi-concept phrases collapse recall. A single
    role keyword must return at least as many results as a longer, more
    specific combined phrase against the same role.
    """
    single = search_jobs("Data Engineer", "Berlin", angebotsart=None, size=25)
    combined = search_jobs("Werkstudent Data Engineering", "Berlin", angebotsart=None, size=25)
    assert len(single) >= len(combined)

@requires_api
def test_nationwide_search_covers_more_than_single_city():
    """
    Regression: confirmed empirically that omitting `wo` entirely returns a
    genuinely nationwide spread (Bielefeld, Bremen, Nurnberg, Kiel, etc.), not
    just more results clustered in one place. Profile default is
    target_location="Germany" (not a specific city), so `wo` must be omitted
    rather than defaulting to "Berlin" - the original bug this test guards
    against silently limited every user with no city preference to Berlin only.
    """
    nationwide = search_jobs("Data Engineer", wo=None, size=25)
    berlin_only = search_jobs("Data Engineer", wo="Berlin", size=25)
    assert len(nationwide) >= len(berlin_only)

    cities = {job["stellenlokationen"][0]["adresse"].get("ort") for job in nationwide}
    assert len(cities) > 3, f"expected spread across multiple cities, got: {cities}"