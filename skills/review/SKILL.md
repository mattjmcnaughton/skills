---
name: review
description: Self-review the current local changes against plan.md before committing. Produces `.agentic/<slug>/review.md` covering acceptance-criteria verification and code-quality findings. Use after /build and before /create-commit.
---

`/review` checks the work `/build` produced against `plan.md` — both whether the acceptance criteria pass and whether the code quality is acceptable — and writes a single `.agentic/<slug>/review.md`.

This is **pre-commit self-review** on local changes. For reviewing an open GitHub PR, use `/review-pr`.

## Locate inputs

- `.agentic/<slug>/plan.md` — required (acceptance criteria, verification plan, optimization target).
- `.agentic/<slug>/diary.md` — required (what was actually done, files touched).
- Working tree: staged + unstaged changes. If everything is already committed in checkpoint mode, review the commits on this branch instead.

If a `review.md` already exists, ask whether to overwrite or append a second pass.

## Process

1. **Determine scope.** Files changed since branch point + any uncommitted edits. Use `git diff main...HEAD` plus `git diff` and `git diff --cached`.

2. **Walk the verification plan.** For each step in plan.md's `Verification plan`, actually run the command or open the URL and observe the result. Don't assert from inspection alone when the plan defined a runnable check.

3. **Walk acceptance criteria.** For each criterion in plan.md, mark `PASS` / `FAIL` / `PARTIAL`, citing the evidence (test output, command result, file:line). For instrumentable criteria (latency, error rate, etc.), include actual measurements vs targets.

4. **Code-quality review.** Examine the diff with the optimization target as the lens. Look at: correctness, alignment with patterns in plan.md's Research section, error handling, test coverage of the new code, breaking changes for callers, and any obvious tripwires.

   Also read project guidance — `CLAUDE.md`, `AGENTS.md`, any `.claude/rules/*.md` — and apply repo-specific conventions.

5. **Categorize findings**:
   - **Critical** — must fix before commit/PR.
   - **Suggestion** — should consider.
   - **Nit** — optional polish.

   If nothing is wrong, say so. Don't manufacture findings.

6. **Verdict** — `Approve` / `Approve with minor changes` / `Needs revision`.

## review.md template

```markdown
# Review: <task name>

**Slug**: <slug>
**Scope**: <files changed / branch range>
**Optimization target**: <from plan.md>

## Acceptance criteria
| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | <name>    | PASS   | <test/command + result> |
| 2 | ...       | FAIL   | <what failed, where>    |

[For instrumentable criteria, include measurements:]
**Metric**: <name>  **Baseline**: <v>  **Target**: <v>  **Actual**: <v>  **Status**: MET|NOT MET

## Code-quality findings

### Critical
- <file:line> — <what's wrong, recommended fix>

### Suggestions
- <file:line> — <suggestion + rationale>

### Nits
- <file:line> — <optional polish>

## Coverage and impact
- **Tests for new code**: <gaps or "adequate">
- **Breaking changes**: <list or "none">
- **Docs to update**: <list or "none">

## Verdict
<Approve | Approve with minor changes | Needs revision>
<one-sentence rationale>
```

## Guidelines

- Be specific. Findings without `file:line` aren't actionable.
- Run the verification plan; don't just read code and infer it would work.
- Prioritize honestly. A nit is not a blocker. "No changes necessary" is a valid verdict.
- Frame around the code, not the author.
- Don't implement fixes here — `/review` is advisory. If revisions are needed, the user (or a return to `/build`) handles them.
- Plain text only. No emojis.
