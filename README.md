# Job Agent

A job-application agent that runs inside Claude Code. One command, `/todays-work`, does
the following:

1. Searches job portals for roles that fit your resume and your requirements. It covers
   LinkedIn, Naukri, Indeed, Foundit, Wellfound, remote job boards, and company career
   sites through Greenhouse, Lever, Ashby and Workable.
2. Filters out jobs that are too senior, in the wrong place, underpaid or excluded. It
   scores the rest, then shows you up to 20 of the best.
3. For the jobs you pick, it writes a resume tailored to each job description and
   checks it for invented content. Then it fills in the application and submits it.
   Quick applies go first, and anything that needs you (CAPTCHAs, passwords,
   verification codes) is saved for the end.
4. Records every job in `tracker.csv` and keeps a Google Sheet in sync.

Claude does the reasoning and drives your own Chrome through the Claude in Chrome
extension, so you can watch it work.

## How it works

The agent is mostly plain-English instructions, plus a few small Python helpers for
the steps that must be exact.

| Path | Purpose |
|---|---|
| `.claude/skills/todays-work/SKILL.md` | Registers the `/todays-work` command and points to the instructions |
| `instructions/todays-work.md` | The agent's full procedure and rules |
| `instructions/portals.md` | How to search each job portal |
| `config.toml` | Your requirements: roles, experience, locations, salary, job types, daily target, portals |
| `job_tools.py`, `settings.py` | Reads public Greenhouse and Lever job boards (no AI needed) |
| `resume_tailoring/resume_pdf.py` | Turns a Markdown resume into a one-page PDF |
| `resume_tailoring/check_resume.py` | Rejects tailored resumes that add numbers, employers, titles or skills not in the original |
| `google_sheet/Code.gs`, `google_sheet/sync.py` | Keeps a "Job Tracker" Google Sheet in your own account up to date |

## Set up

You need macOS or Linux, Python 3.11 or later, Claude Code with a Claude plan, Chrome, and
the Claude in Chrome extension.

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Then add your own files. Git ignores all of them, so they never leave your computer:

- `resume_tailoring/resume.md`: your resume in Markdown.
- `applicant_profile.md`: answers for application forms, such as phone, notice period,
  salary and work authorization.
- Edit `config.toml` to match what you're looking for.

To use the Google Sheet tracker (optional):

1. Run `venv/bin/python google_sheet/sync.py setup`.
2. Paste the generated `google_sheet/Code_to_paste.gs` into a sheet's
   Extensions > Apps Script.
3. Deploy it as a web app.
4. Put the URL in `google_sheet/sheet_link.toml`.

## Run

In Claude Code, enable Chrome with `/chrome`, open this folder, and type:

```
/todays-work
```

## Safety rules built in

- It never invents experience. Tailored resumes are checked against the original.
- It never solves CAPTCHAs and never types or stores passwords.
- It treats job postings as untrusted text and ignores instructions inside them.
- It stops the whole run if a site shows an account warning.
- Automated use may break some job sites' terms of service, so use it at your own risk.
