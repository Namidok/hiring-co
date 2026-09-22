"""
Single entry point for the whole Hiring&Co pipeline - the one command
you actually run day to day.

Every cycle (INTERVAL_SECONDS apart):
    1. Search for postings, skip ones already seen, rank the new ones
       (same logic as run_loop.py's run_once - inlined here so this
       script owns the new_count/output-path info step 2 needs, without
       changing run_loop.py's tested return contract; run_loop.py keeps
       working standalone exactly as before if you ever want it).
    2. Generate a CV + cover letter per newly-ranked posting (skipping
       not_a_fit ones).
    3. For each fitting new posting: fetch the real job page, summarize
       it with the local LLM, and send you a Telegram message with the
       job title/summary/location/skillset/language level/link, followed
       by the CV and cover letter as file attachments - so you can review
       and apply straight from your phone.
    4. Check your inbox (read-only) for status updates on applications
       you've already logged with mark_applied.py, and notify on those.

mark_applied.py stays a separate, manual command on purpose: applying is
your decision, and nothing here submits anything for you.

Usage:
    nohup python -u src/hiring_co.py > hiring_co.log 2>&1 &
"""
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

from search_jobs import search_for_profile
from rank_jobs import rank_all
from run_loop import load_seen, save_seen, NEW_DIR
from generate_cvs_batch import generate_batch
from fetch_job_detail import summarize_posting
from check_inbox import check_inbox
from telegram_notify import notify, send_document

INTERVAL_SECONDS = 2 * 60 * 60  # 2 hours


def _search_and_rank(profile: dict, seen: set[str]) -> tuple[set[str], int, Path | None]:
    location = profile.get("target_location")
    postings = search_for_profile(profile["target_roles"], location)
    new_postings = [p for p in postings if p["referenznummer"] not in seen]

    print(f"[{datetime.now().isoformat(timespec='seconds')}] "
          f"{len(postings)} total postings, {len(new_postings)} new")

    out_path = None
    if new_postings:
        ranked = rank_all(profile, new_postings)
        NEW_DIR.mkdir(parents=True, exist_ok=True)
        out_path = NEW_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H%M')}.jsonl"
        with open(out_path, "w") as f:
            for r in ranked:
                f.write(json.dumps(r) + "\n")
        strong = [r for r in ranked if r["verdict"] == "strong_fit"]
        print(f"  wrote {out_path} ({len(strong)} strong_fit)")
    else:
        print("  nothing new this cycle")

    seen.update(p["referenznummer"] for p in postings)
    save_seen(seen)
    return seen, len(new_postings), out_path


def _notify_posting(result: dict) -> None:
    posting = result["posting"]
    referenznummer = posting.get("referenznummer", "")
    title = posting.get("title", "?")
    company = posting.get("company", "?")

    detail = summarize_posting(referenznummer)

    message = (
        f"Job: {title}\n"
        f"Company: {company}\n\n"
        f"{detail['summary']}\n\n"
        f"Location: {detail['location']}\n"
        f"Skillset: {detail['skillset']}\n"
        f"Language: {detail['language_level']}\n\n"
        f"{detail['url']}"
    )
    notify(message)
    send_document(str(result["cv_path"]), caption=f"CV - {title}")
    send_document(str(result["cover_path"]), caption=f"Cover Letter - {title}")


def run_cycle(profile: dict, seen: set[str]) -> set[str]:
    summary = []

    seen, new_count, out_path = _search_and_rank(profile, seen)

    if new_count:
        summary.append(f"{new_count} new posting(s) found and ranked")
        results = generate_batch(str(out_path))
        summary.append(f"{len(results)} CV(s) + cover letter(s) generated")

        for result in results:
            try:
                _notify_posting(result)
            except Exception as e:
                print(f"  failed to notify for {result['posting'].get('title')}: {e}")
    else:
        summary.append("no new postings this cycle")

    try:
        changes = check_inbox()
    except RuntimeError as e:
        changes = []
        summary.append(f"inbox check skipped ({e})")

    if changes:
        summary.append(f"{len(changes)} application status update(s):")
        for c in changes:
            summary.append(f"  {c['company']} - {c['title']}: {c['old_status']} -> {c['new_status']}")

    message = "Hiring&Co cycle:\n" + "\n".join(summary)
    print(message)
    notify(message)
    return seen


if __name__ == "__main__":
    with open("profiles/profile.json") as f:
        profile = json.load(f)

    seen = load_seen()
    print(f"starting Hiring&Co: every {INTERVAL_SECONDS // 3600}h, "
          f"{len(seen)} postings already seen from prior runs")
    print("Ctrl+C to stop. To keep this running after closing the terminal: "
          "nohup python -u src/hiring_co.py > hiring_co.log 2>&1 &")

    while True:
        try:
            seen = run_cycle(profile, seen)
        except Exception:
            traceback.print_exc()
            notify("Hiring&Co: a cycle failed with an error - check hiring_co.log")
        print(f"sleeping {INTERVAL_SECONDS // 60} minutes...\n")
        time.sleep(INTERVAL_SECONDS)