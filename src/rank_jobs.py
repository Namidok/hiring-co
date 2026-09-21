import json
from llm import ask_json

RANK_SCHEMA = {
    "type": "object",
    "properties": {
        "fit_score": {"type": "number"},
        "verdict": {"type": "string", "enum": ["strong_fit", "moderate_fit", "weak_fit", "not_a_fit"]},
        "reasoning": {"type": "string"},
    },
    "required": ["fit_score", "verdict", "reasoning"],
}

PROMPT_TEMPLATE_NATIONWIDE = """Score how well this job posting fits this candidate's profile.

fit_score: 0.0-1.0, how well the role matches the candidate's actual skills,
experience level, and stated target roles.

verdict:
- strong_fit: role matches target_roles closely, skills align, right seniority
- moderate_fit: partial match - some skills/domain overlap but not central
- weak_fit: tangential match only (e.g. keyword overlap but wrong domain)
- not_a_fit: role is clearly wrong (wrong seniority, unrelated field, language
  requirement the candidate doesn't meet, etc.)

reasoning: 1-2 sentences citing SPECIFIC evidence from the profile and posting -
not generic praise. Cite ONLY fields explicitly given below.

Hard rule: Do NOT comment on whether the candidate's language level is
sufficient, adequate, or appropriate for this posting. We have NO language
requirement data for any posting - any such claim is invented. You may state
the candidate's language level as a fact about them, but never judge it
against a job requirement that was not given to you.

The candidate is searching nationwide across all of Germany, so location and
country are NOT part of this evaluation - the job's location has been left
out of this prompt on purpose. Do not mention location, city, or country
anywhere in your reasoning. Base your reasoning only on role/title, skills,
domain, and seniority.

If it's a weak/not fit, say exactly why using only the given fields.

CANDIDATE PROFILE:
{profile_json}

JOB POSTING:
Title: {title}
Company: {company}
Type: {job_type}
"""

PROMPT_TEMPLATE_LOCATION_SPECIFIC = """Score how well this job posting fits this candidate's profile.

fit_score: 0.0-1.0, how well the role matches the candidate's actual skills,
experience level, and stated target roles.

verdict:
- strong_fit: role matches target_roles closely, skills align, right seniority
- moderate_fit: partial match - some skills/domain overlap but not central
- weak_fit: tangential match only (e.g. keyword overlap but wrong domain)
- not_a_fit: role is clearly wrong (wrong seniority, unrelated field, language
  requirement the candidate doesn't meet, etc.)

reasoning: 1-2 sentences citing SPECIFIC evidence from the profile and posting -
not generic praise. Cite ONLY fields explicitly given below.

Hard rule: Do NOT comment on whether the candidate's language level is
sufficient, adequate, or appropriate for this posting. We have NO language
requirement data for any posting - any such claim is invented. You may state
the candidate's language level as a fact about them, but never judge it
against a job requirement that was not given to you.

The candidate has a specific target_location preference. You may cite
location as evidence only if the posting's city/region is a poor match for
that preference (e.g. a different region entirely) - do not cite a match as
positive evidence, since proximity alone doesn't indicate role fit.

If it's a weak/not fit, say exactly why using only the given fields.

CANDIDATE PROFILE:
{profile_json}

JOB POSTING:
Title: {title}
Company: {company}
Location: {location}
Type: {job_type}
"""


def _is_nationwide(target_location: str | None) -> bool:
    return not target_location or target_location.strip().lower() == "germany"


def rank_posting(profile: dict, posting: dict) -> dict:
    location = posting.get("stellenlokationen", [{}])[0].get("adresse", {}).get("ort", "unknown")
    nationwide = _is_nationwide(profile.get("target_location"))

    if nationwide:
        prompt = PROMPT_TEMPLATE_NATIONWIDE.format(
            profile_json=json.dumps(profile, indent=2),
            title=posting.get("stellenangebotsTitel", "?"),
            company=posting.get("firma", "?"),
            job_type=posting.get("stellenangebotsart", "?"),
        )
    else:
        prompt = PROMPT_TEMPLATE_LOCATION_SPECIFIC.format(
            profile_json=json.dumps(profile, indent=2),
            title=posting.get("stellenangebotsTitel", "?"),
            company=posting.get("firma", "?"),
            location=location,
            job_type=posting.get("stellenangebotsart", "?"),
        )
    return ask_json(prompt, RANK_SCHEMA)


def rank_all(profile: dict, postings: list[dict]) -> list[dict]:
    ranked = []
    total = len(postings)
    for i, posting in enumerate(postings, start=1):
        print(f"  [{i}/{total}] {posting.get('stellenangebotsTitel', '?')[:60]}", flush=True)
        result = rank_posting(profile, posting)
        ranked.append({
            "fit_score": result["fit_score"],
            "verdict": result["verdict"],
            "reasoning": result["reasoning"],
            "title": posting.get("stellenangebotsTitel", "?"),
            "company": posting.get("firma", "?"),
            "referenznummer": posting.get("referenznummer"),
        })
    ranked.sort(key=lambda r: r["fit_score"], reverse=True)
    return ranked


if __name__ == "__main__":
    from datetime import date
    from pathlib import Path

    with open("profiles/profile.json") as f:
        profile = json.load(f)

    with open("results/postings_raw/2026-09-21.jsonl") as f:
        postings = [json.loads(line) for line in f]

    print(f"ranking {len(postings)} postings...")
    ranked = rank_all(profile, postings)

    out_dir = Path("results/ranked")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date.today().isoformat()}.jsonl"
    with open(out_path, "w") as f:
        for r in ranked:
            f.write(json.dumps(r) + "\n")

    counts = {}
    for r in ranked:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print(f"wrote {out_path}")
    print(f"verdicts: {counts}")
    print("\ntop 10:")
    for r in ranked[:10]:
        print(f"[{r['fit_score']:.2f}] {r['verdict']:12} {r['title']} @ {r['company']}")