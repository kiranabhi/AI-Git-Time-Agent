import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LOG_DIR      = os.getenv("LOG_DIR", "./logs")
LOG_FORMAT   = os.getenv("LOG_FORMAT", "both")   # "csv", "json", or "both"
CSV_LOG_FILE = os.path.join(LOG_DIR, "timelog.csv")
JSON_LOG_FILE = os.path.join(LOG_DIR, "timelog.json")

CSV_FIELDS = ["date", "author", "hours", "summary", "commit_count", "logged_at"]


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _write_csv(date: str, author: str, hours: float, summary: str, commit_count: int):
    _ensure_log_dir()
    file_exists = os.path.isfile(CSV_LOG_FILE)

    with open(CSV_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()   # Write header only on first run
        writer.writerow({
            "date":         date,
            "author":       author,
            "hours":        hours,
            "summary":      summary,
            "commit_count": commit_count,
            "logged_at":    datetime.utcnow().isoformat(),
        })

    print(f"✅ CSV entry appended → {CSV_LOG_FILE}")


def _write_json(date: str, author: str, hours: float, summary: str, commits: list[dict]):
    _ensure_log_dir()

    # Load existing entries if file exists
    entries = []
    if os.path.isfile(JSON_LOG_FILE):
        with open(JSON_LOG_FILE, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                entries = []

    entries.append({
        "date":         date,
        "author":       author,
        "hours":        hours,
        "summary":      summary,
        "commit_count": len(commits),
        "commits":      commits,        # Full commit detail preserved
        "logged_at":    datetime.utcnow().isoformat(),
    })

    with open(JSON_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)

    print(f"✅ JSON entry saved → {JSON_LOG_FILE}")


def log_entry(date: str, hours: float, summary: str, author: str, commits: list[dict]):
    """Write a time log entry to CSV and/or JSON based on LOG_FORMAT env var."""
    fmt = LOG_FORMAT.lower()

    if fmt in ("csv", "both"):
        _write_csv(date, author, hours, summary, commit_count=len(commits))

    if fmt in ("json", "both"):
        _write_json(date, author, hours, summary, commits)
