---
name: create-worktree
description: Initialize an isolated git worktree, branch, and `.agentic/<slug>/` workspace for an agentic coding task. Use at the start of a new task, before /prep.
---

Set up an isolated workspace for a coding task: a git worktree, a branch, and a `.agentic/<slug>/` directory the rest of the coding-loop skills write into.

## Input

The user usually provides a task descriptor — either a free-form description ("add semantic indexing"), a Linear identifier ("AGE-4"), or a GitHub issue ("gh #42"). Linear is the default when nothing prefixes the identifier; "gh"/"github" forces GitHub.

The user may also override the slug with phrasing like "use slug AGE-4-custom-name".

---

## Preflight: is `worktree-manager` installed?

Assume the CLI is installed and call it directly. Only check if a call fails with "command not found":

```bash
command -v worktree-manager >/dev/null
```

If the binary is missing:

1. Tell the user `worktree-manager` isn't installed and point them at the install instructions in the upstream README: <https://github.com/mattjmcnaughton/worktree-manager#installation>.
2. Then fall back to the raw `git worktree` commands documented in the **Fallback** section so the immediate task isn't blocked. Be explicit when you do this — the CLI handles user-prefix resolution, hooks, and task metadata for you; the fallback skips all of that.

---

## Process

### 1. Determine the slug

This step is the same on both paths — `worktree-manager` does not know how to fetch Linear or GitHub issue titles, so the skill owns slug derivation.

- If the user gave an explicit slug, use it.
- If a Linear/GitHub identifier was provided: fetch the issue title and build a kebab-case slug like `AGE-4-add-semantic-indexing` (issue number + 3-5 word summary). For Linear, also move the issue to "In Progress".
- If only a free-form description: build a kebab-case slug from the description; no ticket coupling.

### 2. Create the worktree (preferred: `worktree-manager`)

From the main repo root:

```bash
worktree-manager create --slug <slug> --agentic
```

What this handles for you:

- Resolves the user prefix and branches as `<user>/<slug>` (template: `{{ user }}/{{ slug }}`).
- Picks the worktree path from the repo config or default template `{{ repo }}-{{ slug }}` under `.worktrees/`.
- Creates `.agentic/<slug>/` because of `--agentic`.
- Runs any `pre_create` / `post_create` hooks declared in `.worktree-manager.yml` (e.g. copying `.env`, running `just init-worktree`).
- Records task metadata under `${XDG_STATE_HOME:-~/.local/state}/worktree-manager/repos/<sha8>/tasks/<slug>.json`.

Other flags worth knowing:

- `--base <branch>` — fork from a base other than the repo default.
- `--no-agentic` — skip workspace creation (rarely useful for this skill; `/prep` expects `.agentic/<slug>/` to exist).

If the command fails because the branch or worktree already exists, surface the error and ask the user how to proceed (use the existing setup, pick a new slug, abort). Do not force-overwrite.

### 3. Record ticket metadata

Only if a Linear/GitHub ID was involved. Write `.agentic/<slug>/ticket.json` inside the new worktree so downstream skills can read issue context without re-fetching:

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

### 4. Report

Tell the user the slug, branch, worktree path, and next step. `worktree-manager create` already prints these — quote them back in your report:

```
Worktree: .worktrees/myapp-AGE-4-add-semantic-indexing
Branch:   me/AGE-4-add-semantic-indexing
Workspace: .agentic/AGE-4-add-semantic-indexing/

cd .worktrees/myapp-AGE-4-add-semantic-indexing
Then run /prep to scope the task.
```

---

## Fallback (no `worktree-manager` binary)

If the CLI is missing, do the work by hand. Call out in your report that you used the fallback so the user knows hooks and task metadata weren't applied.

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
   If the branch already exists, ask the user how to proceed.

4. **Run worktree init if available.** From inside the new worktree:
   ```bash
   just --list 2>/dev/null | rg '(init-worktree|setup-worktree|worktree-init)' && just init-worktree
   ```
   Non-blocking. If no such target exists, mention it as a suggestion for next time.

5. **Create the task workspace.**
   ```bash
   mkdir -p .agentic/<slug>
   ```

Then continue from step 3 of the main process (ticket metadata) and step 4 (report).

---

## Guidelines

- Default to Linear when only an identifier is given; only treat as GitHub when "gh"/"github" is explicit.
- Confirm the slug if it's at all ambiguous — slugs are visible in the branch name and on disk for the life of the task.
- Never force-overwrite an existing worktree or branch without explicit confirmation.
- Keep slugs lowercase kebab-case, 3-5 descriptive words after any issue prefix.
- Don't `cd` into the new worktree from the persistent Bash shell — back-to-back invocations will nest. Hand the `cd` instruction back to the user in the report.
