from pathlib import Path

from parse_cv import extract_text
from llm import ask_json
from profile_schema import Profile

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "location": {"type": "string"},
        "years_experience": {"type": "number"},
        "highest_degree": {"type": "string"},
        "degree_status": {"type": "string"},
        "current_role_type": {"type": "string"},
        "languages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "level": {"type": "string"},
                },
                "required": ["language", "level"],
            },
        },
    },
    "required": [
        "name", "email", "location", "years_experience",
        "highest_degree", "degree_status", "languages",
    ],
}

PROMPT_TEMPLATE = """You are extracting structured fields from a CV for a job-search tool.
Read the CV text below and extract exactly the fields in the JSON schema.

Rules:
- years_experience: sum the duration of ALL full-time professional roles
  listed under "PROFESSIONAL EXPERIENCE" (add each role's duration together).
  Do not count the current Masters/Bachelors degree as experience. Compute
  each role's duration from its date range (e.g. "May 2023 - Aug 2025" is
  about 2.25 years), then sum across every role found.
- current_role_type: ONLY the job title of the most recent role (e.g.
  "Application Developer"), not the company name. Null if none.
- degree_status: one of "completed", "in_progress", or "expected_<date>"
  (e.g. "expected_2027") based on the CV's own wording.
- Do not invent information that is not present in the CV text.

CV TEXT:
---
{cv_text}
---
"""


def extract_profile(pdf_path: str = "profiles/cv.pdf") -> dict:
    text = extract_text(pdf_path)
    prompt = PROMPT_TEMPLATE.format(cv_text=text)
    return ask_json(prompt, EXTRACTION_SCHEMA)


if __name__ == "__main__":
    data = extract_profile()
    import json
    print(json.dumps(data, indent=2))