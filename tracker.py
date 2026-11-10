"""Reads and writes tracker.csv, the one record of every job.

This is the repository layer. You may edit the CSV by hand, so every change
re-reads the file first and keeps any extra columns or edits you made.
"""

import csv
import os
import tempfile
from pathlib import Path

COLUMNS = ["job", "company", "score", "status", "link", "missing_skills", "file"]
STATUS_TO_REVIEW = "to_review"
STATUS_DRAFTED = "drafted"

Row = dict[str, str]


def _path() -> Path:
    return Path.cwd() / "tracker.csv"


def read_tracker() -> tuple[list[str], list[Row]]:
    """Return the column names and rows. Raises ValueError if the file is unusable."""
    if not _path().exists():
        return COLUMNS.copy(), []

    # utf-8-sig also accepts the invisible marker Excel adds when it saves a CSV.
    with _path().open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = list(reader.fieldnames or [])

    removed = [column for column in COLUMNS if column not in columns]
    if removed:
        raise ValueError(f"tracker.csv is missing required columns: {', '.join(removed)}")
    for number, row in enumerate(rows, start=2):
        if None in row:  # csv puts cells beyond the last column under the key None.
            raise ValueError(f"tracker.csv row {number} has more cells than there are columns")
    return columns, rows


def _write_tracker(columns: list[str], rows: list[Row]) -> None:
    # Write a temp file in the same folder, then swap it in. os.replace is atomic,
    # so a crash midway leaves the old tracker intact, never a half-written one.
    descriptor, temp_name = tempfile.mkstemp(dir=Path.cwd(), prefix=".tracker-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, _path())
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _safe_cell(value: str) -> str:
    """Stop text from a posting being run as a formula if the CSV is opened in Excel."""
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


def add_job(job: str, company: str, score: int, link: str, missing_skills: list[str], file: str) -> None:
    columns, rows = read_tracker()
    rows.append(
        {
            "job": _safe_cell(job),
            "company": _safe_cell(company),
            "score": str(score),
            "status": STATUS_TO_REVIEW,
            "link": _safe_cell(link),
            "missing_skills": _safe_cell("; ".join(missing_skills)),
            "file": file,
        }
    )
    _write_tracker(columns, rows)
