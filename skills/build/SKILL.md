---
name: build
description: Executes or resumes plan.md step by step, preserving progress and decisions in diary.md. Use after /prep to implement a plan, or after a pause or /rehydrate to continue. Asks about checkpoint commits and TDD only when not recorded.
---

`/build` reads `plan.md`, walks the implementation steps, runs the gate, and writes a `diary.md` rich enough that `/rehydrate` can pick up the work in a fresh session.

## Locate inputs

`.agentic/<slug>/plan.md` is required. If missing, suggest `/prep` first. Read `ticket.json` or `ticket.md` in the same directory if present; neither is required. Accept free-form Markdown without conversion. If both exist, read both and ask about material conflicts rather than silently choosing one.

If `.agentic/<slug>/diary.md` exists, read and preserve it. Resume using the check below rather than starting fresh. `/rehydrate` is useful for restoring context in a new session, but is not a prerequisite for continuing here. Restarting completed work requires an explicit user request; retain the prior diary history.

## Resume check

- Read the recorded checkpoint/TDD choices, step statuses, current-step pointer, decisions, and blockers. Reuse those choices; ask only for missing choices, not ones already recorded.
- Check the relevant files, Git status, and recorded commits against the diary. Reuse a just-completed `/rehydrate` reconciliation when the state has not changed. If code, commits, or the pointer contradict recorded progress, surface the discrepancy and ask before proceeding; do not erase history or repeat completed work to resolve it.
- Continue from the first incomplete step in plan order. For an `in_progress` step, preserve its partial work and finish what remains. For a `blocked` step, check whether the recorded blocker is resolved; if not, report it and wait. Do not treat ordinary partial work as a discrepancy or ask for redundant permission to resume.
- If all steps are complete, do not restart implementation or repeat completed commit handling. Report the state and suggest `/review-suite` when final handling is done; if it is still pending, continue there. Ask if the diary and Git state cannot establish whether it already happened.

## Opening prompts

On a fresh start, or for choices missing from the diary, ask before writing code:

1. **Checkpoint commits?** (y/n) — When yes, create one conventional commit per plan step after the gate passes. When no, work freely and commit at the end.
2. **Red/green TDD?** (y/n) — When yes, each step writes a failing test, then implements until green, then refactors. When no, freer-form.

Record new answers in diary.md without replacing existing entries so `/rehydrate` knows the mode.

## Per-step loop

For each remaining step in `plan.md`, starting from the resume point when applicable:

1. **Implement** the step's deliverables. If TDD is on: failing test first, then implementation. Reference the patterns and file paths called out in plan.md's Research section — `/prep` did that discovery already.

2. **Run the gate command** from plan.md.
   - **Gate passes + checkpoints on**: create a conventional checkpoint commit (`feat(scope): step N — <subject>` or appropriate type). Use `/create-commit` semantics.
   - **Gate passes + checkpoints off**: continue, no commit yet.
   - **Gate fails**: do not move on. Create a WIP commit only if checkpoints are on (`wip(scope): step N — <subject> [gate failed]`). Report the failure and pause.

3. **Update diary.md.** Append a step entry capturing what was done, why, and any deviation from plan. (See diary spec below — this fidelity is what `/rehydrate` depends on.)

4. **Check for divergence.** If you discovered the plan doesn't fit reality (missing dep, wrong file structure, an acceptance criterion that needs renegotiating, an unanticipated subtask), do not push through. Stop, write the divergence into diary.md, and ask the user: continue / amend the plan inline / re-enter `/prep`.

5. **Final step**: run the full gate, walk the verification plan, confirm each acceptance criterion. This is always the last entry in plan.md and the last entry in diary.md.

## diary.md format

```markdown
# Diary: <task name>

**Slug**: <slug>
**Started**: <ISO date>
**Checkpoints**: yes|no
**TDD**: yes|no
**Current step**: <N> (or "done")

---

## Step 1: <name>
**Status**: completed
**Commit**: <sha-short> (if checkpoint commit made)
**Files**: <paths touched>
**What**: <2-3 lines: concrete actions>
**Why**: <key decisions and rationale>
**Deviations**: <none | what differed from plan, and why>

## Step 2: ...
```

The `Current step` pointer and per-step `Status` (`pending`, `in_progress`, `completed`, `blocked`) are what `/rehydrate` reads to resume cleanly.

## Final commit handling

When all steps pass:

- **Checkpoints off**: produce one commit covering the whole task.
- **Checkpoints on**: ask whether to squash the step commits into one (cleaner PR history), keep them as-is, or interactively pick which to squash.

Record the outcome and resulting commit references in diary.md so a later resume does not repeat this handling.

Use the squash form when squashing:
```
<type>(<scope>): <task description>

- Step 1: <brief>
- Step 2: <brief>
- ...
```

## Guidelines

- Always write diary.md. There is no opt-out; `/rehydrate` depends on it.
- Stay aligned with the optimization target. When in doubt between two approaches, pick the one closer to what plan.md says to optimize for.
- Pause on gate failures and on divergence. Don't silently amend the plan to match what you did.
- Plain text only. No emojis in code, comments, commits, or diary.
