# Hiring&Co

![CI](https://github.com/Namidok/hiring-co/actions/workflows/ci.yml/badge.svg)

A multi-agent job-application pipeline that runs on a **local LLM** (Ollama,
`qwen3:8b`). Every two hours it finds new postings in Germany, ranks how well each
one fits your profile, drafts a tailored CV and cover letter for the good ones, and
sends them to your phone over Telegram. It then watches your inbox for replies.

Two design rules shape everything:

1. **It never invents facts about you.** Generated CVs and cover letters can only
   reorder and select your real CV content. They never rewrite it or add to it.
2. **It never applies for you.** A human decides and submits every application.

## Agents

| # | Agent | What it does | Key files |
|---|---|---|---|
| 1 | **Profile** | Extracts a structured profile from your CV with the LLM and classifies your career stage with a confidence score. Below 0.7 it asks you multiple-choice clarifying questions instead of guessing, and you confirm the result before it's saved. | `agent1_profile.py`, `extract_profile.py`, `classify_stage.py`, `profile_schema.py` |
| 2 | **Search** | Queries the Bundesagentur für Arbeit job-search API (nationwide by default) and skips postings it has already seen. It can also parse LinkedIn job-alert emails into the same posting format. | `search_jobs.py`, `run_loop.py`, `parse_linkedin_alert.py` |
| 3 | **Rank** | Scores each posting's fit (0–1) and gives a verdict (`strong_fit` … `not_a_fit`) with reasoning that must cite specific evidence. | `rank_jobs.py` |
| 4 | **Draft** | For each fitting posting, reorders your real CV bullets and projects by relevance and renders a matched CV + cover-letter PDF pair. | `generate_cvs_batch.py`, `select_bullets.py`, `cv_bullets.py`, `cv_structure.py`, `generate_cv.py`, `generate_cover_letter.py` |
| 5 | **Track** | Logs every posting in a CSV tracker and scans your inbox read-only (IMAP) for interview, rejection or assessment replies. | `tracker.py`, `check_inbox.py`, `mark_applied.py` |

`hiring_co.py` ties all five agents together into one loop. `fetch_job_detail.py`
summarises each real job page (skills, language level, location) for the Telegram
message.

## Keeping a local LLM honest

- **Schema-enforced output.** Every LLM call uses Ollama's JSON-schema `format` at
  temperature 0, so the code always gets a parseable structure back, never free text.
- **Grounding by construction.** CV content comes from a deterministically parsed
  bullet bank (`cv_bullets.py`), not from the model. The model chooses an order and
  never writes the text.
- **Removing the context that invites fabrication.** These bugs were found during
  development, and each fix is in the commit history:
  - The ranker invented location-based reasoning. Location is now left out of the
    prompt entirely for nationwide searches.
  - The ranker judged language requirements the postings never stated. That is now
    explicitly forbidden in the prompt.
  - The profile classifier read `expected_2027` as "final year of studies".
  - Years of experience were summed from only one role.
- **Human in the loop.** Low-confidence classifications are confirmed with you, and
  `mark_applied.py` is a manual step by design.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:8b
```

Put your CV at `profiles/cv.pdf` and save its text for the bullet bank:

```bash
python -c "import sys; sys.path.insert(0,'src'); from parse_cv import extract_text; \
open('profiles/cv_raw_text.txt','w').write(extract_text('profiles/cv.pdf'))"
```

Telegram and inbox monitoring are optional. To use them, add the following to
`profiles/.env`, which is gitignored:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
IMAP_HOST=...
IMAP_USER=...
IMAP_APP_PASSWORD=...
```

## Run

```bash
python src/agent1_profile.py                          # once: build and confirm your profile
nohup python -u src/hiring_co.py > hiring_co.log 2>&1 &   # the 2-hourly loop
python src/mark_applied.py <referenznummer>           # after you've actually applied
```

Output goes to `results/`: ranked postings, generated CVs and cover letters, and
`applications.csv`. All of it is gitignored. Your CV text and profile never leave
your machine except as files Telegram delivers to you.

## Tests

```bash
pytest -q
```

There are 40 tests. Tests that need a running Ollama model are marked
`requires_ollama` and are skipped automatically when no model is reachable, which
is the case in CI.

## Limitations

- The CV parser is calibrated to one CV layout (em-dash or `|` headers). Check the
  output of `python src/cv_bullets.py` whenever your CV changes.
- Ranking quality is bounded by an 8B local model, so treat verdicts as a filter,
  not a decision.
- The LinkedIn alert parser is a draft that hasn't yet been calibrated against
  many real emails.