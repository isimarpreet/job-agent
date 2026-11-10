"""Stage 7: the whole pipeline in one command.

Run: python run.py

1. Fetch postings from the boards in config.toml. Plain Python, no Claude.
2. Score new jobs (score_jobs.py).
3. Draft a summary and cover letter for good matches (draft.py).

It stops there. You read the drafts and submit applications yourself.
"""

import asyncio
import sys

from draft import draft_matches
from job_tools import fetch_and_save
from score_jobs import score_new_jobs
from settings import Settings, load_settings

# Saving files costs no Claude quota, so fetch everything that matches. The real
# limit is max_new_jobs_per_run, applied to the steps that do call Claude.
FETCH_LIMIT = 1000


def fetch_all(settings: Settings) -> int:
    """Fetch every configured board and return how many boards failed."""
    failures = 0
    for source, boards in (
        ("greenhouse", settings.greenhouse_boards),
        ("lever", settings.lever_boards),
    ):
        for board in boards:
            try:
                saved = fetch_and_save(source, board, settings.keywords, FETCH_LIMIT)
            except (OSError, ValueError, KeyError) as error:
                # One bad board shouldn't stop the others.
                print(f"  FAILED {source}/{board}: {error}")
                failures += 1
                continue
            print(f"  {source}/{board}: {len(saved)} matching job(s)")
    return failures


async def main() -> int:
    settings = load_settings()

    print("Step 1: fetching jobs")
    failures = fetch_all(settings)

    print("Step 2: scoring new jobs")
    failures += await score_new_jobs(settings.model, settings.max_new_jobs_per_run)

    print("Step 3: drafting for good matches")
    failures += await draft_matches(
        settings.model, settings.min_score, settings.max_new_jobs_per_run
    )

    print("Done. Review tracker.csv and drafts/. Nothing has been submitted.")
    return failures


if __name__ == "__main__":
    try:
        failed = asyncio.run(main())
    except ValueError as error:
        sys.exit(str(error))
    sys.exit(1 if failed else 0)
