"""
Agent 5, part 2: inbox monitoring. Read-only IMAP scan of your mailbox
for replies to applications already recorded in the tracker
(tracker.py), and updates each matching application's status
(interview / rejection / assessment) automatically.

Never marks emails as read, moves them, or replies - it only reads
headers/bodies via IMAP SEARCH (mailbox opened readonly) and writes to
results/applications.csv.

Credentials come from environment variables, never hardcoded or
committed:
    IMAP_HOST            e.g. imap.gmail.com
    IMAP_USER            the mailbox to check
    IMAP_APP_PASSWORD    a Gmail "App Password" (not your normal
                          password - generate one at
                          myaccount.google.com/apppasswords with 2FA on)

Simplest way to set these without polluting your shell or committing
secrets: put them in profiles/.env (already covered by the profiles/
gitignore rules, but double-check with `git check-ignore -v profiles/.env`)
    IMAP_HOST=imap.gmail.com
    IMAP_USER=you@gmail.com
    IMAP_APP_PASSWORD=xxxxxxxxxxxxxxxx
This script loads that file itself - no extra dependency needed.
"""
import email
import imaplib
import os
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path

from tracker import load_tracker, update_status

ENV_PATH = Path("profiles/.env")
LOOKBACK_DAYS = 14

REJECTION_KEYWORDS = [
    "unfortunately", "not moving forward", "other candidates",
    "will not be proceeding", "decided not to", "regret to inform",
    "not successful", "position has been filled",
]
INTERVIEW_KEYWORDS = [
    "interview", "schedule a call", "would like to speak", "meet with you",
    "next steps", "phone screen", "video call",
]
ASSESSMENT_KEYWORDS = [
    "assessment", "coding challenge", "take-home", "technical test",
    "online test", "hackerrank", "codesignal",
]


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _decode(value) -> str:
    if value is None:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(text)
    return "".join(out)


def _get_body_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    return part.get_payload(decode=True).decode(charset, errors="ignore")
                except Exception:
                    continue
        return ""
    charset = msg.get_content_charset() or "utf-8"
    try:
        return msg.get_payload(decode=True).decode(charset, errors="ignore")
    except Exception:
        return ""


def _classify(subject: str, body: str) -> str | None:
    text = f"{subject} {body}".lower()
    if any(k in text for k in REJECTION_KEYWORDS):
        return "rejected"
    if any(k in text for k in ASSESSMENT_KEYWORDS):
        return "assessment_received"
    if any(k in text for k in INTERVIEW_KEYWORDS):
        return "interview_invite"
    return None


def check_inbox() -> list[dict]:
    _load_env_file(ENV_PATH)
    host = os.environ.get("IMAP_HOST")
    user = os.environ.get("IMAP_USER")
    password = os.environ.get("IMAP_APP_PASSWORD")
    if not (host and user and password):
        raise RuntimeError(
            "missing IMAP_HOST / IMAP_USER / IMAP_APP_PASSWORD - set them in "
            "profiles/.env (see this file's module docstring)"
        )

    tracked = load_tracker()
    if not tracked:
        print("no tracked applications yet - run mark_applied.py first")
        return []

    companies = {row["company"].strip().lower(): row for row in tracked if row["company"].strip()}

    imap = imaplib.IMAP4_SSL(host)
    imap.login(user, password)
    imap.select("INBOX", readonly=True)  # readonly: never marks messages as seen

    since = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%d-%b-%Y")
    status, data = imap.search(None, f"(SINCE {since})")
    ids = data[0].split() if status == "OK" else []

    changes = []
    for msg_id in ids:
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK" or not msg_data or not msg_data[0]:
            continue
        msg = email.message_from_bytes(msg_data[0][1])

        from_header = _decode(msg.get("From", ""))
        subject = _decode(msg.get("Subject", ""))
        body = _get_body_text(msg)

        matched_row = None
        for company_lower, row in companies.items():
            if company_lower in from_header.lower() or company_lower in subject.lower():
                matched_row = row
                break
        if matched_row is None:
            continue

        new_status = _classify(subject, body)
        if new_status and matched_row["status"] != new_status:
            update_status(matched_row["referenznummer"], new_status)
            changes.append({
                "company": matched_row["company"],
                "title": matched_row["title"],
                "old_status": matched_row["status"],
                "new_status": new_status,
                "subject": subject,
            })

    imap.logout()
    return changes


if __name__ == "__main__":
    changes = check_inbox()
    if not changes:
        print("no status changes")
    else:
        print(f"{len(changes)} application(s) updated:")
        for c in changes:
            print(f"  {c['company']} - {c['title']}: {c['old_status']} -> {c['new_status']}")
            print(f'    (matched: "{c["subject"]}")')