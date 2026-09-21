import requests

API_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
API_KEY = "jobboerse-jobsuche"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
ANGEBOTSART_PRAKTIKUM_TRAINEE = 34  # covers Praktikum, Werkstudent, Trainee


def search_jobs(was: str, wo: str | None = None, umkreis: int = 100, size: int = 25,
                 angebotsart: int | None = ANGEBOTSART_PRAKTIKUM_TRAINEE) -> list[dict]:
    """
    Query the Bundesagentur für Arbeit job search API.

    wo=None searches nationwide - confirmed empirically to return MORE results
    than a single-city query for the same keyword (19 nationwide vs fewer for
    Berlin alone), spread genuinely across Germany (Bielefeld, Bremen, Nürnberg,
    Kiel, etc.) rather than clustering - this is the right default for a
    profile with no specific city preference, not a fallback list of "major
    cities" which would still miss smaller markets.

    Design notes from empirical testing:
    - `was` behaves like a phrase match, not a keyword OR-search. Stacking
      multiple concepts (e.g. "Software Engineer Praktikum") collapses results
      to zero even for a common role. Pass ONE role keyword per call.
    - Filter to internship-type roles via `angebotsart=34`, not by cramming
      "Praktikum" into `was` - the API's own docs show this covers Praktikum,
      Werkstudent, and Trainee together, and it's verified to only return
      correctly-tagged PRAKTIKUM_TRAINEE results.
    - Requires a browser User-Agent - their WAF 403s on default requests/curl UAs.
    """
    headers = {"X-API-Key": API_KEY, "User-Agent": USER_AGENT}
    params = {"was": was, "page": 1, "size": size}
    if wo:
        params["wo"] = wo
        params["umkreis"] = umkreis
    if angebotsart is not None:
        params["angebotsart"] = angebotsart

    r = requests.get(API_URL, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("ergebnisliste", [])


def _role_keyword(target_role: str) -> str:
    """
    Strip 'Praktikum'/'Pflichtpraktikum'/'Werkstudent' from a target_role
    string, since filtering is done via angebotsart, not the free-text query -
    keeping these words in `was` only hurts recall (see search_jobs docstring).
    """
    for noise in ["Pflichtpraktikum", "Praktikum", "Werkstudent"]:
        target_role = target_role.replace(noise, "")
    return target_role.strip()


def _is_nationwide(location: str | None) -> bool:
    return not location or location.strip().lower() == "germany"


def search_for_profile(target_roles: list[str], location: str | None = None) -> list[dict]:
    """
    One query per role keyword, merged and deduped by referenznummer.
    location=None or "Germany" searches nationwide (see search_jobs docstring).
    """
    wo = None if _is_nationwide(location) else location
    seen = {}
    for role in target_roles:
        keyword = _role_keyword(role)
        if not keyword:
            continue
        for job in search_jobs(keyword, wo):
            seen[job["referenznummer"]] = job
    return list(seen.values())


if __name__ == "__main__":
    import json
    from datetime import date
    from pathlib import Path

    with open("profiles/profile.json") as f:
        profile = json.load(f)

    location = profile.get("target_location")
    results = search_for_profile(profile["target_roles"], location)
    scope = "nationwide" if _is_nationwide(location) else location
    print(f"found {len(results)} unique postings across {len(profile['target_roles'])} "
          f"role keywords ({scope})")

    out_dir = Path("results/postings_raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date.today().isoformat()}.jsonl"
    with open(out_path, "w") as f:
        for job in results:
            f.write(json.dumps(job) + "\n")
    print(f"wrote {out_path}")