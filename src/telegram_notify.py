"""
Lightweight Telegram notifications - one-way "push" messages announcing
something happened (new postings found, an inbox status change), plus
sending actual files (CV/cover letter PDFs) as Telegram documents. Uses
Telegram's Bot API directly via HTTP (the `requests` library).

Setup (one-time):
1. Message @BotFather on Telegram, send /newbot, follow the prompts.
   You'll get a bot token like "123456789:ABCdefGhIjKlmnOpQrstuVwxyz".
2. Message your new bot anything (e.g. "hi") so it can see your chat.
3. Visit https://api.telegram.org/bot<TOKEN>/getUpdates in a browser
   (with your real token) and find "chat":{"id": ...} in the JSON -
   that number is your chat ID.
4. Add both to profiles/.env:
       TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIjKlmnOpQrstuVwxyz
       TELEGRAM_CHAT_ID=987654321

If these aren't set, notify()/send_document() silently do nothing - the
rest of the project works fine without Telegram configured.
"""
import os
from pathlib import Path

import requests

ENV_PATH = Path("profiles/.env")


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _credentials() -> tuple[str, str] | None:
    _load_env_file(ENV_PATH)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        return None
    return token, chat_id


def notify(message: str) -> bool:
    """
    Sends a text message to your Telegram chat. Returns True on success,
    False if not configured or the request failed - callers should
    treat this as best-effort and never let a notification failure
    break the actual pipeline.
    """
    creds = _credentials()
    if creds is None:
        return False
    token, chat_id = creds

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


def send_document(file_path: str, caption: str = "") -> bool:
    """
    Sends a file (e.g. a generated CV or cover letter PDF) to your
    Telegram chat as a document attachment. Returns True on success,
    False if not configured, the file is missing, or the request failed.
    """
    creds = _credentials()
    if creds is None:
        return False
    token, chat_id = creds

    path = Path(file_path)
    if not path.is_file():
        return False

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with path.open("rb") as f:
            files = {"document": (path.name, f)}
            data = {"chat_id": chat_id, "caption": caption[:1024]}
            response = requests.post(url, data=data, files=files, timeout=60)
        return response.status_code == 200
    except (requests.RequestException, OSError):
        return False


if __name__ == "__main__":
    ok = notify("Hiring&Co: test notification - Telegram is wired up correctly.")
    print("sent" if ok else "not configured or failed - check profiles/.env")