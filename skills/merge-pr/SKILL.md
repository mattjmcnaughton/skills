---
name: merge-pr
description: Merge an approved GitHub PR via rebase and delete the remote branch. Use as the final step after the PR is approved and CI is green.
---

Merge the PR for the current branch (or a specified PR) using an explicit PR number and `--repo` with `gh pr merge --rebase --delete-branch`. Keep history linear and request remote branch deletion, leaving all local cleanup to `/delete-worktree`.

## Preconditions

- `gh` is authenticated. If not, surface the error from `gh auth status`.
- The PR is approved (or the user explicitly chooses to override) and CI is green (or the user explicitly accepts merging with failing checks).
- No uncommitted changes lingering. If there are, stop and tell the user.

## Gather context

1. **PR reference.** If the user provided one, use it. Otherwise infer from the current branch:
   ```bash
   gh pr view --json number,title,url,baseRefName,headRefName,isCrossRepository,state,mergeable,mergeStateStatus
   ```
   Resolve the PR's base repository (`owner/repo`, including the host for GitHub Enterprise) from its URL or repository context. For a supplied PR, inspect that PR rather than the current branch's PR. Carry the explicit repository and PR number into every subsequent command; do not assume the fork's head repository is the merge destination.
2. **Branch state.** `git branch --show-current` and `git rev-parse --abbrev-ref HEAD@{upstream}`.
3. **Mergeability.** If `mergeStateStatus` is not `CLEAN`, surface the exact value and stop — the user resolves and re-runs. Exception: if `mergeable` is `UNMERGEABLE` (or `UNKNOWN`), wait 15 seconds and re-query once before surfacing — GitHub sometimes returns this while it's still computing mergeability right after a push.

## Confirm

Show the proposed action and ask once:

```
About to:
  Merge PR #<N> (<title>) into <base> using --rebase
  Repository: <owner/repo>
  Request remote branch deletion: <branch> (same-repository PR only)
  Leave local branches and worktrees unchanged

Proceed? (y/n)
```

## Execute

1. **Merge** a same-repository PR with rebase and remote branch deletion:
   ```bash
   gh pr merge <N> --repo <owner/repo> --rebase --delete-branch
   ```
   The explicit `--repo` flag disables GitHub CLI's local branch/worktree cleanup. Keep it even when running in that repository; `GH_REPO` or a PR URL alone is not a substitute. Do not switch branches, pull, prune, remove worktrees, or delete local branches here.

   For a fork PR, omit `--delete-branch` and state in the confirmation that the fork branch will be left alone. If a merge queue or repository policy rejects this operation, stop and report the blocker; do not bypass it or silently choose another merge mode. Do not rerun a merge merely to retry branch deletion.
2. **Verify and report** merge state and remote branch deletion separately. Re-read the PR with `gh pr view <N> --repo <owner/repo> --json state,mergedAt,url`. For requested deletion, verify the head branch's existence through a read-only GitHub API check, treating authentication/network failures as unknown, not as proof of deletion. Report merged, queued/pending, or failed accurately, and remote branch deleted, retained, or unknown. If the command fails after a partial success, inspect state before deciding what remains. Include the PR URL and explain that local cleanup is still the responsibility of `/delete-worktree`.

## Guidelines

- Always `--rebase`. Don't switch to `--squash` or `--merge` unless the user explicitly asks.
- Request `--delete-branch` for same-repository PRs; never claim deletion without verifying it. Fork branches and blocked deletion require a separate decision.
- Never `--admin` to bypass branch protection unless the user explicitly says so.
- Don't touch local worktrees, local branches, or linked issues here — this skill is scoped to the merge itself.
- Plain text only. No emojis in confirmation or report unless the user asks.
