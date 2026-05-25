# The Comeback Story

> An honest record of what was broken, what I fixed, and how GitHub Copilot
> helped me finally ship this project. Written for the
> [DEV Community GitHub Finish-Up-A-Thon Challenge](https://dev.to/challenges/github-2026-05-21).

## Where this project was

I started this project in **January 2026** as a side experiment. The idea: a
local-first, AI-mentored Linux training game. You'd get a realistic enterprise
scenario, type commands, and an AI judge would grade you. The mentor would
give Socratic hints — no spoilers.

I built the skeleton over a long weekend. Then I hit a wall and walked away.

**As of the day before this revival, the repo's state was:**

- README.md contained **unresolved git merge conflict markers** from a botched
  fixup four months ago. Anyone landing on the repo saw raw `<<<<<<< HEAD`
  markers as the first thing on the page. Look at the commit before this
  comeback — they were still there.
- The backend was hard-wired to **NVIDIA NIM**, a paid LLM service I'd
  lost access to. There was no fallback. Without the env vars, every
  endpoint 500'd.
- The `core/sandbox.py` file — the literal heart of the game, the thing
  that runs user commands safely — **did not exist**. The judge endpoint
  was scoring imaginary commands.
- `api/mission.py` was a single stub that returned `"Mission started"`
  and did nothing.
- There were two empty files named `git` and `main` sitting at the repo
  root, likely from a fat-fingered shell redirect months ago.
- Only one scenario YAML existed, and it had four fields. No challenge
  text, no setup script, no success criteria.
- The mentor and judge prompts were three lines each. No JSON schema,
  no rubric, no guarantees about output structure.

It was, in short, a project that *looked* like it was 30% done and was
actually closer to 10% — because the missing pieces were the load-bearing
ones.

## What I changed

Five commits to take it from "broken on landing" to "playable end-to-end."

**Commit 1 — Resolve the merge conflict and clean up debris**

- Fixed the README.md merge markers and rewrote the README to reflect the
  revived architecture.
- Removed the empty `git` and `main` artifact files.

**Commit 2 — Swap NVIDIA NIM for local Ollama (with NIM as a fallback)**

- Renamed `core/nim_client.py` → `core/llm_client.py`.
- Default provider is now Ollama (free, local). NIM kept as a fallback for
  users who have it. Selected via `LLM_PROVIDER` env var.
- Kept a `NIMClient` class alias so the existing API code didn't have to
  change in this commit. Backward-compatible refactor.
- Updated `core/model_router.py` to map levels to Ollama tags.
- Pinned `requirements.txt` versions, dropped the unused `docker` Python
  package in favour of shelling out to the `docker` CLI directly.
- Added a `extract_json()` helper that tolerates the markdown fences and
  prose wrappers that local models often emit.

**Commit 3 — Add the missing sandbox runner**

- Created `core/sandbox.py`. This is the file the game cannot exist
  without — it runs each player command inside a fresh Docker container
  with `--network=none`, `--memory=256m`, `--user 1000:1000`, and a
  per-command timeout. User input never touches the host.
- Improved `sandbox/Dockerfile` to include the tools the scenarios need
  (`grep`, `awk`, `sed`, `df`, `du`, `ps`, `find`, etc.) and a non-root
  user.

**Commit 4 — Real game loop and grounded prompts**

- Rewrote `api/mentor.py` and `api/judge.py` to use Pydantic request
  models, pinned JSON output schemas, and structured grading rubrics.
- Replaced the stub `api/mission.py` with the actual game loop:
  `POST /mission/start` picks a scenario, `POST /mission/run` executes a
  command in the sandbox, `POST /mission/finish` dispatches to the judge.
- Added three new scenario YAMLs (operator/engineer/sre levels) with real
  challenge narratives, setup scripts, and success keywords. These play
  to the part of this project no AI can fake for me: I've been an
  enterprise Linux trainer; I know which problems actually happen and
  what good investigation looks like.
- Beefed up the mentor and judge prompts. The judge now grades on a
  three-axis rubric (correctness / safety / efficiency) with weighted
  scoring and coaching feedback.

**Commit 5 — CLI client and polished README**

- Added `play.py` — the CLI that makes the game actually playable. Handles
  level pick, command loop, `/hint` and `/done` interactives, and renders
  the judge's verdict with the score breakdown.
- Polished the README with an architecture diagram and a quickstart that
  works on a clean machine.
- Added screenshots and a demo recording link.

## How GitHub Copilot helped (specifically)

Three places where Copilot did real work, not generic autocomplete:

1. **Resolving the merge conflict.** I opened the README in VS Code and asked
   Copilot Chat: *"Resolve this Git merge conflict in this README. Keep the
   richer 'Enterprise Linux Mastery Game' content but make it the start of a
   real README — add sections for what it does, quickstart, and configuration."*
   It produced a clean draft that I then edited for the specific Ollama
   instructions.

2. **Mapping the legacy NIM model names to Ollama tags.** I gave Copilot the
   original `model_router.py` and asked: *"These three NIM-specific model
   identifiers need to map to Ollama tags. Generate a fallback mapping that
   defaults to llama3.1 when an exact match isn't available, and keep the
   level→model selection logic intact."* The `_resolve_model_alias` method in
   `llm_client.py` is essentially what it produced, lightly edited.

3. **Drafting the sandbox runner.** This was the most useful one. I described
   what I wanted: *"Write a Python function that runs a shell command inside
   a one-shot Docker container using the docker CLI via subprocess. Hard
   timeout, no network, memory and CPU limits, runs as UID 1000. Return a
   dataclass with stdout, stderr, exit_code, and a `timed_out` flag."*
   Copilot drafted the structure including the `subprocess.TimeoutExpired`
   handling I would have forgotten. I added the `sandbox_image_exists()`
   health-check and the `FileNotFoundError` branch for the "Docker not
   installed" case.

What Copilot didn't do — and what I want to be honest about:

- It didn't write the scenario YAMLs. Those needed real domain knowledge
  about which enterprise Linux problems are pedagogically valuable. I wrote
  the narratives and success criteria; Copilot would have given me generic
  textbook examples.
- It didn't write the judge prompt rubric. The three-axis scoring scheme
  (correctness / safety / efficiency) and the weighting is mine — it
  reflects how I actually evaluate trainees.
- It didn't make the architectural call to keep `NIMClient` as a backward-
  compatible alias rather than ripping it out. That was a judgement call to
  keep the commit diff small and reviewable.

The honest version of "how Copilot helped" is: it removed the friction of
writing boilerplate — `subprocess` glue, Pydantic models, JSON parsing
helpers, README scaffolding — so I could spend my limited attention on the
parts of the project only I could do.

## What I'd still do if I had more time

- Persistent player state (XP, scenarios completed) — currently `user_id`
  is just for log lines.
- A web UI to complement the CLI.
- More scenarios per level, especially around `systemd`, networking, and
  container troubleshooting.
- Per-scenario per-command "blast radius" warnings before destructive
  commands execute, even though they're sandboxed.

## What I learned

Side projects die in the gap between **almost demoable** and **actually
playable**. The five commits above are 90% boring glue — JSON parsing, a
subprocess wrapper, request models, a CLI loop. None of it was hard. All of
it was the kind of thing I'd previously dropped because "the interesting
part is done."

The Finish-Up-A-Thon framing helped me see the gap for what it is: not a
missing capability, just missing patience for the unglamorous middle.
