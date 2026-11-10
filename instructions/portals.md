# Job portals

How to search each portal key in `config.toml` `[portals] enabled`. In the URLs,
`{role}` is one role from `[search] roles`, URL-encoded, and `{role-slug}` is the
same role in lower case with hyphens.

These URL patterns may change. If one doesn't load or shows no results, open the
portal's home page and use its own search box with the same role, location and
"posted recently" filter.

## India

| Key | Portal | Search | Notes |
|---|---|---|---|
| `linkedin` | LinkedIn Jobs | `https://www.linkedin.com/jobs/search/?keywords={role}&location=India&f_TPR=r86400&f_JT=F%2CC` | Also run once with `location=Worldwide` and remote filter. Mark Easy Apply jobs. |
| `naukri` | Naukri | `https://www.naukri.com/{role-slug}-jobs-in-india?jobAge=1` | Applying uses the resume on the Naukri profile, not the tailored PDF. |
| `indeed` | Indeed India | `https://in.indeed.com/jobs?q={role}&l=India&fromage=1` | |
| `foundit` | Foundit (formerly Monster India) | `https://www.foundit.in/srp/results?query={role}&locations=India` | |
| `instahyre` | Instahyre | Home page search | Needs a login to see or apply. |
| `cutshort` | Cutshort | Home page search | Needs a login to apply. |
| `hirist` | Hirist (tech jobs) | Home page search | |
| `glassdoor` | Glassdoor India | `https://www.glassdoor.co.in/Job/index.htm`, then search | Often shows a sign-in pop-up. |
| `shine` | Shine | `https://www.shine.com/job-search/{role-slug}-jobs` | |

## Startups, remote and worldwide

| Key | Portal | Search | Notes |
|---|---|---|---|
| `wellfound` | Wellfound (formerly AngelList Talent) | Home page search, location India or Remote | Needs a login. Shows salary and equity. |
| `remotive` | Remotive | `https://remotive.com/remote-jobs/search?query={role}` | Remote only. Check the allowed countries. |
| `weworkremotely` | We Work Remotely | `https://weworkremotely.com/remote-jobs/search?term={role}` | Remote only. Many are US-only: check. |
| `himalayas` | Himalayas | Home page search | Remote only. Lists allowed countries. |
| `remoteok` | Remote OK | `https://remoteok.com/remote-{role-slug}-jobs` | Remote only. Check the allowed countries. |

## Company career sites

| Key | Source | Search |
|---|---|---|
| `company_sites` | Google search across company career systems | `https://www.google.com/search?tbs=qdr:w&q="{role}" (India OR remote) (site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:apply.workable.com OR site:jobs.smartrecruiters.com OR site:myworkdayjobs.com)` |
| `company_boards` | Public Greenhouse and Lever boards listed in `config.toml` | Run `venv/bin/python job_tools.py`. It saves postings to `jobs/` and prints one line per job. Read the full file only for promising lines. |

`company_sites` reaches thousands of companies' own career pages, which are often
not on any portal. `tbs=qdr:w` limits results to the past week.
