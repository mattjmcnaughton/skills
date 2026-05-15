---
name: merge-pr
description: Merge a GitHub PR, then tear down the local worktree, prune the branch, and mark any linked Linear/GitHub issue Done. Use as the final step after a PR is approved.
---

`/merge-pr` is the close-out skill: merge + cleanup. It replaces "merge, then remember to delete the worktree, then update the ticket" — that sequence is here as one operation.

## Preconditions

- The PR exists, is approved (or the user is choosing to override), and CI is green (or the user explicitly accepts merging with failing checks).
- The user is in the repo (main worktree or task worktree — both work; we'll move out of the task worktree before deleting it).

## Gather context

1. **PR reference.** If the user provided one, use it. Otherwise infer from the current branch:
   ```bash
   gh pr view --json number,headRefName,state,mergeable,mergeStateStatus
   ```
2. **Branch + worktree.** `git branch --show-current` and `git worktree list` to find the path.
3. **Linked issue.** Read `.agentic/<slug>/ticket.json` if it exists. Otherwise scan the PR body for `Closes #N` / `Fixes #N` / `AGE-N`.
4. **Merge strategy.** Default is `--squash`. Ask if the repo conventions differ (some repos use `--merge` or `--rebase`).

## Confirm

Show a summary and ask for one confirmation:

```
About to:
  Merge PR #<N> (<title>) into main using --squash
  Delete worktree: <path>
  Delete branch:   <branch>
  Mark <issue> as Done in <Linear|GitHub>

Proceed? (y/n)
```

## Execute

1. **Merge.**
   ```bash
   gh pr merge <N> --squash --delete-branch
   ```
   `--delete-branch` removes the remote branch. The local branch is still ours to delete in step 3.

2. **Leave the worktree** if currently inside it:
   ```bash
   cd $(git -C <task-worktree>/.. rev-parse --show-toplevel)
   ```
   (Or any path outside the worktree being removed.)

3. **Remove the worktree and local branch.**
   ```bash
   git worktree remove <path>
   git branch -d <branch>
   ```
   If `-d` rejects an "unmerged" branch (can happen with squash since the upstream history differs), warn the user, then fall back to `-D` only on explicit confirmation.

4. **Close the issue.**
   - **Linear** (when `ticket.source == "linear"`): use the `linear` skill (when present) or the Linear MCP to move the issue to "Done". If neither is wired up, surface a manual instruction.
   - **GitHub** (when `ticket.source == "github"` or detected from PR body): `gh issue close <N>`. `Closes #N` in the PR body usually does this automatically on merge — verify, and only call `gh issue close` if it didn't.

5. **Report.**
   ```
   Merged PR #<N>.
   Deleted worktree: <path>
   Deleted branch:   <branch>
   <Linear|GitHub> issue <id>: Done
   ```

## Error handling

- **PR not mergeable** (failing checks, conflicts, missing reviews): surface the exact `mergeStateStatus`, stop, do not run cleanup. The user resolves and re-runs.
- **Uncommitted changes in the worktree**: stop. Don't merge based on a PR that doesn't reflect local state — the user should commit or stash first.
- **Branch unmerged after merge** (squash-related): warn, ask for `-D` permission, don't auto-force.
- **Linear/GitHub close failure**: don't roll back the merge. Report the failure and tell the user to update the issue manually.

## Guidelines

- One merge strategy per repo. Don't switch styles unprompted.
- Never `--admin` to bypass branch protection unless the user explicitly says so.
- Confirm before destructive steps (worktree removal, branch force-delete). The cost of pausing is small; the cost of losing a worktree with unpushed work is large.
- Plain text only.
