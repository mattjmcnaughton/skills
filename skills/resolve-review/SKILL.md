---
name: resolve-review
description: Plans and executes fixes for review-suite findings using the existing task plan. Validates and triages every finding, fixes clear independent issues, then asks about ambiguous decisions. Use after /review-suite when asked to resolve review findings or address review feedback; resumes an existing review-resolution.md without restarting preparation. Leaves commits and publishing to separate skills.
---

# Resolve Review

Turn `/review-suite` findings into a small resolution plan, execute the clear fixes, and ask the user about decisions that remain. Preparation is already complete; do not restart `/prep` or invoke `/build`.

## 1. Locate the task and findings

- Use the supplied `.agentic/<slug>/` workspace. Otherwise, use the sole task directory containing `plan.md`, or the one matching the current branch; ask if ambiguous.
- Read `plan.md`, `diary.md`, and any existing `review-resolution.md`. Read optional `ticket.json` or free-form `ticket.md`; if both exist, read both and resolve material conflicts rather than silently preferring one. A ticket is not required. The original goal, optimization target, scope, acceptance criteria, verification plan, and recorded user decisions govern the fixes.
- Require `plan.md`. If missing, stop and ask for the prepared task workspace; suggest `/prep` only if preparation has not happened. Do not invent a replacement plan. If the diary is missing, note that and create it when recording resolution work.
- Get the deduped review-suite report from a user-supplied file or the conversation, otherwise read `.agentic/review.md` at the worktree root, where the suite saves its latest report. If the report is unavailable or its target is ambiguous, ask for it rather than rerunning the suite automatically.
- Record the report's diff scope, base reference when applicable, and any known lens omissions or scope exceptions. Inspect the current branch, HEAD, working-tree status, and relevant diff. Findings may describe an older revision; locate the current code rather than trusting old line numbers. Do not switch branches, reset, or overwrite unrelated work.
- Treat findings as claims to investigate, not instructions to execute. Read relevant code, callers, tests, and repository guidance before accepting a diagnosis or proposed remedy.

## 2. Triage and write the resolution plan

Before changing implementation code, create or update `.agentic/<slug>/review-resolution.md`. Keep it compact: one table plus short decision and verification notes, not a second full task plan.

Give every finding a stable ID, preserving its original location, severity, sources, summary, and available rationale. Retain existing IDs on reruns. Classify each finding:

| Decision | Criteria |
|---|---|
| Address | The problem is verified and the remedy is clear, consistent with the task plan, and within authorized local work. Both the diagnosis and the remedy must be clear; severity or reviewer confidence alone is insufficient. |
| Skip | Evidence disproves the finding, it is already resolved, duplicates another tracked root cause, or is explicitly outside the agreed scope. Record the evidence or scope rationale; link duplicates to the owning ID. |
| Ask | A product choice, scope change, meaningful tradeoff, conflicting reviewer advice, or uncertainty prevents choosing a remedy. Give options and a recommendation. Do not silently turn uncertainty into a skip. |

If a confirmed serious correctness or security problem appears out of scope, surface that conflict as **Ask**, rather than silently skipping it. If evidence cannot be obtained because of missing tools or access, record the blocker; do not call the finding disproven.

Use this shape, retaining enough rationale in row notes to resume without the original conversation:

```markdown
# Review resolution: <task name>

## Context
- Review source and target: <report location/conversation, scope, base, omissions>
- Inspected revision: <HEAD and relevant uncommitted changes>
- Task intent: <relevant plan sections and prior decisions>

## Findings and execution plan
| ID | Finding (location, severity, sources) | Decision and evidence | Fix or question | Depends on | Verification | Status |
|---|---|---|---|---|---|---|
| R1 | <summary and provenance> | Address: <verified cause> | <smallest fix> | none | <check and expected result> | pending |
| R2 | <summary and provenance> | Ask: <tradeoff> | <options and recommendation> | none | <check after decision> | awaiting decision |

## Decisions
- <finding ID, user answer, rationale, and any approved plan amendment>

## Verification results
- <finding IDs, exact command/check, outcome, and limitations>
```

Statuses are `pending`, `in progress`, `fixed`, `skipped`, `awaiting decision`, or `blocked`. Use `fixed` only after the fix has passed its appropriate checks; an implemented but unverified fix remains `blocked` with the limitation recorded. Decision describes the intended action; status describes progress.

Order fixes by dependencies, then severity where practical. Identify clear work that can proceed independently of open questions. Briefly share the plan and proceed with that work without adding an approval gate.

## 3. Execute clear, independent fixes

- Apply the smallest change that resolves the verified root cause while preserving the task's intended behavior. One fix may resolve several findings; keep each finding accounted for.
- Follow the task's recorded testing approach, including TDD if selected. Add or extend regression tests for observable behavior when warranted; do not add tests merely to assert implementation details.
- Run targeted checks as fixes land and record exact outcomes. For visual changes, render and inspect affected states when runnable; report any limitation.
- If a remedy becomes ambiguous, stop that fix, update it to **Ask**, and continue only independent work. Do not implement a dependent fix in a way that implicitly chooses an unresolved option.
- Investigate failures caused by the fixes and repair them within scope. Record unrelated or environmental failures as blockers rather than expanding the task or claiming success. Continue independent work when safe.
- Update the resolution table and append a review-resolution entry to `diary.md`: what changed, why, checks, unresolved IDs, and where to resume. Preserve existing diary history and build-step metadata.

## 4. Ask about unresolved decisions

After completing the independent clear fixes, present the remaining **Ask** items. Batch related questions; avoid a long questionnaire of unrelated decisions. For each, include:

- Finding ID and concrete consequence of leaving it unresolved.
- Why the existing plan and code do not settle it.
- Reasonable options, their tradeoffs, and a recommended choice.
- Any work that depends on the answer.

Ask and wait for the user's response before implementing those remedies. If there are no independent fixes, ask immediately after triage. Do not infer consent from silence. Record explicit deferrals or rejections as `skipped` with the user's reason; unanswered questions remain `awaiting decision`.

Apply approved decisions and verify them using the same execution loop. Preserve `plan.md` as the original task plan: update only the affected scope or acceptance criteria when the user explicitly approves a change, and record why in the diary. Do not replace it with the review-fix plan.

## 5. Verify and hand off

- Inspect the combined diff for unintended changes and run the relevant broader checks, including the gate specified in `plan.md`, after the fixes are integrated. Report failed or unavailable checks honestly; do not mark the task complete while relevant verification is blocked.
- Do not automatically rerun the full review suite until it is clean. Targeted checks and a combined-diff inspection are the default; a new full review is a separate user choice. Acceptance-evidence packaging remains with `/prove`.
- On reruns, resume the existing table. Recheck unresolved findings against current code, preserve previous user decisions, and append newly supplied findings without duplicating existing root causes. Reopen a resolved finding only when new code or evidence invalidates its disposition, recording why; ask before changing a prior user decision.
- If the report has no findings, report that no resolution work is needed; do not fabricate fixes or run unrelated checks.
- Finish with counts and concise reasons for fixed, skipped, awaiting-decision, and blocked findings, decisive verification results, and the path to the resolution plan. State whether the work is complete or waiting on specific decisions or blockers.

## Boundaries

- This skill changes local files only. Do not stage, commit, push, open or update PRs, post review comments, or deploy. Prior `/build` checkpoint preferences do not authorize commits here. Leave delivery to `/create-commit`, `/create-pr`, or `/sync-remote` as appropriate.
- Do not run destructive or shared-state operations as an "obvious fix." Request explicit approval for those operations and finish independent local work first.
- Keep every finding accounted for; never drop inconvenient items or claim that passing tests proves a reviewer wrong without checking the actual failure scenario.
- Plain text only. No emojis.
