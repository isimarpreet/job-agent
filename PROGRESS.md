# Job Agent: Progress

To resume in a new session, say: "read PROGRESS.md and continue".

Rules for this project: uses the Claude Agent SDK with your Claude Code login (never an API key).
It never submits applications and never scrapes LinkedIn/Naukri. You review and submit yourself.

Review each stage with `git log --reverse` and `git show <hash>`. Each commit is one stage.

## Stage 0: Environment (done)

**Concept.** A venv is a per-project install location, like giving each Maven project its own
private `.m2` and JDK. Activating it only puts `venv/bin` first on `PATH` for that terminal.
`requirements.txt` is a plain `<dependencies>` block.

**What happened.**
- Python 3.13.2. SDK `claude-agent-sdk` 0.2.180, which bundles its own Claude Code CLI.
- The project moved from `~/Desktop/job-agent` to `~/Developer/job-agent`. Desktop is synced by
  iCloud with Optimize Storage on, so venv files became cloud-only placeholders and `pip` hung
  forever reading them. Keep code, venvs and `.git` out of iCloud folders.
- The project has its own `git init`, because your home folder is itself a git repo.
- Login check: the SDK's init message reported `apiKeySource: none` and a test query succeeded.

**Each new terminal:** `cd ~/Developer/job-agent && source venv/bin/activate`

**Quiz.**
1. Why can't you move a venv by simply moving its folder?
2. If `which python` prints `/Library/Frameworks/...`, what does that tell you?

<details><summary>Answers</summary>

1. A venv has absolute paths baked into its scripts and config, so you recreate it instead.
2. The venv isn't active, so `pip install` would go to the system Python.
</details>

## Stage 1: Hello-world agent (done, `hello.py`)

**Concept.** `query()` streams messages, like a reactive `Flux<Message>`. `async for` consumes it.

**Message types seen.** `SystemMessage` (session start, lists tools and model), `RateLimitEvent`
(your plan's quota status), `AssistantMessage` (Claude's output), `ResultMessage` (always last,
with success or error). `total_cost_usd` is only an estimate. Pro usage comes from your plan quota.

**Quiz.**
1. Which message tells you the run is over, and how do you tell whether it failed?
2. Why is `hello.py` not an agent yet?

<details><summary>Answers</summary>

1. `ResultMessage`. Check `is_error` and `subtype`.
2. It has no tools (`tools=[]`), so Claude can only answer, not act.
</details>

## Stage 2: The agent loop (done, `agent_loop.py`)

**Concept.** An agent is a model plus tools plus a loop. Claude requests a tool, the SDK runs it,
the result goes back, and Claude decides the next step. You don't write that loop.

**Three separate controls.**
- `tools`: which tools exist at all.
- `allowed_tools`: which calls are pre-approved. It does not restrict anything on its own.
- `permission_mode="dontAsk"`: anything not approved is refused.

Tested: with `Edit(/summary.txt)` approved, a request to write `other.txt` was refused and the
file was not created. `Edit(...)` rules also cover the Write tool. Never use `bypassPermissions`
here, since it ignores `allowed_tools`.

**Quiz.**
1. Why do tool results arrive as a `UserMessage`?
2. What would happen with `allowed_tools=["Read"]` but no `permission_mode`, and the agent tried Write?

<details><summary>Answers</summary>

1. The conversation has two sides. Anything Claude didn't produce itself is on the user side.
2. Write isn't approved, so it goes to `default` mode's approval step. With no callback to approve it, it's denied.
</details>
