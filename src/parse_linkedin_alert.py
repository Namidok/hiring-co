"""
Parses LinkedIn "job alert" emails into the same posting shape used by
search_jobs.py, so Agent 3 (rank_jobs.py) can rank LinkedIn postings
alongside Bundesagentur postings without caring where they came from.

ASSUMPTION (not yet verified against a real email - calibrate on first
real sample): LinkedIn job-alert emails contain repeated blocks, each
with:
  - a link to /jobs/view/<numeric_id> whose link text is the job title
  - a company name as plain text near the title
  - a location as plain text near the company name
This matches LinkedIn's publicly documented alert format as of recent
years, but LinkedIn changes email templates without notice, so treat
this as a first draft to be corrected once real samples are available.

This module only parses text/HTML you already have in hand (e.g. a
.eml file you exported, or an email body Agent 5 hands it later). It
does not fetch anything from LinkedIn itself - no scraping, no login,
no automation of LinkedIn's site. The user sets up the alerts as
first-party opt-in email subscriptions in their own LinkedIn account;
this just parses the resulting email.
"""
import re
from html import unescape

JOB_LINK_RE = re.compile(
    r'href="(https://www\.linkedin\.com/jobs/view/(\d+)[^"]*)"[^>]*>([^<]+)</a>',
    re.IGNORECASE,
)


def _clean(text: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", text)).strip()


def parse_alert_email(raw_html: str) -> list[dict]:
    """
    Extract job postings from a LinkedIn job-alert email.

    Returns a list of dicts shaped like:
        {
            "source": "linkedin",
            "job_id": "<numeric linkedin job id>",
            "title": "...",
            "url": "https://www.linkedin.com/jobs/view/<id>",
            "company": "..." | None,
            "location": "..." | None,
        }

    company/location extraction is best-effort: LinkedIn's email HTML
    doesn't cleanly tag these fields, so we look at the text immediately
    following each job link and split on the first line break or bullet
    separator. If this comes back None often once we see a real sample,
    that's the first thing to fix.
    """
    postings = []
    seen_ids = set()

    for match in JOB_LINK_RE.finditer(raw_html):
        url, job_id, title_raw = match.groups()
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        title = _clean(title_raw)
        if not title:
            continue

        # Look at a window of text right after the link for company/location.
        window = raw_html[match.end():match.end() + 400]
        window_text = _clean(window)
        company, location = _split_company_location(window_text)

        postings.append({
            "source": "linkedin",
            "job_id": job_id,
            "title": title,
            "url": url.split("?")[0],
            "company": company,
            "location": location,
        })

    return postings


def _split_company_location(window_text: str) -> tuple[str | None, str | None]:
    """
    Best-effort split of the trailing text after a job link into
    (company, location). LinkedIn commonly separates these with a
    middle dot (·) or a line break; fall back to None/None rather
    than fabricating a value if the pattern isn't recognized.
    """
    if not window_text:
        return None, None
    for sep in ["\u00b7", "|", "-"]:
        if sep in window_text:
            parts = [p.strip() for p in window_text.split(sep) if p.strip()]
            if len(parts) >= 2:
                return parts[0], parts[1]
    return None, None


def to_posting_shape(linkedin_job: dict) -> dict:
    """
    Adapts a parsed LinkedIn job dict into the minimal shape rank_jobs.py
    expects (same fields search_jobs.py postings carry: stellenangebotsTitel,
    firma, stellenangebotsart, stellenlokationen, referenznummer), so it can
    go through rank_posting() unmodified.
    """
    return {
        "stellenangebotsTitel": linkedin_job["title"],
        "firma": linkedin_job.get("company") or "unknown",
        "stellenangebotsart": "LINKEDIN",
        "stellenlokationen": [
            {"adresse": {"ort": linkedin_job.get("location") or "unknown"}}
        ],
        "referenznummer": f"linkedin-{linkedin_job['job_id']}",
        "url": linkedin_job["url"],
    }