---
name: create-pr
description: Push the current branch and open a GitHub PR with title and description derived from `.agentic/<slug>/plan.md` and `diary.md`. Use after /create-commit when changes are ready for review.
---

Push the active branch to origin and open a GitHub PR via `gh`. The body is composed from the task's plan and diary so reviewers see the goal, acceptance criteria, and what was actually done.

## Preconditions

- Inside the worktree for the task (so `.agentic/<slug>/` resolves cleanly).
- The branch is committed; nothing staged or unstaged should be lingering. If there are uncommitted changes, stop and tell the user.
- `gh` is authenticated. If not, surface the error from `gh auth status`.

## Gather context

1. **Branch state.** `git branch --show-current`, `git rev-parse --abbrev-ref HEAD@{upstream}` (might fail if not pushed yet — that's expected).
2. **Diff scope.** Commits and files in `git log <base>..HEAD` and `git diff <base>...HEAD`.
3. **Plan + diary.** Read `.agentic/<slug>/plan.md` and `diary.md`. These drive the PR body.
4. **Ticket.** If `.agentic/<slug>/ticket.json` exists, capture the identifier for `Closes #N` / `Fixes #N`.

## Build the PR

**Base branch**: `main` unless the user specifies otherwise.

**Title** (≤70 chars): one line summarizing the change in conventional-commit style without the `(scope)` parens. Examples:
- `feat: add semantic indexing to search`
- `fix: race condition in worker pool shutdown`

**Body** (HEREDOC):

```markdown
## Summary
<2-4 bullets distilled from plan.md goal + diary highlights>

## Acceptance criteria
<paste the criteria from plan.md as `- [ ]` checkboxes; the reviewer ticks them off
 while walking the Test plan below>

## Test plan
<paste plan.md's Verification plan as a checklist the reviewer can run>

## Notes
<diary's "Issues/Deviations" lines, if any — surface them so the reviewer isn't surprised>

<footer>
Closes #<N>     <-- only if ticket.json had a Linear/GitHub identifier
```

Do **not** include AI attribution or `Generated with` trailers unless the user explicitly asks for them.

## Execute

1. **Push the branch** (with upstream set on first push):
   ```bash
   git push -u origin <branch>
   ```
2. **Show the proposed title and body** to the user. Ask "Create the PR? (y/n)".
3. **On y**: open the PR with `gh pr create --base main --title "..." --body "$(cat <<'EOF' ... EOF)"`.
4. **Report** the PR URL.

## Guidelines

- Title in description-mode language ("add X", "fix Y"), not "this PR adds X".
- Don't draft against `--draft` by default; if the work is incomplete, the user should say so.
- Don't `--no-verify` or skip hooks unless the user explicitly requests it.
- If the branch tracks an existing PR, surface that and ask whether to update or open new.
- Plain text only. No emojis in title or body unless the user asks.
