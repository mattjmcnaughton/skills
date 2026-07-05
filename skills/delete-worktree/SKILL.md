---
name: delete-worktree
description: Tear down a git worktree and its local branch created by /create-worktree. Use after /merge-pr (or when abandoning a task) to clean up the isolated workspace.
---

Remove a worktree and delete its local branch. Counterpart to `/create-worktree`. Scoped strictly to local cleanup — does not touch remotes, issues, or `.agentic/<slug>/` contents on the main branch.

## Input

The user usually provides one of:
- A slug ("AGE-4-add-semantic-indexing") — preferred.
- A worktree path (".worktrees/myapp-AGE-4-add-semantic-indexing").
- Nothing — assume the current worktree is the target.

---

## Process

### 1. Resolve the target

- If the user gave a slug: worktree path is `.worktrees/<repo>-<slug>`, branch is `<user>/<slug>` (or just `<slug>` if no user prefix is configured).
- If they gave a path: read its branch with `git -C <path> branch --show-current`.
- If nothing: use `git worktree list` and `git branch --show-current` from the current location. Confirm that the current worktree is not the main repo worktree — refuse to delete the main one.

### 2. Check for uncommitted or unpushed work

```bash
git -C <path> status --porcelain
git -C <path> log @{u}.. 2>/dev/null
```

If either is non-empty, stop and surface what's there. The user must commit/push/stash or explicitly say "delete anyway" before proceeding.

### 3. Confirm

```
About to:
  Remove worktree: <path>
  Delete branch:   <branch>

Proceed? (y/n)
```

### 4. Step out if needed

If the current shell is inside the target worktree, `cd` to the main repo toplevel first:
```bash
cd $(git -C <path>/.. rev-parse --show-toplevel 2>/dev/null || dirname <path>)
```

### 5. Remove the worktree

```bash
git worktree remove <path>
```
If this fails because of leftover state, surface the error. Only fall back to `git worktree remove --force <path>` on explicit user confirmation.

### 6. Delete the local branch

```bash
git branch -d <branch>
```
If `-d` rejects an "unmerged" branch (common after a rebase-merge upstream — the local SHA no longer matches), warn the user and ask before falling back to `-D`.

Note: if the user already ran `/merge-pr`, the local branch is usually already gone — `gh pr merge --delete-branch` deletes it when the checkout was on the PR branch with no unpushed work. In that case `git branch -d` will return `branch '<branch>' not found`; treat that as success and move on.

### 7. Report

```
Removed worktree: <path>
Deleted branch:   <branch>
```

---

## Guidelines

- Never delete the main worktree or the currently-checked-out branch of the main repo.
- Never `--force` (worktree) or `-D` (branch) without explicit confirmation.
- Don't touch the remote branch — `/merge-pr` already handled that with `--delete-branch`.
- Don't touch linked Linear/GitHub issues — out of scope here.
- Plain text only.
