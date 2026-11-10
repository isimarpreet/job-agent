"""Send tracker.csv to your Job Tracker Google Sheet.

Run once to set up:  python google_sheet/sync.py setup
Run to update:       python google_sheet/sync.py

The sheet lives in your own Google account. A small script in the sheet
(Code.gs) receives the rows, so no Claude connector is needed. Only a link
starting with https://script.google.com/ is ever contacted.
"""

import csv
import json
import secrets
import ssl
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import certifi

FOLDER = Path(__file__).parent
LINK_FILE = FOLDER / "sheet_link.toml"
TEMPLATE = FOLDER / "Code.gs"
TO_PASTE = FOLDER / "Code_to_paste.gs"
ALLOWED_PREFIX = "https://script.google.com/macros/s/"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def setup() -> None:
    """Create the secret key and the script to paste. Keeps an existing key."""
    if LINK_FILE.exists():
        token = tomllib.loads(LINK_FILE.read_text())["token"]
    else:
        token = secrets.token_urlsafe(24)
        LINK_FILE.write_text(
            "# Your Job Tracker sheet. Private: git ignores this file.\n"
            "# Paste the web app URL from Apps Script > Deploy between the quotes.\n"
            'url = ""\n'
            f'token = "{token}"\n'
        )
    TO_PASTE.write_text(TEMPLATE.read_text().replace("__TOKEN__", token))
    print(f"Created {TO_PASTE.relative_to(Path.cwd())}. Copy all of it into Apps Script.")
    print(f"Then paste the web app URL into {LINK_FILE.relative_to(Path.cwd())}.")


def sync() -> int:
    if not LINK_FILE.exists():
        sys.exit("Not set up yet. Run: venv/bin/python google_sheet/sync.py setup")
    settings = tomllib.loads(LINK_FILE.read_text())
    url = settings.get("url", "").strip()
    if not url.startswith(ALLOWED_PREFIX):
        sys.exit(f"Paste your Apps Script web app URL into {LINK_FILE} first.")

    tracker = Path.cwd() / "tracker.csv"
    if not tracker.exists():
        print("No tracker.csv yet. Nothing to send.")
        return 0
    with tracker.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = list(reader.fieldnames or [])

    body = json.dumps({"token": settings["token"], "columns": columns, "rows": rows}).encode()
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        # Apps Script answers with a redirect. urllib follows it and reads the reply.
        with urllib.request.urlopen(request, timeout=90, context=SSL_CONTEXT) as response:
            text = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"Sheet update FAILED: {error}")
        return 1

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        print("Sheet update FAILED: Google returned a web page instead of a reply.")
        print("In Apps Script > Deploy, check 'Who has access' is set to 'Anyone'.")
        return 1
    if not result.get("ok"):
        print(f"Sheet update FAILED: {result.get('error')}")
        return 1
    print(f"Sheet updated: {result['added']} added, {result['updated']} updated, {result['total']} total.")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["setup"]:
        setup()
    elif len(sys.argv) == 1:
        sys.exit(sync())
    else:
        sys.exit("Usage: python google_sheet/sync.py [setup]")
