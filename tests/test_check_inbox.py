import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from check_inbox import _classify


def test_classifies_rejection():
    assert _classify(
        "Update on your application",
        "Unfortunately, we have decided to move forward with other candidates.",
    ) == "rejected"


def test_classifies_interview_invite():
    assert _classify(
        "Next steps",
        "We would like to schedule a call with you next week.",
    ) == "interview_invite"


def test_classifies_assessment():
    assert _classify(
        "Coding challenge",
        "Please complete the following technical test within 5 days.",
    ) == "assessment_received"


def test_returns_none_for_unrelated_email():
    assert _classify("Newsletter", "Check out our latest blog post.") is None