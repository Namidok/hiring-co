import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cv_bullets import load_bullet_bank

# Built from raw codepoints, not literal glyphs or backslash escapes, so
# no editor/clipboard auto-formatting along the way can silently swap
# these for markdown-list hyphens or similar.
BULLET = chr(0x2022)
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)
MIDDOT = chr(0x00b7)

LINES = [
    "SUMMARY",
    "Some summary text that spans",
    "multiple lines before the next section.",
    "TECHNICAL SKILLS",
    BULLET + " Programming Languages: Python, SQL",
    BULLET + " Backend: FastAPI, Flask",
    "PROFESSIONAL EXPERIENCE",
    "Software Engineer " + EM_DASH + " Acme Corp    Berlin, Germany | Jan 2022 " + EN_DASH + " Dec 2023",
    BULLET + " Built a feature that improved page-",
    "load time by 50%.",
    BULLET + " Shipped 3 releases with zero regressions.",
    "Junior Developer " + EM_DASH + " StartupX    Munich, Germany | Jun 2020 " + EN_DASH + " Dec 2021",
    BULLET + " Wrote tests covering 20 core",
    "functionalities across the platform.",
    "PROJECTS",
    "cool-project " + EM_DASH + " A Thing That Does Stuff " + EM_DASH + " Python " + MIDDOT + " pytest " + MIDDOT,
    "github.com/user/cool-project",
    BULLET + " Built a tool that does something",
    "useful and important for people.",
    "EDUCATION",
    "MSc Computer Science    2023 " + EN_DASH + " 2025",
    "Some University",
]

SAMPLE_CV_TEXT = "\n".join(LINES) + "\n"


def _write_sample(tmp_path):
    p = tmp_path / "cv_raw_text.txt"
    p.write_text(SAMPLE_CV_TEXT)
    return p


def test_bullet_count(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    assert len(bank) == 6


def test_technical_skills_bullets_have_correct_section(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    skills = [b for b in bank if b["section"] == "TECHNICAL SKILLS"]
    assert len(skills) == 2
    assert skills[0]["text"] == "Programming Languages: Python, SQL"


def test_wrapped_bullet_text_is_reassembled(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    target = next(b for b in bank if "page-load" in b["text"])
    assert target["text"] == "Built a feature that improved page-load time by 50%."


def test_wrapped_bullet_without_hyphen_joins_with_space(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    target = next(b for b in bank if "20 core" in b["text"])
    assert target["text"] == "Wrote tests covering 20 core functionalities across the platform."


def test_bullets_grouped_under_correct_job_context(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    acme_bullets = [b for b in bank if "Acme Corp" in b["context"]]
    startupx_bullets = [b for b in bank if "StartupX" in b["context"]]
    assert len(acme_bullets) == 2
    assert len(startupx_bullets) == 1


def test_wrapped_project_header_is_reassembled_before_first_bullet(tmp_path):
    path = _write_sample(tmp_path)
    bank = load_bullet_bank(str(path))
    project_bullet = next(b for b in bank if "useful and important" in b["text"])
    assert "cool-project" in project_bullet["context"]
    assert "github.com/user/cool-project" in project_bullet["context"]