"""Stage 4: custom tools that fetch postings from public job board APIs.

Only two hard-coded public read-only APIs are ever contacted, using GET. There
is deliberately no code here that can POST or submit anything.

A @tool function is like a Spring @Bean that Claude can call: the description
tells Claude when to use it, and the schema is its method signature.
"""

import asyncio
import html
import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import certifi
from claude_agent_sdk import create_sdk_mcp_server, tool

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

# python.org builds of Python on macOS ship without root certificates. certifi
# provides them, so HTTPS verification stays fully on.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "job-agent/0.1"})
    with urllib.request.urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
        return json.load(response)


def _html_to_text(raw: str) -> str:
    """Simple on purpose. Good enough for Claude to read."""
    text = html.unescape(html.unescape(raw))  # Greenhouse escapes its HTML.
    text = re.sub(r"<(br|/p|/li|/h\d)\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _normalise_greenhouse(board: str) -> list[dict[str, str]]:
    data = _get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    return [
        {
            "id": str(job["id"]),
            "title": job["title"],
            "company": job.get("company_name") or board,
            "location": (job.get("location") or {}).get("name", ""),
            "link": job["absolute_url"],
            "body": _html_to_text(job.get("content", "")),
        }
        for job in data["jobs"]
    ]


def _normalise_lever(company: str) -> list[dict[str, str]]:
    data = _get_json(f"https://api.lever.co/v0/postings/{company}?mode=json")
    jobs = []
    for job in data:
        sections = [job.get("descriptionPlain", "")]
        for section in job.get("lists", []):
            sections.append(f"{section.get('text', '')}\n{_html_to_text(section.get('content', ''))}")
        sections.append(job.get("additionalPlain", ""))
        jobs.append(
            {
                "id": job["id"],
                "title": job["text"],
                "company": company,
                "location": (job.get("categories") or {}).get("location", ""),
                "link": job["hostedUrl"],
                "body": "\n\n".join(s for s in sections if s),
            }
        )
    return jobs


FETCHERS = {"greenhouse": _normalise_greenhouse, "lever": _normalise_lever}


def fetch_and_save(source: str, board: str, keywords: list[str], limit: int) -> list[Path]:
    """Fetch one board, keep postings whose TITLE matches a keyword, save as .txt."""
    if not SLUG_PATTERN.match(board):
        # The board name goes into a URL and a filename, so validate it first.
        raise ValueError(f"Invalid board name: {board!r}")

    wanted = [k.lower() for k in keywords if k.strip()]
    matches = [
        job
        for job in FETCHERS[source](board)
        if not wanted or any(k in job["title"].lower() for k in wanted)
    ]

    folder = Path.cwd() / "jobs"
    folder.mkdir(exist_ok=True)
    saved = []
    for job in matches[:limit]:
        path = folder / f"{source}-{board}-{job['id']}.txt"
        path.write_text(
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Link: {job['link']}\n\n"
            f"{job['body']}\n",
            encoding="utf-8",
        )
        saved.append(path)
    return saved


async def _run_fetch(source: str, args: dict[str, Any]) -> dict[str, Any]:
    keywords = [k.strip() for k in args["keywords"].split(",")]
    try:
        # urllib blocks, so run it on a worker thread and keep the event loop free.
        saved = await asyncio.to_thread(
            fetch_and_save, source, args["board"], keywords, args["limit"]
        )
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as error:
        # Returning is_error lets Claude see the failure and react, rather than
        # the exception crashing the whole run.
        return {"content": [{"type": "text", "text": f"Fetch failed: {error}"}], "is_error": True}

    names = "\n".join(path.name for path in saved) or "(no matching jobs)"
    return {"content": [{"type": "text", "text": f"Saved {len(saved)} jobs:\n{names}"}]}


SCHEMA = {"board": str, "keywords": str, "limit": int}
HELP = (
    " Saves matching postings into the jobs folder. keywords is a comma-separated"
    " list matched against job titles. limit is the maximum number to save."
)


@tool("fetch_greenhouse_jobs", "Fetch postings from a public Greenhouse board." + HELP, SCHEMA)
async def fetch_greenhouse_jobs(args: dict[str, Any]) -> dict[str, Any]:
    return await _run_fetch("greenhouse", args)


@tool("fetch_lever_jobs", "Fetch postings from a public Lever board." + HELP, SCHEMA)
async def fetch_lever_jobs(args: dict[str, Any]) -> dict[str, Any]:
    return await _run_fetch("lever", args)


jobs_server = create_sdk_mcp_server("jobs", tools=[fetch_greenhouse_jobs, fetch_lever_jobs])
