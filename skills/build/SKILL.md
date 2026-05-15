---
name: build
description: Execute `.agentic/<slug>/plan.md` step by step, writing `diary.md` as it goes. Asks at start whether to use checkpoint commits and red/green TDD. Pauses and asks the user when reality diverges from the plan. Use after /prep.
---

`/build` reads `plan.md`, walks the implementation steps, runs the gate, and writes a `diary.md` rich enough that `/rehydrate` can pick up the work in a fresh session.

## Locate inputs

`.agentic/<slug>/plan.md` is required. If missing, suggest `/prep` first. Read `ticket.json` if present.

If `.agentic/<slug>/diary.md` already exists with step entries, **stop** and suggest `/rehydrate` instead of starting fresh. Only continue with a clean diary on explicit user confirmation.

## Opening prompts

Before writing any code, ask:

1. **Checkpoint commits?** (y/n) — When yes, create one conventional commit per plan step after the gate passes. When no, work freely and commit at the end.
2. **Red/green TDD?** (y/n) — When yes, each step writes a failing test, then implements until green, then refactors. When no, freer-form.

Write the answers into diary.md so `/rehydrate` knows the mode.

## Per-step loop

For each step in `plan.md`:

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
