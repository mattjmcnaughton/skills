---
name: review-suite
description: Fan-out wrapper that runs the installed review skills (`/thermo-nuclear-code-quality-review`, `/ponytail-review`, `/ship-gate`, `/correctness-review`, `/security-review`) against a target diff in parallel subagents and dedupes findings across them. Prints a terminal report by default; can optionally push the unified result into a live `/hunk-review` session for inline review. Use when the user says "review-suite", "run the reviews", "full review", or wants a multi-lens pass on a diff before committing or pushing. Strictly diff-oriented; acceptance evidence belongs to `/prove`.
---

`/review-suite` runs several focused review skills in parallel and dedupes their findings into one terminal report. Hunk is an optional second medium: if the user is already reviewing in Hunk, the suite can push the same findings into the live session as inline comments.

It is **strictly diff-oriented**: code quality, correctness, security, and ship hygiene. It does not read `plan.md` or check acceptance criteria — `/prove` owns that evidence.

## Target

Pick a diff target. Default is the working tree (staged + unstaged uncommitted edits).

| Invocation | Diff scope |
|---|---|
| `/review-suite` (default) | `git diff` + `git diff --cached` |
| `/review-suite --against <ref>` | `git diff <ref>...HEAD` + uncommitted |
| `/review-suite --against main` | branch-vs-main view (common before push) |

Lens selection is automatic (see [Triage](#triage-select-the-relevant-lenses)); these flags override it:

| Flag | Effect |
|---|---|
| `--all` | Skip triage; run every installed core lens regardless of surface. |
| `--only <names>` | Run only the named lenses (comma-separated), skip triage. |
| `--skip <names>` | Run the triaged set minus the named lenses. |

If the chosen target has no diff, report that and exit.

## The lenses

`/review-suite` orchestrates these **core** lenses:

- `/thermo-nuclear-code-quality-review` — strict maintainability / abstraction review
- `/ponytail-review` — over-engineering review (what to delete)
- `/ship-gate` — mechanical pre-ship checks (secrets, garbage, debug residue, etc.)
- `/correctness-review` — adversarial logic + test-meaningfulness review, supplemented by the relevant correctness cheat sheets
- `/security-review` — deep exploitable-vulnerability review, supplemented by the relevant OWASP Cheat Sheet Series guidance

## Triage: select the relevant lenses

Not every diff needs every lens — running `/security-review` on a docs-only change or `/correctness-review` on a config-only change wastes a subagent and adds noise. Before fanning out, classify the diff and select the lenses whose surface it actually touches.

**Bias to include.** Triage removes a lens only on *clear* evidence there is no surface for it. When in doubt, keep the lens — a wasted subagent is cheaper than a missed finding. `--all` forces the full set; `--only` / `--skip` override the selection entirely.

Classify the changed files and content (`git diff --stat` for shape, `git diff` for content signals), then apply:

| Lens | Select when the diff… | Safe to skip when the diff is… |
|---|---|---|
| `ship-gate` | always — its checks (secrets, garbage, deps, commit hygiene) apply to any change | never skipped on a non-empty diff |
| `thermo-nuclear` | changes source code / structure | docs-only, data/fixture-only, lockfile-only, or pure rename/move |
| `ponytail` | adds code or abstraction | docs-only, config-only, or pure deletion |
| `correctness-review` | changes executable logic or tests | docs-only, config-only, or pure formatting/rename |
| `security-review` | touches an input boundary, auth, network/HTTP, crypto, deserialization, subprocess, filesystem, secrets/config, SQL, or adds a dependency | pure internal refactor with no external surface, docs, or comments |

Record the decision — every selected lens *and* every skipped lens with its one-line reason — and surface it in the report's `Triage:` line so a skip is always a visible, explained choice, never a silent gap.

## Sub-skill check

Verify each **selected** lens is installed at `~/.claude/skills/<name>/SKILL.md` (or a project-local `.claude/skills/<name>/SKILL.md`). If any selected core lens is missing, **exit immediately** and tell the user which to install — do not silently run a degraded subset of what triage asked for. A lens that triage *deselected* need not be installed; don't check or complain about it.

Example exit message:

```
/review-suite selected these lenses for this diff, but some are not installed:

  - security-review  (expected at ~/.claude/skills/security-review/)

Install them and retry, or re-run with --skip security-review.
```

## Fan-out

**When subagent spawning is available, prefer it.** Spawn one subagent per **selected** lens (from [Triage](#triage-select-the-relevant-lenses)), in parallel, in a single message (e.g. multiple `Task`/`Agent` tool calls in one turn). Each subagent runs its skill against the resolved target diff and returns a JSON array of findings. This is the preferred path: it isolates each lens in its own context and runs them concurrently.

If subagent fan-out is **not** available in the current harness (no `Task`/`Agent` tool, or the environment can't spawn parallel subagents), fall back to running each sub-skill sequentially in the main conversation. The fallback produces the same findings JSON per skill and feeds the same dedupe step — only the concurrency and context isolation are lost. Note in the report which path was used.

Prompt shape per subagent (also the per-skill instruction in the sequential fallback):

> Run `/<sub-skill>` on the diff produced by `<diff command>`. Return ONLY a JSON array of findings, no prose around it. Each finding: `{"file": str, "line": int, "line_end": int|null, "severity": "critical|warn|nit", "summary": str, "rationale": str|null, "source": "<sub-skill>"}`. Use `line` = `line_end` for single-line findings. If the skill has no findings, return `[]`.

Notes per skill:

- **ponytail-review**: maps its `delete:` / `stdlib:` / `native:` / `yagni:` / `shrink:` tags into the `severity` field as `warn` (or `critical` if the finding eliminates a whole abstraction). Include the tag in `rationale`.
- **thermo-nuclear**: prefer `critical` for structural/spaghetti findings, `warn` for boundary/abstraction issues, `nit` only for legibility polish.
- **ship-gate**: its `FAIL` → `critical`, `WARN` → `warn`, `CLEAN` checks contribute no findings.
- **correctness-review**: CONFIRMED logic bug → `critical`; PLAUSIBLE logic bug or weak/missing test → `warn`. It reasons from the diff and repository; `/prove` owns executing counterfactual evidence.
- **security-review**: CONFIRMED exploitable vuln → `critical`; PLAUSIBLE weakness or defense-in-depth gap → `warn`; hardening suggestion → `nit`.

Both `/correctness-review` and `/security-review` self-gate: on a diff with no relevant surface they return `[]`, exactly like ship-gate's CLEAN checks.

`/ship-gate` is hard-coded to `main...HEAD`. If the user passed `--against <other-ref>`, note in the report that ship-gate ran against `main` regardless.

## Dedupe

After all subagents return, dedupe in the orchestrator (not in another subagent).

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
Triage: ran thermo-nuclear, ship-gate, correctness  |  skipped ponytail (pure deletion), security (no external surface)
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

- Triage first, then fail closed on what triage selected — a *selected* lens that isn't installed stops the run; a *deselected* one is ignored. Skipping by triage is deliberate and shown in the `Triage:` line, never silent.
- Bias triage toward inclusion — a wasted subagent is cheaper than a missed finding. Use `--all` to force the full set when in doubt.
- Prefer fanning sub-skills out as parallel subagents when the harness supports it; only chain them sequentially as a fallback when subagent spawning is unavailable.
- Trust each sub-skill's own judgment about what counts as a finding — do not re-filter or re-categorize beyond the dedupe step.
- The suite is diff review only. If the user asks for acceptance-criteria checks or evidence that the change works, point them at `/prove` rather than expanding scope here.
- Plain text only in terminal output. No emojis. If pushing to Hunk, keep comment summaries short — put detail in `rationale`.
- Do not auto-fix. The sub-skills surface findings; the user (or a follow-up pass) acts on them.
- Do not write any artifact under `.agentic/<slug>/`. The terminal report is the primary output; Hunk is an optional secondary medium.
