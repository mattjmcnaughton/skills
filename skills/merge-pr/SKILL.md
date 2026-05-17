---
name: merge-pr
description: Merge an approved GitHub PR via rebase and delete the remote branch. Use as the final step after the PR is approved and CI is green.
---

Merge the PR for the current branch (or a specified PR) using `gh pr merge --rebase --delete-branch`. Keep history linear and tear down the remote branch in one step.

## Preconditions

- `gh` is authenticated. If not, surface the error from `gh auth status`.
- The PR is approved (or the user explicitly chooses to override) and CI is green (or the user explicitly accepts merging with failing checks).
- No uncommitted changes lingering. If there are, stop and tell the user.

## Gather context

1. **PR reference.** If the user provided one, use it. Otherwise infer from the current branch:
   ```bash
   gh pr view --json number,title,headRefName,state,mergeable,mergeStateStatus
   ```
2. **Branch state.** `git branch --show-current` and `git rev-parse --abbrev-ref HEAD@{upstream}`.
3. **Mergeability.** If `mergeStateStatus` is not `CLEAN`, surface the exact value and stop — the user resolves and re-runs.

## Confirm

Show the proposed action and ask once:

```
About to:
  Merge PR #<N> (<title>) into <base> using --rebase
  Delete remote branch: <branch>

Proceed? (y/n)
```

## Execute

1. **Merge** with rebase and remote branch deletion:
   ```bash
   gh pr merge <N> --rebase --delete-branch
   ```
2. **Report** the result, including the merged PR URL.

## Guidelines

- Always `--rebase`. Don't switch to `--squash` or `--merge` unless the user explicitly asks.
- Always `--delete-branch` to remove the remote branch.
- Never `--admin` to bypass branch protection unless the user explicitly says so.
- Don't touch local worktrees, local branches, or linked issues here — this skill is scoped to the merge itself.
- Plain text only. No emojis in confirmation or report unless the user asks.
