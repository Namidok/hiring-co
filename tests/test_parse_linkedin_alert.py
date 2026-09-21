import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parse_linkedin_alert import parse_alert_email, to_posting_shape

SAMPLE_EMAIL_HTML = """
<html><body>
<table>
  <tr><td>
    <a href="https://www.linkedin.com/jobs/view/4123456789/?trk=email">
      Werkstudent Data Engineering (m/w/d)
    </a>
    <div>DeepL SE &middot; Cologne, Germany</div>
  </td></tr>
  <tr><td>
    <a href="https://www.linkedin.com/jobs/view/4123456790/?trk=email">
      AI Engineering Intern
    </a>
    <div>Celonis &middot; Munich, Germany</div>
  </td></tr>
</table>
</body></html>
"""


def test_parse_alert_email_extracts_all_jobs():
    jobs = parse_alert_email(SAMPLE_EMAIL_HTML)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Werkstudent Data Engineering (m/w/d)"
    assert jobs[0]["job_id"] == "4123456789"
    assert jobs[1]["title"] == "AI Engineering Intern"


def test_parse_alert_email_dedupes_repeated_job_ids():
    doubled = SAMPLE_EMAIL_HTML + SAMPLE_EMAIL_HTML
    jobs = parse_alert_email(doubled)
    assert len(jobs) == 2


def test_parse_alert_email_returns_empty_list_for_no_matches():
    assert parse_alert_email("<html><body>no jobs here</body></html>") == []


def test_to_posting_shape_produces_rank_jobs_compatible_dict():
    jobs = parse_alert_email(SAMPLE_EMAIL_HTML)
    posting = to_posting_shape(jobs[0])
    assert posting["stellenangebotsTitel"] == "Werkstudent Data Engineering (m/w/d)"
    assert posting["stellenangebotsart"] == "LINKEDIN"
    assert posting["referenznummer"] == "linkedin-4123456789"
    assert "adresse" in posting["stellenlokationen"][0]