"""
Fetches a posting's real public job-detail page (Bundesagentur fur Arbeit
jobsuche site) and asks the local LLM to extract a short structured
summary from it - location, skillset, and language level - since the
search API only returns summary fields (title/company/location), not
the actual job description. Used only for the Telegram notification;
never used for ranking or CV/cover-letter content, which stay sourced
from the real CV and never from a posting's description.
"""
import html as html_module
import re

import requests

from llm import ask_json

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "skillset": {"type": "string"},
        "language_level": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["location", "skillset", "language_level", "summary"],
}

SUMMARY_PROMPT = """Extract a short structured summary from this job posting's page text.

location: city/region the role is based in, or "not specified" if unclear.
skillset: the key skills/technologies/qualifications required, as a short
comma-separated phrase (not a full sentence).
language_level: any stated language requirement (e.g. "German C1", "English
fluent"), or "not specified" if the page doesn't mention one. Never invent a
requirement that isn't in the text.
summary: 1-2 plain sentences describing what the role actually involves,
based only on the text given.

PAGE TEXT:
{page_text}
"""


def _strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw_html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html_module.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_job_url(referenznummer: str) -> str:
    return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{referenznummer}"


def fetch_job_text(referenznummer: str, max_chars: int = 6000) -> str:
    url = build_job_url(referenznummer)
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    text = _strip_html(r.text)
    return text[:max_chars]


def summarize_posting(referenznummer: str) -> dict:
    """
    Returns {"location", "skillset", "language_level", "summary", "url"}.
    Falls back to placeholder values (never raises) if the page can't be
    fetched or parsed - a failed summary shouldn't block CV/cover-letter
    generation or the rest of a Telegram notification.
    """
    url = build_job_url(referenznummer)
    try:
        page_text = fetch_job_text(referenznummer)
        result = ask_json(SUMMARY_PROMPT.format(page_text=page_text), SUMMARY_SCHEMA)
        result["url"] = url
        return result
    except Exception as e:
        return {
            "location": "not available",
            "skillset": "not available",
            "language_level": "not available",
            "summary": f"(could not fetch job details: {e})",
            "url": url,
        }


if __name__ == "__main__":
    import sys
    ref = sys.argv[1] if len(sys.argv) > 1 else "10000-1189233935-S"
    print(summarize_posting(ref))