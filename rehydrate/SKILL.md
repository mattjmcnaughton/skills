---
name: rehydrate
description: Reload context for an interrupted coding task from `.agentic/<slug>/plan.md` and `diary.md` so a fresh session can resume cleanly. Use after a /clear, a session crash, or when picking up tomorrow's work.
---

`/rehydrate` is the resume hook. It reads the plan and diary, summarizes where the task stands, and gets the agent and user back in sync so `/build` can pick up at the next incomplete step.

## Locate the workspace

If the worktree has one `.agentic/<slug>/`, use it. Multiple: pick the one matching the current git branch; else ask. None: there's nothing to resume — suggest `/create-worktree` + `/prep`.

## Read everything

Read in order:
1. `plan.md` — the contract (goal, acceptance, verification, steps).
2. `diary.md` — the history (what was done, when, what mode).
3. `ticket.json` if present — issue context.
4. `git log --oneline <branch-base>..HEAD` — actual commit trail.
5. `git status` and `git diff` — uncommitted state.

## Reconcile

Cross-check plan ↔ diary ↔ git:

- **Plan steps marked done in diary**: confirm the corresponding files exist / commits are present. Flag any discrepancy.
- **Uncommitted changes**: if checkpoints were on but there are uncommitted edits, the previous session likely stopped mid-step. Note which step.
- **Gate state**: re-run plan.md's gate command to confirm the working tree is green/red as the diary claims.

## Present the summary

Show the user a compact status:

```
Resuming: <task name>  (slug: <slug>)

Branch: <branch>  Worktree: <path>
Mode: checkpoints=<y/n>, TDD=<y/n>

Progress: <X> of <Y> steps completed.

Last completed: Step <N> — <name>
  <one-line diary summary>

Current step pointer: Step <N+1> — <name>
  Status in diary: <pending|in_progress|blocked>
  <description from plan.md>

Working tree: <clean | uncommitted changes in N files>
Gate: <last-known status from diary, plus re-run result if it just ran>

Ready to continue. Run /build to resume from Step <N+1>.
```

Surface any reconciliation problems explicitly:
- "Diary says Step 3 done, but no commit and no test file at the expected path."
- "Diary's last step is `in_progress` — likely interrupted mid-implementation."
- "Uncommitted changes from a previous session; review before continuing."

## Edge cases

- **No diary.md**: nothing to rehydrate. Suggest `/build` to start fresh.
- **All steps completed in diary**: suggest `/review`.
- **User wants to restart a step**: honor "redo step N" and reset the diary's current-step pointer.
- **User wants to skip ahead**: honor "skip to step M" but warn if prerequisite steps look incomplete.

## Guidelines

- Don't modify code. `/rehydrate` only reads, summarizes, and reconciles. `/build` does the work.
- Trust the diary for intent but verify against git. The diary records what the agent meant to do; git records what actually landed.
- Keep the summary scannable. If reconciliation needs paragraphs, lead with the one-line bottom-line ("ready to resume" vs "needs cleanup first").
- Plain text only.
