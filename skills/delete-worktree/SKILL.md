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

## Preflight: is `worktree-manager` installed?

Assume the CLI is installed and call it directly. Only check if a call fails with "command not found":

```bash
command -v worktree-manager >/dev/null
```

If the binary is missing:

1. Tell the user `worktree-manager` isn't installed and point them at the install instructions in the upstream README: <https://github.com/mattjmcnaughton/worktree-manager#installation>.
2. Then fall back to the raw `git worktree` commands documented in the **Fallback** section so the immediate task isn't blocked. Be explicit when you do this — the CLI handles the dirty-check, hooks, and task-store cleanup for you; the fallback doesn't.

---

## Process (preferred: `worktree-manager`)

### 1. Resolve the slug

The CLI deletes by slug — it looks the task up in its metadata store, then resolves the worktree path and branch from there.

- If the user gave a slug, use it.
- If they gave a path or nothing: run `worktree-manager list` and pick the slug whose `WorktreePath` matches the target path (or matches the current `pwd` when no input was given). If no match is found, fall through to the raw-git path — the task wasn't created by `worktree-manager`.
- Refuse to operate on the main worktree.

### 2. Confirm

```
About to:
  Remove worktree: <path>
  Delete branch:   <branch>

Proceed? (y/n)
```

### 3. Step out if needed

If the current shell is inside the target worktree, `cd` to the main repo toplevel first — `worktree-manager` won't operate on its own cwd.

### 4. Delete

```bash
worktree-manager delete --with-branch <slug>
```

What this handles for you:

- Refuses to delete the main worktree.
- Checks for uncommitted and unpushed work. If either is present, the CLI errors out — surface the message and ask the user whether to retry with `--force` (which also bypasses the unpushed check). Only add `--force` on explicit confirmation.
- Runs `pre_delete` / `post_delete` hooks declared in `.worktree-manager.yml`.
- Removes the worktree, deletes the local branch (because of `--with-branch`), and removes the task metadata.

If `--with-branch` fails because the branch is "unmerged" (common after a rebase-merge upstream — the local SHA no longer matches), warn the user and ask before retrying with `--force-branch` (the `-D` equivalent).

If the branch is already gone (e.g. `/merge-pr` already ran `gh pr merge --delete-branch`), the CLI will report it — treat that as success.

### 5. Report

```
Removed worktree: <path>
Deleted branch:   <branch>
```

---

## Fallback (no `worktree-manager` binary, or task not in the CLI's store)

If the CLI is missing — or `worktree-manager list` doesn't know about the target (it was created with raw `git worktree add`) — do the cleanup by hand. Call out in your report that you used the fallback so the user knows hooks weren't run.

1. **Resolve the target.**
   - If the user gave a slug: worktree path is `.worktrees/<repo>-<slug>`, branch is `<user>/<slug>` (or just `<slug>` if no user prefix is configured).
   - If they gave a path: read its branch with `git -C <path> branch --show-current`.
   - If nothing: use `git worktree list` and `git branch --show-current` from the current location. Confirm that the current worktree is not the main repo worktree — refuse to delete the main one.

2. **Check for uncommitted or unpushed work.**
   ```bash
   git -C <path> status --porcelain
   git -C <path> log @{u}.. 2>/dev/null
   ```
   If either is non-empty, stop and surface what's there. The user must commit/push/stash or explicitly say "delete anyway" before proceeding.

3. **Confirm** (same prompt as the preferred path).

4. **Step out if needed.** If the current shell is inside the target worktree, `cd` to the main repo toplevel first:
   ```bash
   cd $(git -C <path>/.. rev-parse --show-toplevel 2>/dev/null || dirname <path>)
   ```

5. **Remove the worktree.**
   ```bash
   git worktree remove <path>
   ```
   If this fails because of leftover state, surface the error. Only fall back to `git worktree remove --force <path>` on explicit user confirmation.

6. **Delete the local branch.**
   ```bash
   git branch -d <branch>
   ```
   If `-d` rejects an "unmerged" branch, warn the user and ask before falling back to `-D`.

   Note: if the user already ran `/merge-pr`, the local branch is usually already gone — `gh pr merge --delete-branch` deletes it when the checkout was on the PR branch with no unpushed work. In that case `git branch -d` will return `branch '<branch>' not found`; treat that as success and move on.

7. **Report** (same format as the preferred path).

---

## Guidelines

- Never delete the main worktree or the currently-checked-out branch of the main repo.
- Never `--force` (worktree) or `--force-branch` / `-D` (branch) without explicit confirmation.
- Don't touch the remote branch — `/merge-pr` already handled that with `--delete-branch`.
- Don't touch linked Linear/GitHub issues — out of scope here.
- Plain text only.
