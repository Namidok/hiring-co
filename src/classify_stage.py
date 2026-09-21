from llm import ask_json
from profile_schema import CareerStage

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "career_stage": {
            "type": "string",
            "enum": [s.value for s in CareerStage],
        },
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["career_stage", "confidence", "reasoning"],
}

PROMPT_TEMPLATE = """Classify this person's career stage for a job-search tool, based
on the extracted CV fields below.

Categories:
- student_no_experience: currently studying (degree_status is "in_progress"
  or "expected_<future date>"), no full-time professional roles before or
  during study
- student_with_experience: currently studying (degree_status is "in_progress"
  or "expected_<future date>"), AND has 1+ years of full-time professional
  experience from before starting the current degree
- graduate_seeking_first_role: degree_status is "completed" (studies are
  FULLY finished, not "expected"), has little/no full-time professional
  experience
- experienced_switching: degree_status is "completed" (or education is
  incidental to their career), has significant (2+ years) full-time
  professional experience

IMPORTANT: if degree_status starts with "expected_", the person is still
studying RIGHT NOW - do not treat "expected" as equivalent to "completed" or
assume they are close to finishing. Only use graduate_/experienced_ categories
when degree_status is exactly "completed".

confidence: 0.0-1.0. Use a LOW confidence (below 0.7) if the CV is genuinely
ambiguous - e.g. unclear whether studies are ongoing, unclear if experience
counts as full-time, mixed signals about intent.

Extracted profile:
{profile_json}
"""


def classify(profile_data: dict) -> dict:
    import json
    prompt = PROMPT_TEMPLATE.format(profile_json=json.dumps(profile_data, indent=2))
    return ask_json(prompt, CLASSIFY_SCHEMA)


if __name__ == "__main__":
    from extract_profile import extract_profile
    data = extract_profile()
    result = classify(data)
    print(result)