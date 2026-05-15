---
name: create-worktree
description: Initialize an isolated git worktree, branch, and `.agentic/<slug>/` workspace for an agentic coding task. Use at the start of a new task, before /prep.
---

Set up an isolated workspace for a coding task: a git worktree, a branch, and a `.agentic/<slug>/` directory the rest of the coding-loop skills write into.

## Input

The user usually provides a task descriptor — either a free-form description ("add semantic indexing"), a Linear identifier ("AGE-4"), or a GitHub issue ("gh #42"). Linear is the default when nothing prefixes the identifier; "gh"/"github" forces GitHub.

The user may also override the slug with phrasing like "use slug AGE-4-custom-name".

## Process

1. **Determine the slug.**
   - If the user gave an explicit slug, use it.
   - If a Linear/GitHub identifier was provided: fetch the issue title and build a kebab-case slug like `AGE-4-add-semantic-indexing` (issue number + 3-5 word summary). For Linear, also move the issue to "In Progress".
   - If only a free-form description: build a kebab-case slug from the description; no ticket coupling.

2. **Pick the worktree path.** Use `.worktrees/<repo>-<slug>/` where `<repo>` is `basename $(git rev-parse --show-toplevel)`. Example: `.worktrees/myapp-AGE-4-add-semantic-indexing`.

3. **Create the worktree and branch.**
   ```bash
   mkdir -p .worktrees
   git worktree add -b <user>/<slug> .worktrees/<repo>-<slug>
   ```
   `<user>` defaults to the local git user; if unset, omit the prefix. If the branch already exists, ask the user how to proceed (use existing, pick a new slug, abort).

4. **Run worktree init if available.** From inside the new worktree:
   ```bash
   just --list 2>/dev/null | rg '(init-worktree|setup-worktree|worktree-init)' && just init-worktree
   ```
   Non-blocking. If no such target exists, mention it as a suggestion for next time.

5. **Create the task workspace.** Inside the worktree:
   ```bash
   mkdir -p .agentic/<slug>
   ```

6. **Record ticket metadata** (only if a Linear/GitHub ID was involved). Write `.agentic/<slug>/ticket.json` so downstream skills can read issue context without re-fetching:
   ```json
   {
     "source": "linear" | "github",
     "identifier": "AGE-4",
     "title": "...",
     "description": "...",
     "url": "...",
     "fetchedAt": "<ISO-8601>"
   }
   ```
   For Linear add `team`, `priority`, `assignee` when available. For GitHub add `number`, `author`, `milestone`.

7. **Report.** Tell the user the slug, branch, worktree path, and next step:
   ```
   Worktree: .worktrees/myapp-AGE-4-add-semantic-indexing
   Branch:   me/AGE-4-add-semantic-indexing
   Workspace: .agentic/AGE-4-add-semantic-indexing/

   cd .worktrees/myapp-AGE-4-add-semantic-indexing
   Then run /prep to scope the task.
   ```

## Guidelines

- Default to Linear when only an identifier is given; only treat as GitHub when "gh"/"github" is explicit.
- Confirm the slug if it's at all ambiguous — slugs are visible in the branch name and on disk for the life of the task.
- Never force-overwrite an existing worktree or branch without explicit confirmation.
- Keep slugs lowercase kebab-case, 3-5 descriptive words after any issue prefix.
