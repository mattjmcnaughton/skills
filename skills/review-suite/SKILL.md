---
name: review-suite
description: Fan-out wrapper that runs the installed code-quality review skills (`/thermo-nuclear-code-quality-review`, `/ponytail-review`, `/ship-gate`) against a target diff in parallel subagents and dedupes findings across them. Prints a terminal report by default; can optionally push the unified result into a live `/hunk-review` session for inline review. Use when the user says "review-suite", "run the reviews", "full review", or wants a multi-lens pass on a diff before committing or pushing. Strictly code-quality oriented; acceptance-criteria verification is out of scope.
---

`/review-suite` runs several focused review skills in parallel and dedupes their findings into one terminal report. Hunk is an optional second medium: if the user is already reviewing in Hunk, the suite can push the same findings into the live session as inline comments.

It is **strictly code-quality oriented**. It does not read `plan.md` and does not verify acceptance criteria — that responsibility belongs elsewhere.

## Target

Pick a diff target. Default is the working tree (staged + unstaged uncommitted edits).

| Invocation | Diff scope |
|---|---|
| `/review-suite` (default) | `git diff` + `git diff --cached` |
| `/review-suite --against <ref>` | `git diff <ref>...HEAD` + uncommitted |
| `/review-suite --against main` | branch-vs-main view (common before push) |

If the chosen target has no diff, report that and exit.

## Sub-skill check

`/review-suite` orchestrates these skills:

- `/thermo-nuclear-code-quality-review` — strict maintainability / abstraction review
- `/ponytail-review` — over-engineering review (what to delete)
- `/ship-gate` — mechanical pre-ship checks (secrets, garbage, debug residue, etc.)

For each, verify the skill is installed by checking `~/.claude/skills/<name>/SKILL.md` (or a project-local `.claude/skills/<name>/SKILL.md`). If **any** are missing, **exit immediately** and tell the user which ones to install. Do not proceed with a partial run — the value of the suite is the multi-lens overlap, and silently degrading defeats the point.

Example exit message:

```
/review-suite requires three skills, but the following are not installed:

  - thermo-nuclear-code-quality-review  (expected at ~/.claude/skills/thermo-nuclear-code-quality-review/)

Install them and retry.
```

## Fan-out

**When subagent spawning is available, prefer it.** Spawn one subagent per sub-skill, in parallel, in a single message (e.g. multiple `Task`/`Agent` tool calls in one turn). Each subagent runs its skill against the resolved target diff and returns a JSON array of findings. This is the preferred path: it isolates each lens in its own context and runs them concurrently.

If subagent fan-out is **not** available in the current harness (no `Task`/`Agent` tool, or the environment can't spawn parallel subagents), fall back to running each sub-skill sequentially in the main conversation. The fallback produces the same findings JSON per skill and feeds the same dedupe step — only the concurrency and context isolation are lost. Note in the report which path was used.

Prompt shape per subagent (also the per-skill instruction in the sequential fallback):

> Run `/<sub-skill>` on the diff produced by `<diff command>`. Return ONLY a JSON array of findings, no prose around it. Each finding: `{"file": str, "line": int, "line_end": int|null, "severity": "critical|warn|nit", "summary": str, "rationale": str|null, "source": "<sub-skill>"}`. Use `line` = `line_end` for single-line findings. If the skill has no findings, return `[]`.

Notes per skill:

- **ponytail-review**: maps its `delete:` / `stdlib:` / `native:` / `yagni:` / `shrink:` tags into the `severity` field as `warn` (or `critical` if the finding eliminates a whole abstraction). Include the tag in `rationale`.
- **thermo-nuclear**: prefer `critical` for structural/spaghetti findings, `warn` for boundary/abstraction issues, `nit` only for legibility polish.
- **ship-gate**: its `FAIL` → `critical`, `WARN` → `warn`, `CLEAN` checks contribute no findings.

`/ship-gate` is hard-coded to `main...HEAD`. If the user passed `--against <other-ref>`, note in the report that ship-gate ran against `main` regardless.

## Dedupe

After all three subagents return, dedupe in the orchestrator (not in another subagent).

Two findings are duplicates when **both**:

1. Same `file`, and line ranges overlap or are within 2 lines of each other.
2. Summaries describe the same root cause (e.g., both flag the same unused wrapper, the same magic-number, the same debug print).

When merging duplicates:

- Keep the most specific `summary` (longer / more concrete usually wins).
- Take the highest severity across the duplicates.
- Concatenate `source` into a list: `"source": ["ponytail-review", "thermo-nuclear-code-quality-review"]`.
- Preserve the union of rationales.

Do not rank findings beyond severity. Order them by `file`, then `line`.

## Output: terminal report (always)

Always print the deduped findings to the terminal. This is the primary output and works whether or not Hunk is installed.

```
review-suite report
Target: <diff scope>
Sub-skills: thermo-nuclear, ponytail, ship-gate
Findings: <N> (after dedupe from <M> raw)

[critical] src/api.ts:88 — debug console.log in production path  (via: ship-gate)
[critical] src/repo.py:14-38 — AbstractRepository wrapper with one implementation. Inline it.  (via: ponytail-review, thermo-nuclear)
[warn]     src/loader.py:14 — new outbound HTTP read to api.partner.example  (via: ship-gate)
...
```

If every sub-skill returned `[]`, say so on one line (`No findings.`) and stop.

## Output: push to Hunk (optional)

After printing the terminal report, check whether a live Hunk session exists for the current repo:

```bash
hunk session list --json
```

- If no live session, do nothing. Do not prompt the user to launch Hunk; the terminal report stands on its own.
- If a live session exists, offer once: "A live Hunk session is open. Push these <N> findings as inline comments? (y/n)". Don't push without confirmation — the user may already have their own notes in the session.

On `y`, build a JSON batch — one comment per finding — and apply it:

- `filePath` = `file`
- `newLine` = `line`
- `summary` = `[<severity>] <summary>  (via: <source(s)>)`
- `rationale` = the rationale (or omit)
- `author` = `"review-suite"`

```bash
printf '%s' '<json>' | hunk session comment apply --repo . --stdin
```

Report how many comments were posted and where to start.

This step is convenience, not contract: a missing or broken Hunk install must not fail the suite.

## Guidelines

- Fail closed when a sub-skill is missing — never silently run a partial suite.
- Prefer fanning sub-skills out as parallel subagents when the harness supports it; only chain them sequentially as a fallback when subagent spawning is unavailable.
- Trust each sub-skill's own judgment about what counts as a finding — do not re-filter or re-categorize beyond the dedupe step.
- The suite is code-quality only. If the user asks for acceptance-criteria checks, point them at a future `/verify` skill (not yet built) rather than expanding scope here.
- Plain text only in terminal output. No emojis. If pushing to Hunk, keep comment summaries short — put detail in `rationale`.
- Do not auto-fix. The sub-skills surface findings; the user (or a follow-up pass) acts on them.
- Do not write any artifact under `.agentic/<slug>/`. The terminal report is the primary output; Hunk is an optional secondary medium.
