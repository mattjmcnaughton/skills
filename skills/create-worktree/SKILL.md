---
name: create-worktree
description: Initialize an isolated git worktree, branch, and `.agentic/<slug>/` workspace for an agentic coding task. Use at the start of a new task, before /prep.
---

Set up an isolated workspace for a coding task: a git worktree, a branch, and a `.agentic/<slug>/` directory the rest of the coding-loop skills write into.

## Input

The user usually provides a task descriptor — a free-form description ("add semantic indexing"), or an identifier or URL from GitHub, Linear, Jira, or another tracker. Resolve the tracker from an explicit source, URL, or repository guidance; identifiers like `AGE-4` do not uniquely identify a tracker. Ask if the source is ambiguous before fetching.

The user may also override the slug with phrasing like "use slug AGE-4-custom-name".

---

## Process

### 1. Determine the slug

- If the user gave an explicit slug, use it.
- If a ticket was provided: use its supplied title or fetch it through an available tracker integration, then build a kebab-case slug like `age-4-add-semantic-indexing` (identifier + 3-5 word summary). If fetching is unavailable, accept pasted context or ask for a short task description; do not require installing an integration. Do not change remote ticket status unless explicitly authorized.
- If only a free-form description: build a kebab-case slug from the description; no ticket coupling.

### 2. Create the worktree and branch

**Before creating either directory, ensure local ignores.** Run these checks from the current worktree's repository root:

- Check `git ls-files -- .agentic .worktrees`. If any paths are tracked, stop and explain that this repository already tracks workflow files; ask how to proceed. Do not untrack files or hide this conflict with ignore rules.
- Check each directory with `git check-ignore -q -- .agentic/` and `git check-ignore -q -- .worktrees/`. Exit 0 means ignored; exit 1 means a rule is needed; other failures must be surfaced, not treated as missing rules.
- For missing rules, resolve the local exclude file with `git rev-parse --path-format=absolute --git-path info/exclude`. Do not assume `.git` is a directory. Preserve its contents and append only missing exact lines `/.agentic/` and `/.worktrees/`, ensuring a newline separates them from existing content. Create the parent directory/file if needed. Never edit `.gitignore`, global Git configuration, or the index for this setup.
- Recheck both directories. If a higher-priority rule prevents exclusion, stop and explain the conflict rather than modifying project ignore policy. Report any local exclude changes; they are shared by linked worktrees in this local repository, not published to other clones.

1. **Pick the worktree path.** Use `.worktrees/<repo>-<slug>/` where `<repo>` is `basename $(git rev-parse --show-toplevel)`.

2. **Resolve the user prefix.** Use `$USER` (always set on Unix) with `id -F` as a macOS fallback. Do NOT chain through `git config user.email` with `&&` — it short-circuits when empty and forces retries:
   ```bash
   USER_PREFIX="${USER:-$(id -F 2>/dev/null || id -un)}"
   ```
   If `USER_PREFIX` is somehow empty, omit the prefix entirely (branch is just `<slug>`).

3. **Create the worktree and branch.**
   ```bash
   mkdir -p .worktrees
   git worktree add -b "${USER_PREFIX:+$USER_PREFIX/}<slug>" .worktrees/<repo>-<slug>
   ```
   If the branch or worktree already exists, surface the error and ask the user how to proceed (use the existing setup, pick a new slug, abort). Do not force-overwrite.

4. **Run worktree init if available.** From inside the new worktree:
   ```bash
   just --list 2>/dev/null | rg '(init-worktree|setup-worktree|worktree-init)' && just init-worktree
   ```
   Non-blocking. If no such target exists, mention it as a suggestion for next time.

5. **Create the task workspace.** From the new worktree's root, repeat the tracked-path and effective-ignore checks above before writing task artifacts (its checkout or init step may have different rules). Stop on tracked paths or unresolved ignore conflicts; preserve the worktree already created and report the blocker.
   ```bash
   mkdir -p .agentic/<slug>
   ```

### 3. Record ticket metadata

Ticket context is optional. With a free-form task and no ticket, skip this step; do not require an issue or create a placeholder. Preserve an existing `ticket.json` or `ticket.md`; both are supported by downstream skills, and Markdown needs no fixed schema or conversion. If both exist, surface material conflicts rather than silently choosing one.

When a ticket was supplied and no ticket file exists, record the supplied or fetched context inside `.agentic/<slug>/` in the new worktree so downstream skills need not re-fetch it. Default to `ticket.json` below, or use `ticket.md` if the user prefers Markdown. Include only known fields; `source` is an open-ended tracker name, not an enum. Omit `fetchedAt` when no fetch occurred. For example:

```json
{
  "source": "jira",
  "identifier": "AGE-4",
  "title": "...",
  "description": "...",
  "url": "...",
  "fetchedAt": "<ISO-8601>"
}
```

Preserve useful tracker-specific fields when available (for example project, team, priority, assignee, number, or milestone); downstream skills must not require them. Keep the original identifier and URL, regardless of tracker.

### 4. Report

Tell the user the slug, branch, worktree path, and next step:

```
Worktree: .worktrees/myapp-AGE-4-add-semantic-indexing
Branch:   me/AGE-4-add-semantic-indexing
Workspace: .agentic/AGE-4-add-semantic-indexing/

cd .worktrees/myapp-AGE-4-add-semantic-indexing
Then run /prep to scope the task.
```

---

## Guidelines

- Do not assume a tracker from an identifier's shape or require a particular tracker.
- Confirm the slug if it's at all ambiguous — slugs are visible in the branch name and on disk for the life of the task.
- Never force-overwrite an existing worktree or branch without explicit confirmation.
- Keep slugs lowercase kebab-case, 3-5 descriptive words after any issue prefix.
- Don't `cd` into the new worktree from the persistent Bash shell — back-to-back invocations will nest. Hand the `cd` instruction back to the user in the report.
