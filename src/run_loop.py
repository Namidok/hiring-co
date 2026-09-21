"""
Agent 2/3 scheduling loop: runs the search -> rank pipeline every N hours,
skips postings already seen in a prior run (so you're not re-reading the
same 70 jobs every cycle), and writes only the NEW ranked postings to
results/new/{timestamp}.jsonl.

This does not auto-apply to anything. It only produces a file for you to
read. Run it in the foreground with `python src/run_loop.py` and leave the
terminal tab open, or use `nohup`/`screen`/`tmux` to keep it running after
you close the terminal - see the note printed at startup.
"""
import json
import time
from datetime import datetime
from pathlib import Path

from search_jobs import search_for_profile
from rank_jobs import rank_all

SEEN_FILE = Path("results/seen_referenznummern.json")
NEW_DIR = Path("results/new")
INTERVAL_SECONDS = 2 * 60 * 60  # 2 hours


def load_seen() -> set[str]:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(sorted(seen)))


def run_once(profile: dict, seen: set[str]) -> set[str]:
    location = profile.get("target_location")
    postings = search_for_profile(profile["target_roles"], location)
    new_postings = [p for p in postings if p["referenznummer"] not in seen]

    print(f"[{datetime.now().isoformat(timespec='seconds')}] "
          f"{len(postings)} total postings, {len(new_postings)} new")

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
    return seen


if __name__ == "__main__":
    with open("profiles/profile.json") as f:
        profile = json.load(f)

    seen = load_seen()
    print(f"starting loop: every {INTERVAL_SECONDS // 3600}h, "
          f"{len(seen)} postings already seen from prior runs")
    print("Ctrl+C to stop. To keep this running after closing the terminal, "
          "restart it with: nohup python src/run_loop.py > loop.log 2>&1 &")

    while True:
        seen = run_once(profile, seen)
        print(f"sleeping {INTERVAL_SECONDS // 60} minutes...\n")
        time.sleep(INTERVAL_SECONDS)