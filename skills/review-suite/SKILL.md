---
name: review-suite
description: Runs relevant code-quality, correctness, security, and ship-hygiene reviews on a local diff and deduplicates findings. Use for "full review" or "run the reviews" before committing or pushing. Acceptance evidence belongs to /prove.
---

`/review-suite` runs several focused review skills in parallel and dedupes their findings into one report, printed to the terminal and saved to `.agentic/review.md`.

It is **strictly diff-oriented**: code quality, correctness, security, and ship hygiene. It does not read `plan.md` or check acceptance criteria — `/prove` owns that evidence.

On every outcome, including early exits or a pause for clarification, write the report as specified in "Output" below. Do not leave a previous run's report looking current.

## Target

Default to the complete task branch against its base, including staged and unstaged tracked changes and non-ignored untracked files. Checkpoint commits and a final `/build` commit must not disappear from review just because the working tree is clean.

| Invocation | Diff scope |
|---|---|
| `/review-suite` (default) | Net tracked changes from the resolved base's merge base through the working tree, plus non-ignored untracked files |
| `/review-suite --against <ref>` | Same scope, with an explicit base ref |
| `/review-suite --working-tree` | `git diff HEAD` — staged and unstaged tracked changes, plus non-ignored untracked files |

Resolve the base once: use `--against` when supplied; otherwise use the task's known PR target branch, then the repository's remote default branch (for example `origin/HEAD`), then local `main` if available. If the base is unknown, ambiguous, or cannot be resolved, ask rather than silently reviewing only uncommitted changes. Do not use the feature branch's own tracking upstream as its base. Reject `--against` combined with `--working-tree`.

For branch review, resolve `BASE=$(git merge-base <resolved-ref> HEAD)` and use `git diff "$BASE"` for the content and `git diff --stat "$BASE"` for triage. This is the net candidate state, including committed, staged, and unstaged tracked changes; do not concatenate patches that may undo each other. For `--working-tree`, use `git diff HEAD` and `git diff --stat HEAD`. Report the resolved ref, merge-base commit, and scope in `Target:` and pass the same resolved diff command to the selected lenses.

For both modes, also collect `git ls-files --others --exclude-standard -z` from the worktree root. Handle NUL-delimited paths without whitespace splitting and exclude the exact generated report path `.agentic/review.md` from this untracked list. Do not exclude all of `.agentic/` unless Git ignores it. Do not stage files, use `git add -N`, or change ignore rules to make them visible.

Include each listed file's content and file type in triage and review as a new file, even when the tracked diff is empty. Read text files directly with line numbers; an optional addition patch is `git diff --no-index -- /dev/null "$path"` (exit 1 means differences, not failure). Do not follow symlinks to read their targets; review the link itself. Identify binary or unreadable files and disclose any content-review limits rather than silently omitting them. If an untracked path also appears in the tracked diff (for example after `git rm --cached`), reconcile it by path: inspect the retained content and the tracking removal without double-counting or calling it a genuinely new file.

Pass the same explicit untracked path list alongside the tracked diff command to every selected lens, including sequential calls. Each lens must inspect that content, not just rerun `git diff`. Record the untracked paths separately in the report. If a listed file disappears or cannot be read during review, report the coverage gap.

Lens selection is automatic (see [Triage](#triage-select-the-relevant-lenses)); these flags override it:

| Flag | Effect |
|---|---|
| `--all` | Skip triage; run every installed core lens regardless of surface. |
| `--only <names>` | Run only the named lenses (comma-separated), skip triage. |
| `--skip <names>` | Run the triaged set minus the named lenses. |

Only report no diff and exit when both the tracked diff and the eligible untracked file list are empty.

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

Classify the changed files and content using the resolved target's stat and content commands plus its untracked file list and contents from "Target" above, then apply:

| Lens | Select when the diff… | Safe to skip when the diff is… |
|---|---|---|
| `ship-gate` | always — its checks (secrets, garbage, deps, commit hygiene) apply to any change | never skipped on a non-empty diff |
| `thermo-nuclear` | changes source code / structure | docs-only, data/fixture-only, lockfile-only, or pure rename/move |
| `ponytail` | adds code or abstraction | docs-only, config-only, or pure deletion |
| `correctness-review` | changes executable logic or tests | docs-only, config-only, or pure formatting/rename |
| `security-review` | touches an input boundary, auth, network/HTTP, crypto, deserialization, subprocess, filesystem, secrets/config, SQL, or adds a dependency | pure internal refactor with no external surface, docs, or comments |

Record the decision — every selected lens *and* every skipped lens with its one-line reason — and surface it in the report's `Triage:` line so a skip is always a visible, explained choice, never a silent gap.

## Sub-skill check

Verify each **selected** lens is available to the current client. Use its available-skill catalog or discovery tool first; a listed skill need not already be loaded, and does not need to exist at a Claude-specific path. Respect any invocation restrictions reported by the client.

If no catalog or discovery tool is available, check the current client's configured project and user skill directories for `<name>/SKILL.md`, including symlinked installations. Use paths documented for that client or supplied by its configuration (for example `.claude/skills/` for Claude, or `.agents/skills/` for clients that support it); do not assume another client's directories are active. Merely finding a vendored source directory does not prove it is installed or invocable. If availability cannot be established, report that uncertainty rather than asserting the skill is missing.

If any selected core lens is missing, unavailable to invoke, or cannot be located, stop before fan-out, save an incomplete report to `.agentic/review.md`, and tell the user which lens needs installation or configuration — do not silently run a degraded subset of what triage asked for. A lens that triage *deselected* need not be available; don't check or complain about it.

Example exit message:

```
/review-suite selected these lenses for this diff, but some are unavailable:

  - security-review  (not listed in the current client's available-skill catalog)

Install or enable them for this client and refresh discovery, then retry;
or re-run with --skip security-review.
```

## Fan-out

**When subagent spawning is available, prefer it.** Spawn one subagent per **selected** lens (from [Triage](#triage-select-the-relevant-lenses)), in parallel, in a single message (e.g. multiple `Task`/`Agent` tool calls in one turn). Each subagent runs its skill against the resolved target diff and returns a JSON array of findings. This is the preferred path: it isolates each lens in its own context and runs them concurrently.

If subagent fan-out is **not** available in the current harness (no `Task`/`Agent` tool, or the environment can't spawn parallel subagents), fall back to running each sub-skill sequentially in the main conversation. The fallback produces the same findings JSON per skill and feeds the same dedupe step — only the concurrency and context isolation are lost. Note in the report which path was used.

Prompt shape per subagent (also the per-skill instruction in the sequential fallback):

> Run `/<sub-skill>` for `/review-suite` on the diff produced by `<diff command>`. This is a findings-only suite invocation: do not offer or apply fixes, stage files, rewrite commits, or write report files. The suite owns the combined report. Use this output contract instead of standalone prose, scoring footers, or follow-up prompts. Return ONLY a JSON array of findings, no prose around it. Each finding: `{"file": str, "line": int, "line_end": int|null, "severity": "critical|warn|nit", "summary": str, "rationale": str|null, "source": "<sub-skill>"}`. Use `line` = `line_end` for single-line findings. If the review completed without findings, return `[]`. If it cannot complete, surface the failure to the suite rather than returning a misleading empty array.

Notes per skill:

- **ponytail-review**: maps its `delete:` / `stdlib:` / `native:` / `yagni:` / `shrink:` tags into the `severity` field as `warn` (or `critical` if the finding eliminates a whole abstraction). Include the tag in `rationale`.
- **thermo-nuclear**: prefer `critical` for structural/spaghetti findings, `warn` for boundary/abstraction issues, `nit` only for legibility polish.
- **ship-gate**: its `FAIL` → `critical`, `WARN` → `warn`, `CLEAN` checks contribute no findings.
- **correctness-review**: CONFIRMED logic bug → `critical`; PLAUSIBLE logic bug or weak/missing test → `warn`. It reasons from the diff and repository; `/prove` owns executing counterfactual evidence.
- **security-review**: CONFIRMED exploitable vuln → `critical`; PLAUSIBLE weakness or defense-in-depth gap → `warn`; hardening suggestion → `nit`.

Both `/correctness-review` and `/security-review` self-gate: on a diff with no relevant surface they return `[]`, exactly like ship-gate's CLEAN checks.

Pass `/ship-gate` the target mode and actual resolved merge-base commit for branch reviews, alongside the diff command; do not pass an undefined `$BASE` variable into a separate agent context. It must derive changed-file and added-file lists from the same target, and check commit hygiene over that merge base through `HEAD`. For `--working-tree`, explicitly pass `git diff HEAD` and no commit range; record commit hygiene as not applicable. Its local gate runs on the current working tree, not an isolated diff; disclose that distinction in the combined report. Do not permit a fallback to its standalone `main` scope.

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

## Output: terminal and `.agentic/review.md` (always)

Always save the report to `.agentic/review.md` relative to the current worktree's repository root (`git rev-parse --show-toplevel`), not the shell's subdirectory or `.agentic/<slug>/`. Create `.agentic/` if needed and replace the previous report, rather than appending. Write after review or when stopping, so generating the report does not change the diff being reviewed. The orchestrator owns this file; sub-skills do not write it.

Print the same report to the terminal and identify its saved path. Include the run time, target, completion status, lens coverage, and deduped findings. For no diff, write `Status: no diff`; for a completed review with no findings, write `Status: completed` and `No findings.`. For invalid arguments, unresolved targets, missing skills, or failed lenses, write `Status: incomplete`, the reason, any partial findings, and what did not run. Never describe an incomplete review as clean. If the report cannot be written, report the write failure explicitly and do not claim the report was saved.

```
review-suite report
Run: <ISO timestamp>
Status: completed
Target: <diff scope>
Triage: ran thermo-nuclear, ship-gate, correctness  |  skipped ponytail (pure deletion), security (no external surface)
Findings: <N> (after dedupe from <M> raw)

[critical] src/api.ts:88 — debug console.log in production path  (via: ship-gate)
[critical] src/repo.py:14-38 — AbstractRepository wrapper with one implementation. Inline it.  (via: ponytail-review, thermo-nuclear)
[warn]     src/loader.py:14 — new outbound HTTP read to api.partner.example  (via: ship-gate)
...
```

If every selected sub-skill successfully returned `[]`, include `No findings.` in the saved and printed report, then stop.

## Guidelines

- Triage first, then fail closed on what triage selected — a *selected* lens that isn't installed stops the run; a *deselected* one is ignored. Skipping by triage is deliberate and shown in the `Triage:` line, never silent.
- Bias triage toward inclusion — a wasted subagent is cheaper than a missed finding. Use `--all` to force the full set when in doubt.
- Prefer fanning sub-skills out as parallel subagents when the harness supports it; only chain them sequentially as a fallback when subagent spawning is unavailable.
- Trust each sub-skill's own judgment about what counts as a finding — do not re-filter or re-categorize beyond the dedupe step.
- The suite is diff review only. If the user asks for acceptance-criteria checks or evidence that the change works, point them at `/prove` rather than expanding scope here.
- Plain text only in terminal output. No emojis.
- Do not auto-fix. The sub-skills surface findings; the user (or a follow-up pass) acts on them.
- Always write `.agentic/review.md`; do not put the report under `.agentic/<slug>/` or stage or commit it automatically.
