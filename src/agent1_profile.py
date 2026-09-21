import json
from pathlib import Path

from extract_profile import extract_profile
from classify_stage import classify
from profile_schema import Profile

CONFIDENCE_THRESHOLD = 0.7
PROFILE_OUT = Path("profiles/profile.json")


def ask_clarifying_questions(extracted: dict, classification: dict) -> dict:
    """
    Low-confidence classification: ask the user directly rather than guess.
    Returns answers merged into a dict ready for the Profile schema.
    """
    print("\nI'm not fully confident about your career stage from the CV alone.")
    print(f"Best guess: {classification['career_stage']} "
          f"(confidence {classification['confidence']:.2f})")
    print(f"Reasoning: {classification['reasoning']}\n")

    print("A couple of questions to get this right:")
    stage = input(
        "Which best describes you right now?\n"
        "  1) Student, no professional experience\n"
        "  2) Student, WITH prior professional experience\n"
        "  3) Graduated, looking for my first role\n"
        "  4) Experienced, looking to switch roles/domains\n"
        "> "
    ).strip()

    stage_map = {
        "1": "student_no_experience",
        "2": "student_with_experience",
        "3": "graduate_seeking_first_role",
        "4": "experienced_switching",
    }
    confirmed_stage = stage_map.get(stage, classification["career_stage"])
    return {"career_stage": confirmed_stage, "career_stage_confidence": 1.0}


def ask_search_preferences() -> dict:
    """These fields are never in a CV - always ask."""
    print("\nA few things about what you're looking for:")
    target_roles = input("Target roles (comma-separated, e.g. 'Data Engineer, Software Engineer'): ").strip()
    target_location = input("Target location (e.g. 'Berlin', or 'Germany' for anywhere): ").strip()
    availability = input("Availability (e.g. 'immediate', 'from 10/2026'): ").strip()

    return {
        "target_roles": [r.strip() for r in target_roles.split(",") if r.strip()],
        "target_location": target_location or None,
        "availability": availability or None,
    }


def run(pdf_path: str = "profiles/cv.pdf") -> Profile:
    print(f"Reading CV from {pdf_path}...")
    extracted = extract_profile(pdf_path)

    print("Classifying career stage...")
    classification = classify(extracted)

    if classification["confidence"] < CONFIDENCE_THRESHOLD:
        stage_fields = ask_clarifying_questions(extracted, classification)
    else:
        print(f"\nClassified as: {classification['career_stage']} "
              f"(confidence {classification['confidence']:.2f})")
        confirm = input("Does that look right? [Y/n] ").strip().lower()
        if confirm == "n":
            stage_fields = ask_clarifying_questions(extracted, classification)
        else:
            stage_fields = {
                "career_stage": classification["career_stage"],
                "career_stage_confidence": classification["confidence"],
            }

    search_fields = ask_search_preferences()

    profile = Profile(**extracted, **stage_fields, **search_fields)

    PROFILE_OUT.parent.mkdir(exist_ok=True)
    PROFILE_OUT.write_text(profile.model_dump_json(indent=2))
    print(f"\nSaved to {PROFILE_OUT}")
    return profile


if __name__ == "__main__":
    run()