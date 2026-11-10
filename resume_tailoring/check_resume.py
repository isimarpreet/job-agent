"""Check that a tailored resume adds nothing that isn't in the original.

Run: python resume_tailoring/check_resume.py resume_tailoring/tailored/some-job.md

Compares against resume_tailoring/resume.md and flags:
- numbers and dates that don't appear in the original
- bold text, such as employers, job titles and project names, not in the original
- skills listed in the skills section that the original never mentions

It can't judge meaning, so a sentence that bends the truth with existing words can
still pass. It catches the most common inventions: new numbers, employers and skills.
Exits with 1 if anything is flagged, like a failing unit test.
"""

import re
import sys
from pathlib import Path

ORIGINAL = Path(__file__).parent / "resume.md"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _mentions(known: str, term: str) -> bool:
    """True if the term appears as whole words, so 'Go' doesn't match 'Google'."""
    pattern = r"(?<!\w)" + re.escape(_normalise(term)) + r"(?!\w)"
    return re.search(pattern, known) is not None


def _split_skills(text: str) -> list[str]:
    """Split on commas that aren't inside brackets, so 'AWS (EC2, S3)' stays whole."""
    items, depth, current = [], 0, ""
    for character in text:
        depth += character == "("
        depth -= character == ")"
        if character == "," and depth == 0:
            items.append(current)
            current = ""
        else:
            current += character
    items.append(current)
    return [item.strip(" .") for item in items if item.strip(" .")]


def find_problems(tailored: str, original: str) -> list[str]:
    known = _normalise(original)
    problems = []

    original_numbers = set(re.findall(r"\d+(?:[./]\d+)*", original))
    for number in sorted(set(re.findall(r"\d+(?:[./]\d+)*", tailored))):
        if number not in original_numbers:
            problems.append(f"number or date not in your resume: {number}")

    for bold in sorted(set(re.findall(r"\*\*(.+?)\*\*", tailored))):
        if " | " in bold:
            # The headline, like "Backend Engineer | Python | FastAPI". It may be
            # rewritten for each job, but every part must come from the resume.
            for part in bold.split(" | "):
                if not _mentions(known, part):
                    problems.append(f"headline item not in your resume: {part}")
        elif _normalise(bold).rstrip(":") not in known:
            problems.append(f"bold text not in your resume: {bold}")

    in_skills = False
    for line in tailored.splitlines():
        if line.startswith("## "):
            in_skills = "skill" in line.lower()
            continue
        if in_skills and ":" in line:
            for skill in _split_skills(line.split(":", 1)[1].replace("**", "")):
                if not _mentions(known, skill):
                    problems.append(f"skill not in your resume: {skill}")
    return problems


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python resume_tailoring/check_resume.py tailored.md")
    found = find_problems(
        Path(sys.argv[1]).read_text(encoding="utf-8"), ORIGINAL.read_text(encoding="utf-8")
    )
    if found:
        print("NOT OK. Fix these, using only facts from resume.md:")
        print("\n".join(f"- {problem}" for problem in found))
        sys.exit(1)
    print("OK: no new numbers, employers, titles or skills found.")
