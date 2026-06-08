---
name: setup-permissions
description: Configure the current repo so an agent (Claude Code or Codex CLI) can run lint, fmt, test, and gate commands without permission prompts, while still being blocked from reading gitignored files or running unsafe commands. Writes `.claude/settings.json`, `.codex/config.toml`, `.codex/rules/default.rules`, and an AGENTS.md command-reference section. Use when bootstrapping a repo for autonomous agent work, when a teammate added a new task runner, or when the audit phase should report runner gaps. Triggers include "set up agent permissions", "make this repo agent-ready", "let the agent run tests without asking", "audit my runner for agent gaps".
---

`/setup-permissions` makes the current repository ready for autonomous agent work. It detects the task runner, derives a deny scope from `.gitignore`, and writes coherent permission artifacts for both Claude Code (`.claude/settings.json`, committed and shared with the team) and Codex CLI (`.codex/config.toml` plus `.codex/rules/default.rules`). It also updates `AGENTS.md` (and a sibling `CLAUDE.md`) with the canonical commands the agent should call, and audits the runner for missing targets.

The skill writes to the **committed** `.claude/settings.json`, not the gitignored `.claude/settings.local.json`. Rationale: the runner allowlist and secret-deny floor are project-shared concerns that should reach every contributor without re-running the skill, which matches how the Codex artifacts (`.codex/config.toml`, `.codex/rules/default.rules`) and `AGENTS.md` are already handled. A developer's personal overrides remain in `.claude/settings.local.json`, which the skill **reads** for conflict detection but never writes to.

The skill is **re-runnable**. The managed surface converges across runs: when the model changes (new runner targets land, the gitignore grows, the skill itself gains a new category like `allow_utils`), the managed regions are rewritten cleanly to reflect the new model — there is no manual "delete the old config and start fresh" step. Entries that live outside the managed surface — hand-authored team additions, or entries written by sibling skills like `/fewer-permission-prompts` — are **preserved** by default, not pruned. The skill is convergent on its managed floor, not byte-identical across arbitrary runs.

## Phases

The skill is split into four phases. Each one is independently invocable:

- `/setup-permissions detect` — identify the task runner(s), enumerate runner targets, classify the `.gitignore` into deny globs. Prints a summary; writes nothing.
- `/setup-permissions permissions` — render and write `.claude/settings.json`, `.codex/config.toml`, `.codex/rules/default.rules`.
- `/setup-permissions docs` — render and write the managed command-reference section into `AGENTS.md` (and `CLAUDE.md`).
- `/setup-permissions audit` — check the detected runner for missing canonical targets (`lint`, `fmt`, `test`, `test-one`, `lint-fix`, `gate`) and print a plain-text gap report.

With no arguments, `/setup-permissions` runs the default progression: **detect → permissions → docs → audit**, pausing after each phase to show the proposed diff and ask for confirmation. Users can decline an individual phase and continue; the next phase will see whatever state is on disk. After the permissions phase writes, the skill optionally augments the Claude allowlist by invoking `/fewer-permission-prompts` as a transcript-driven data source — see "Augmenting with observed prompts" under Phase 2.

## Phase 1: Detect

The detect phase reads the repository and builds an in-memory **DetectionResult**:

```
DetectionResult {
  runners: [Runner],           # may be empty; may be multiple
  primary_runner: Runner?,     # one of the above, picked per the rules below
  runner_targets: {Runner: [Target]},
  gitignore_entries: [str],    # raw lines, unfiltered
  existing_artifacts: {        # what's already on disk
    claude_settings_shared: Path?,   # .claude/settings.json — committed, the write target
    claude_settings_local: Path?,    # .claude/settings.local.json — read-only for conflict detection
    codex_config: Path?,
    codex_rules: Path?,
    agents_md: Path?,
    claude_md: Path?,
  },
}
```

### Runner detection

Look for these signals in repo root (do not recurse — only top-level). When multiple match, all are recorded; the **primary** is chosen by the precedence below.

| Signal file(s) | Runner |
|---|---|
| `justfile` (any case) | just |
| `package.json` + `pnpm-lock.yaml` | pnpm |
| `package.json` + `yarn.lock` | yarn |
| `package.json` + `package-lock.json` or `npm-shrinkwrap.json` | npm |
| `Makefile`, `GNUmakefile`, or `makefile` | make |
| `pyproject.toml` + `uv.lock` | uv |
| `pyproject.toml` + `poetry.lock` | poetry |
| `Cargo.toml` | cargo |
| `go.mod` | go |

**Primary precedence**: `just` > `make` > package-manager (pnpm > yarn > npm) > `uv`/`poetry` > `cargo` > `go`. The rationale: when a `justfile` wraps a deeper runner (very common), `just <target>` is the surface the agent should call. Falling back to the wrapped runner is fine but yields a noisier allowlist.

If **no runner** is detected, skip runner-related allowlist entries and continue with gitignore deny + read/search allow + git allowlist. Tell the user "no task runner detected — the agent can read and search, but no automated build/test commands will be allowlisted" so they know what to expect.

If the user explicitly wants a runner the skill doesn't recognise, ask: do not guess. Record their choice and the literal commands to allowlist, and continue.

### Target enumeration

For each detected runner, list its declared targets so we know which canonical intents are covered. Commands to dry-run (capture stdout, do not error on non-zero):

| Runner | Command | Parse rule |
|---|---|---|
| just | `just --list --unsorted` | recipe names, one per line after the header |
| pnpm | `jq -r '.scripts \| keys[]' package.json` | each key |
| yarn | `jq -r '.scripts \| keys[]' package.json` | each key |
| npm | `jq -r '.scripts \| keys[]' package.json` | each key |
| make | `make -np 2>/dev/null \| awk '/^# Make data base/,/^$/' \| grep -E '^[a-zA-Z0-9_.-]+:' \| cut -d: -f1 \| sort -u` | targets ending in `:` |
| uv | `jq -r '.tool.scripts \| keys[]?, .project.scripts \| keys[]?' pyproject.toml 2>/dev/null` (fall back to grep for `[tool.uv.scripts]` if no jq-toml) | script names |
| poetry | `grep -E '^\\[tool.poetry.scripts\\]' pyproject.toml`, list keys | script names |
| cargo | `cargo metadata --no-deps --format-version 1 \| jq -r '.packages[].targets[].name'` for binaries; for built-ins, hardcode `build`, `test`, `fmt`, `clippy`, `check` | name |
| go | hardcode `build`, `test`, `vet`, `fmt` (these are subcommands, not targets) | n/a |

Targets are matched to **canonical intents** by name. The intent table:

| Canonical intent | Matching target names (case-insensitive substring) |
|---|---|
| lint | `lint`, `check`, `clippy`, `vet`, `eslint`, `ruff` (without `fix`) |
| fmt | `fmt`, `format`, `prettier`, `rustfmt`, `gofmt` |
| test | `test`, `tests`, `spec` (no suffix indicating single-test) |
| test-one | `test-one`, `test:one`, `test-single`, anything accepting an argument pattern |
| lint-fix | `lint-fix`, `lint:fix`, `fix`, `ruff-fix`, `eslint-fix` |
| gate | `gate`, `ci`, `verify`, `check-all`, `pre-commit` |

A target that lacks a matching intent is still recorded; it just doesn't slot into a canonical intent and is reported in the audit as "uncategorised".

### Gitignore translation

Read `.gitignore` from the repo root only (do not recurse into nested `.gitignore` files in v1 — flag this as a known limitation in the printed summary). Translate each non-blank, non-comment line to a glob suitable for `.claude/settings.json` (Read deny) and `.codex/config.toml` (filesystem deny).

Rules:

| Gitignore form | Translation |
|---|---|
| `foo` (no slash) | `**/foo` plus `**/foo/**` (match anywhere) |
| `/foo` (leading slash) | `foo` plus `foo/**` (anchored to root) |
| `foo/` (trailing slash) | `**/foo/**` (directory only) |
| `foo/bar` (internal slash) | `foo/bar` plus `foo/bar/**` (anchored) |
| `**/foo` | pass through |
| `*.log`, `*.env` | pass through |
| `!foo` (negation) | **skip with a warning**: "negation pattern `!foo` in `.gitignore` was not translated; review denies manually" |
| blank lines, `#` comments | skip |

**Hardcoded carve-outs** (always skipped during translation, regardless of `.gitignore`):

- `.agentic`, `.agentic/` — the agentic-coding loop (`/create-worktree`, `/prep`, `/build`, `/review`, `/fetch-context`, etc.) reads and writes `.agentic/<slug>/plan.md`, `diary.md`, `review.md`, and `.agentic/sources/`. Denying reads here would break every downstream skill.
- `.worktrees`, `.worktrees/` — `/create-worktree` provisions isolated workspaces under this directory; subsequent skills run inside those worktrees and must be able to read them.
- `.env.example`, `.env.sample`, `.env.template` — these are committed documentation files, not secrets. They exist to show contributors which variables to populate in a real `.env`.

Print a one-line notice when a carve-out fires so the user knows the entry was intentionally not translated.

The translation is intentionally a 90% solution. The audit phase reminds the user to review the produced deny list before accepting.

### Detect output

At the end of the detect phase, print:

```
Detected runners: just (primary), pnpm
Targets covered: lint=just lint, fmt=just fmt, test=just test, gate=just gate
Targets missing: test-one, lint-fix
Gitignore entries translated: 7 (0 skipped due to negations)
Existing artifacts: .claude/settings.json (will merge), .claude/settings.local.json (read-only, will scan for conflicts), .codex/ (absent, will create)
```

If invoked as the standalone `detect` phase, stop here. If running the default progression, pause for confirmation and continue to `permissions`.

## Phase 2: Permissions

The permissions phase computes a single in-memory **PermissionModel** from the DetectionResult, then renders it to three artifacts (Claude in this section; Codex in the next).

### Permission model

```
PermissionModel {
  deny_globs:    [str],   # from .gitignore translation; "files the agent must not read"
  allow_reads:   [str],   # broad read/search across the tree (subtractive: dies on deny_globs)
  allow_runner:  [str],   # canonical runner commands the agent may run unprompted
  allow_fs:      [str],   # safe filesystem-mutating commands within the workspace (e.g., mkdir)
  allow_diag:    [str],   # diagnostic stdout-only commands (e.g., echo "$EXIT:$?")
  allow_utils:   [str],   # read-mostly shell text utilities (cat, head, tail, sed, awk, ...)
  allow_git_ro:  [str],   # read-only git subcommands
  allow_git_rw:  [str],   # write-side git the agent may run unprompted (add, commit, worktree add)
}

The `deny` surface is reserved for **sensitive file reads** — secrets, env files, credentials, and gitignored paths. Git operations are never denied. Destructive commands (`push`, `reset`, `clean`, `rebase`, `cherry-pick`, `checkout`, `restore`, `branch -D`) are simply absent from the allow list, which means the agent will be prompted before running them. This is a deliberate trust posture: hard-block data exfiltration, soft-gate destructive actions via the prompt mechanism.
```

Fixed contents (independent of detection):

- `allow_reads`: `Read`, `Glob`, `Grep` on the entire tree. The deny globs do the narrowing.
- `allow_fs`: `mkdir` (any arguments). The agentic-coding loop creates workspace directories like `.agentic/<slug>/` and `.agentic/sources/<repo>/` without needing a prompt each time. The deny floor still applies to the file contents, and Codex's filesystem-write sandbox confines `mkdir` to the workspace; `Bash(mkdir:*)` in Claude is similarly scoped because the agent only operates inside the working tree.
- `allow_diag`: `echo "$EXIT:$?"` (exact form). The post-command exit-code probe used by hook scripts and quick status checks. Read-only, no side effects beyond stdout.
- `allow_utils`: read-mostly shell text utilities the agent uses in ad-hoc piping and exploration: `cat`, `head`, `tail`, `sed`, `awk`, `wc`, `sort`, `uniq`, `cut`, `tr`, `find`, `rg`, `fd`, plus the compound `xargs cat` (fan-out reads from a file list). Each is allowlisted as `<entry>:*` so arguments pass through. The compound `xargs cat` is allowlisted narrowly rather than bare `xargs` because `xargs` runs an arbitrary subcommand — `xargs rm` and `xargs sh -c ...` should still prompt. Sensitive-file reads are still blocked by the deny floor. Mutating variants (`sed -i`, `find -delete`, `find -exec`) are not separately gated here because the agent already has unrestricted workspace-edit access through the `Edit` and `Write` tools — closing this gap would not raise the security posture, only the prompt rate.
- `allow_git_ro`: `status`, `diff`, `log`, `show`, `blame`, `ls-files`, `check-ignore`, `branch` (no `-d`/`-D`), `rev-parse`, `remote -v`, `worktree list`, `for-each-ref`, `config --get`.
- `allow_git_rw`: `add`, `commit`, `worktree add`.

Variable contents (depend on detection):

- `deny_globs`: the translated `.gitignore` list, deduplicated and sorted. Plus a hardcoded floor regardless of `.gitignore`:
  - `**/.env`
  - `**/.env.local`, `**/.env.*.local`
  - `**/.env.production`, `**/.env.development`, `**/.env.staging`, `**/.env.test`
  - `**/*.pem`, `**/*.key`
  - `**/secrets/**`
  - `**/credentials.json`

  The floor is intentionally **enumerated** rather than using a broad `**/.env.*` glob, because the broad form would also match `.env.example`, `.env.sample`, and `.env.template` — committed documentation files the agent legitimately needs to read. The translation-step carve-outs (`.agentic`, `.worktrees`, `.env.example` and friends) also apply here: even a future floor entry must not deny those paths.
- `allow_runner`: the union of the primary runner's *canonical-intent targets* (lint, fmt, test, test-one, lint-fix, gate) plus any explicit extra targets the user named. Targets that didn't match a canonical intent are **not** allowlisted by default — the agent should ask before running them. Each entry is the full command string (e.g., `just lint`, `pnpm run test`).
- **Runner discovery**: when the primary runner is `just`, additionally allowlist `just --list` (and the `--unsorted` variant used by the detect phase) and `just --summary`. The agent re-runs this skill and other workflows that need to enumerate available recipes; gating discovery behind a prompt every time is friction with no security benefit, since these flags only read the `justfile`. No analogous entry is added for other runners — `make`, `pnpm`, `cargo`, etc. discover targets via tools (`jq`, `make -np`, `cargo metadata`) that are already covered by other allowlist categories.

### Claude renderer

Render to `.claude/settings.json` (the committed, team-shared file) using this matcher syntax (already in the cheatsheet in `plan.md`):

| Model field | Claude matcher form |
|---|---|
| `allow_reads` (broad) | `"Read"`, `"Glob"`, `"Grep"` (entire-tool allow) |
| `deny_globs` (file glob) | `"Read(./<glob>)"` in `permissions.deny` |
| `allow_runner` (exact command) | `"Bash(<command>)"` in `permissions.allow` |
| `allow_runner` (prefix) | `"Bash(<runner> *)"` only when the user opts in (off by default — too broad) |
| `allow_fs` | `"Bash(mkdir)"` and `"Bash(mkdir:*)"` in `permissions.allow` |
| `allow_diag` | `"Bash(echo \"$EXIT:$?\")"` in `permissions.allow` |
| `allow_utils` | one `"Bash(<entry>:*)"` entry per utility in `permissions.allow`; multi-token entries like `xargs cat` render as `"Bash(xargs cat:*)"` |
| `allow_git_ro` | one entry per subcommand: `"Bash(git status)"`, `"Bash(git status:*)"`, etc. The `:*` suffix lets arguments through. |
| `allow_git_rw` | `"Bash(git add:*)"`, `"Bash(git commit:*)"`, `"Bash(git worktree add:*)"` |

Destructive git subcommands are intentionally omitted from both `allow` and `deny`. When the agent tries `git push`, Claude prompts the user; the user can approve case-by-case. The deny list is reserved for sensitive file reads.

### Worked example (this repo)

Given `.gitignore`:
```
.agentic
.worktrees
```

and a detected `just` runner with targets `lint`, `fmt`, `test`, `gate`, the renderer produces (showing only the managed regions; existing entries are preserved). Note that `.agentic` and `.worktrees` from `.gitignore` are **not** translated into denies — the carve-outs keep the agentic-coding workspace and worktree provisioning readable. The `.env` floor likewise enumerates dangerous variants without sweeping in `.env.example` / `.env.sample`:

```json
{
  "permissions": {
    "allow": [
      "Bash(awk:*)",
      "Bash(cat:*)",
      "Bash(cut:*)",
      "Bash(echo \"$EXIT:$?\")",
      "Bash(fd:*)",
      "Bash(find:*)",
      "Bash(git add:*)",
      "Bash(git blame:*)",
      "Bash(git branch)",
      "Bash(git check-ignore:*)",
      "Bash(git commit:*)",
      "Bash(git config --get:*)",
      "Bash(git diff:*)",
      "Bash(git for-each-ref:*)",
      "Bash(git log:*)",
      "Bash(git ls-files:*)",
      "Bash(git remote -v)",
      "Bash(git rev-parse:*)",
      "Bash(git show:*)",
      "Bash(git status)",
      "Bash(git status:*)",
      "Bash(git worktree add:*)",
      "Bash(git worktree list)",
      "Bash(head:*)",
      "Bash(just --list)",
      "Bash(just --list --unsorted)",
      "Bash(just --summary)",
      "Bash(just fmt)",
      "Bash(just gate)",
      "Bash(just lint)",
      "Bash(just test)",
      "Bash(mkdir)",
      "Bash(mkdir:*)",
      "Bash(rg:*)",
      "Bash(sed:*)",
      "Bash(sort:*)",
      "Bash(tail:*)",
      "Bash(tr:*)",
      "Bash(uniq:*)",
      "Bash(wc:*)",
      "Bash(xargs cat:*)",
      "Glob",
      "Grep",
      "Read"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*.local)",
      "Read(./.env.development)",
      "Read(./.env.local)",
      "Read(./.env.production)",
      "Read(./.env.staging)",
      "Read(./.env.test)",
      "Read(./credentials.json)",
      "Read(./secrets/**)",
      "Read(./**/*.key)",
      "Read(./**/*.pem)"
    ]
  }
}
```

Arrays are sorted alphabetically; duplicates removed.

### Codex renderer

Codex splits permissions across two files under `.codex/`:

1. **`.codex/config.toml`** — declarative profile carrying the filesystem deny scope.
2. **`.codex/rules/default.rules`** — Starlark `prefix_rule(...)` entries gating commands.

Both are required: `config.toml` alone does not block command execution.

#### `.codex/config.toml`

The renderer manages exactly three top-level surfaces and leaves everything else (e.g., `[features]`, `[mcp_servers.*]`, `[projects."<path>"]`) untouched:

- `default_permissions = "agent-default"`
- `approval_policy = { granular = { sandbox_approval = true, rules = true, request_permissions = true, mcp_elicitations = true, skill_approval = true } }`
- the named profile `[permissions.agent-default]`

The profile body:

```toml
[permissions.agent-default]
extends = ":workspace"

# Globs are scoped under `:workspace_roots` so they resolve relative to each
# effective workspace root rather than as absolute paths. Per the Codex
# reference, this is the special token that takes a nested subpath/glob table.
[permissions.agent-default.filesystem.":workspace_roots"]
# Generated from .gitignore; do not edit by hand.
# Note: `.agentic/**` and `.worktrees/**` are intentionally NOT denied — the
# agentic-coding loop reads and writes those locations. `.env.example`,
# `.env.sample`, and `.env.template` are intentionally readable; the floor
# enumerates the dangerous variants rather than using a broad `**/.env.*`.
"**/.env" = "deny"
"**/.env.local" = "deny"
"**/.env.*.local" = "deny"
"**/.env.production" = "deny"
"**/.env.development" = "deny"
"**/.env.staging" = "deny"
"**/.env.test" = "deny"
"**/*.key" = "deny"
"**/*.pem" = "deny"
"**/credentials.json" = "deny"
"**/secrets/**" = "deny"
```

Notes:

- `extends = ":workspace"` inherits the built-in workspace profile (read-everywhere, write-in-cwd) and layers the deny entries on top. **Do not set `sandbox_mode`** anywhere in the file; per the Codex reference, combining `sandbox_mode` with `default_permissions` or `[permissions.<name>]` is invalid.
- The deny floor is the same set as in the Claude renderer, so both clients enforce equivalent filesystem scope.
- Keys are quoted strings so the gitignore-translated globs round-trip safely (TOML bare keys would choke on `*`, `.`, `/`).

#### `.codex/rules/default.rules`

Codex auto-loads every `*.rules` file from the config layer's `rules/` directory (confirmed in `codex-rs/core/src/exec_policy.rs`, fetched during /prep). Conventional filename: `default.rules`. The renderer emits one file with a top-of-file managed marker:

```starlark
# managed:setup-permissions
# Generated by /setup-permissions. Edit only the regions outside this header
# block; the rest is regenerated on each skill run.

# --- runner -------------------------------------------------------------
prefix_rule(
    pattern = ["just", ["lint", "fmt", "test", "gate"]],
    decision = "allow",
    justification = "Local dev runner; safe to invoke unprompted.",
)
prefix_rule(
    pattern = ["just", ["--list", "--summary"]],
    decision = "allow",
    justification = "Recipe discovery; read-only inspection of the justfile.",
)

# --- filesystem: safe mutations within the workspace -------------------
prefix_rule(
    pattern = ["mkdir"],
    decision = "allow",
    justification = "Workspace directory creation (e.g., .agentic/<slug>/). Codex's write sandbox confines this to the workspace.",
)

# --- diagnostic: stdout-only probes ------------------------------------
prefix_rule(
    pattern = ["echo", "$EXIT:$?"],
    decision = "allow",
    justification = "Post-command exit-code probe used by hook scripts.",
)

# --- shell utilities: read-mostly text processing ----------------------
prefix_rule(
    pattern = [["cat", "head", "tail", "sed", "awk", "wc",
                "sort", "uniq", "cut", "tr", "find", "rg", "fd"]],
    decision = "allow",
    justification = "Read-mostly text utilities for ad-hoc exploration. Mutating variants (sed -i, find -delete) are not separately gated; the agent already has unrestricted workspace-edit access via Edit/Write tools.",
)
prefix_rule(
    pattern = ["xargs", "cat"],
    decision = "allow",
    justification = "Fan-out reads over a file list. Bare `xargs` is intentionally not allowlisted because it runs an arbitrary subcommand (xargs rm, xargs sh -c ...).",
)

# --- git: read-only -----------------------------------------------------
prefix_rule(
    pattern = ["git", ["status", "diff", "log", "show", "blame", "ls-files",
                       "check-ignore", "branch", "rev-parse", "remote",
                       "worktree", "for-each-ref", "config"]],
    decision = "allow",
    justification = "Read-only git inspection.",
)

# --- git: allowed write side -------------------------------------------
prefix_rule(
    pattern = ["git", ["add", "commit"]],
    decision = "allow",
    justification = "Local-only writes; do not touch the remote.",
)
prefix_rule(
    pattern = ["git", "worktree", "add"],
    decision = "allow",
    justification = "Worktree setup for agentic coding loop.",
)
```

Destructive git subcommands (`push`, `reset`, `clean`, `rebase`, `cherry-pick`, `checkout`, `restore`) are intentionally not listed. The skill takes a permissive posture: `forbidden` is reserved for nothing, `deny` (in the config.toml filesystem table) is reserved for sensitive file reads. Destructive git falls through to Codex's broader approval policy — the `request_permissions = true` setting in the config ensures the user is asked before anything risky proceeds.

Notes:

- `pattern = ["git", ["a", "b", ...]]` matches `git a ...` or `git b ...`; inner-list alternation is token-level.
- Default decision is `allow`, so omitting a rule does not forbid the command. Combined with `approval_policy.granular.request_permissions = true`, unlisted commands route through the user-approval flow rather than running silently.
- Inner-list alternatives like `worktree, for-each-ref, config` allow common read-only subcommands plus the broader write-side. Sub-subcommand precision (e.g., distinguishing `git remote -v` from `git remote add`) is not expressible in `prefix_rule`; Codex will allow the whole `git remote` prefix here. The audit phase calls this out so the user can downgrade specific commands if needed.

#### Merge rules

**`.codex/config.toml`**:

1. If the file does not exist, create it with only the three managed surfaces.
2. If it exists, parse with `tomli` (Python stdlib `tomllib` on 3.11+). On parse failure: refuse to overwrite; print the file path + the error.
3. Strip out any pre-existing `default_permissions`, `approval_policy`, and `[permissions.agent-default]` (including its nested tables). Leave all other tables and top-level keys untouched.
4. Append the freshly-rendered managed surfaces, preserving original formatting/comments for non-managed sections to the extent the TOML library allows. (When using `tomllib`+`tomli_w` round-tripping loses comments — flag this in the diff preview so users with hand-formatted configs know what to expect; future versions can switch to a comment-preserving library like `tomlkit`.)
5. Write with sorted keys inside the `[permissions.agent-default.filesystem]` table only; preserve insertion order elsewhere.

**`.codex/rules/default.rules`**:

1. If the file does not exist, create it with the full managed content.
2. If it exists **and** starts with the `# managed:setup-permissions` marker, regenerate the entire file. (Users with custom rules should put them in a sibling file, e.g., `.codex/rules/team.rules` — Codex loads every `*.rules` in the directory.)
3. If it exists **without** the marker, refuse to overwrite. Print the path, the first three lines of the existing file, and instruct the user: "this file has hand-authored content; move your rules into `.codex/rules/team.rules` and rerun, or pass `--force` to overwrite". The `--force` flag is an opt-in escape hatch for the case where the user knows what they're doing.

#### Restart note

Codex loads `.rules` files at startup. After running `/setup-permissions`, the user must restart Codex for new rules to take effect. The skill prints a reminder at the end of the run.

### Claude merge rules

There are two files to consider:

- `.claude/settings.json` — **the write target**, committed and team-shared. Contains only the managed entries derived from the PermissionModel. Re-runs produce a byte-identical file.
- `.claude/settings.local.json` — **read-only for this skill**, gitignored, per-developer. The skill scans it for conflicts but never writes to it. Personal allowlist additions live here by convention.

#### Writing `.claude/settings.json`

Algorithm:

1. Read the existing JSON if it exists. If parse fails, refuse to overwrite — show the file path and the parse error, ask the user to fix it manually.
2. Compute the desired `allow`/`deny` arrays from the PermissionModel as **managed entries**.
3. Compute the union of (managed entries) ∪ (existing entries not in the managed set). Non-managed entries are **preserved by default** — they may be hand-authored team additions, or written by a sibling skill like `/fewer-permission-prompts`. Surface them in the diff preview so the user can see what's being kept, but don't prune. The one exception: if a non-managed allow conflicts with the managed deny floor (e.g., `Read(./.env)` against the secret-deny set), flag it loudly so the user can decide — the audit phase also covers this case.
4. Write with stable 2-space indentation, arrays sorted, trailing newline.

The managed surface is deterministic; a re-run against a file that contains only managed entries produces zero diff. With augmentations from sibling skills or hand-authored allows present, the managed surface still converges but the file as a whole will differ — that's expected, not a bug.

#### Scanning `.claude/settings.local.json`

The skill reads the local file (if present) only to detect entries that contradict the managed deny set — e.g., a personal `Read(./.env)` allow that would override the managed sensitive-file deny. These appear in the audit phase under "Deny-floor overlap" with the file path so the developer can resolve it. The skill never modifies this file.

### Augmenting with observed prompts

After the baseline artifacts are written, optionally invoke `/fewer-permission-prompts` to fold in commands the user has been prompted on repeatedly. That sibling skill scans the session transcripts and appends frequently-seen read-only Bash and MCP calls directly to `.claude/settings.json`.

Treat this as opt-in, not automatic. Ask the user after the permissions diff has been shown and accepted: "Also scan recent transcripts and append frequently-prompted commands? (runs `/fewer-permission-prompts`)". Skip it if the user has signaled they want a minimal, hand-curated allowlist; use it when the goal is to reduce friction across an active project. Exercise judgment about timing and framing — the principle is "offer this as a data source", not a rigid step in the progression.

Two notes on scope:

- `/fewer-permission-prompts` only writes to `.claude/settings.json`. The Codex artifacts (`.codex/config.toml`, `.codex/rules/default.rules`) are not touched by this augmentation. If the team also runs Codex against this repo and wants symmetric coverage, the appropriate fix is a follow-up `/setup-permissions` run after the runner's surface stabilises, or a hand-edit to `.codex/rules/team.rules`.
- Entries `/fewer-permission-prompts` adds are preserved across subsequent `/setup-permissions` runs by the merge logic above — they look like "non-managed entries" and are kept by default.

## Phase 3: Docs

The docs phase writes a managed command-reference section into `AGENTS.md` so any agent (Claude Code, Codex, others) reading the repo sees the canonical commands without re-discovering them. `CLAUDE.md` is kept in sync via symlink when possible, or by writing the same managed block when both files exist as real files.

### Managed section format

The section is bracketed by stable markers so re-runs locate and rewrite it without touching surrounding content:

```markdown
<!-- managed:setup-permissions -->
## Commands

Use these commands as the canonical entry points. The agent is preauthorised to run them; ad-hoc shell invocations may require a prompt.

| Intent  | Command         | Notes                              |
|---------|-----------------|------------------------------------|
| lint    | `just lint`     | static checks; non-mutating        |
| fmt     | `just fmt`      | format-only; no logic changes      |
| test    | `just test`     | full suite                         |
| test-one| `just test-one <pattern>` | single-test variant      |
| lint-fix| `just lint-fix` | auto-applies safe fixes            |
| gate    | `just gate`     | full pre-commit gate (lint + test) |

Filesystem scope: agent reads/writes the working tree, including `.agentic/` (agentic-coding workspace) and `.worktrees/` (worktree provisioning). Committed `.env.example` / `.env.sample` / `.env.template` stay readable; live `.env` and the common `.env.local` / `.env.production` / etc. variants are denied. Other `.gitignore` entries are denied.
<!-- /managed:setup-permissions -->
```

Rules:

- Render the table from the DetectionResult: an intent appears as a row only if its canonical-intent target was found in detect. Intents with no matching target are skipped (the audit phase reports them separately).
- The body text outside the table is fixed and managed.

### Locate and replace

1. Read `AGENTS.md` if present.
2. Search for `<!-- managed:setup-permissions -->` ... `<!-- /managed:setup-permissions -->`. If found, replace the entire region (markers included) with the freshly rendered block.
3. If not found, append the block at the end of the file with one blank line of separation.
4. If `AGENTS.md` does not exist, create it with only the managed block.

The locate-and-replace is exact-string based, not regex, so user-authored content before/after the markers (including reorderings, surrounding sections) is preserved untouched.

### AGENTS.md / CLAUDE.md coupling

The canonical file is whichever one already exists. When only one is present, the other becomes a symlink to it. When both exist as separate real files, they are treated independently — the skill does not collapse user-authored divergence.

| `AGENTS.md` | `CLAUDE.md` | Action |
|---|---|---|
| absent | absent | Create `AGENTS.md` with the managed block. Symlink `CLAUDE.md` → `AGENTS.md`. |
| present (file) | absent | Write the managed block into `AGENTS.md`. Symlink `CLAUDE.md` → `AGENTS.md`. |
| absent | present (file) | Write the managed block into `CLAUDE.md`. Symlink `AGENTS.md` → `CLAUDE.md`. |
| present (file) | present (symlink to AGENTS.md) | Write the managed block into `AGENTS.md`; the symlink follows. |
| present (symlink to CLAUDE.md) | present (file) | Write the managed block into `CLAUDE.md`; the symlink follows. |
| present (file) | present (file) | Treat separately: write the managed block into each. Do **not** symlink — the user has chosen to maintain divergent files, and the skill must not collapse that. Content outside the managed region in each file is left untouched. |

The skill never replaces an existing real file with a symlink when both files already exist as real files. The "absent + present" cases create a symlink unprompted because there is no existing content to overwrite on the absent side.

### Re-runnability

Because the markers are exact strings and the table content is deterministic from the DetectionResult, a second run produces a byte-identical block. The whole file diffs to zero unless detection picked up a new target.

## Phase 4: Audit

The audit phase prints a plain-text report identifying gaps that would block autonomous agent work. It does not modify the runner file. It is the last phase in the default progression and is also invocable standalone.

### Checks

**Canonical-intent coverage.** For each canonical intent (`lint`, `fmt`, `test`, `test-one`, `lint-fix`, `gate`), report whether the primary runner has a matching target. Use the intent-matching table from the detect phase.

**Bash-wrapper simplicity.** If the runner's matching commands contain shell metacharacters (`$`, backticks, redirects, globs), warn that Codex execpolicy will fail to split-and-match these, falling back to sandbox/approval. Recommend simpler target bodies.

**Gitignore negations.** If any `.gitignore` lines started with `!`, repeat the warning emitted during detection: those denies need manual review.

**Deny-floor overlap.** Scan both `.claude/settings.json` (committed) and `.claude/settings.local.json` (personal) for `permissions.allow` entries that overlap with the sensitive-read deny floor — e.g., a `Read(./.env)` or `Read(./secrets/**)` allow. Surface each hit with its source file as a security gap. The local file is the more common location for these (developers occasionally allowlist things during a session); the committed file should normally not contain them. Git-related entries are not flagged — the deny floor doesn't cover git.

**Stale managed entries.** If existing managed entries no longer correspond to any DetectionResult target (e.g., a `Bash(just legacy-task)` allow when the justfile no longer has `legacy-task`), report them so the user can decide whether to drop them. The skill does not auto-prune — re-running detect should pick up the new state and overwrite cleanly, but stale allows are worth surfacing once.

### Report format

```
Audit: /abs/path/to/repo

Canonical intents (primary runner: just):
  lint        OK (just lint)
  fmt         OK (just fmt)
  test        OK (just test)
  test-one    MISSING — suggest: `just test-one PATTERN` wrapping `cargo test PATTERN`
  lint-fix    MISSING — suggest: `just lint-fix` wrapping `cargo clippy --fix`
  gate        OK (just gate)

Bash-wrapper simplicity:
  OK — all allowlisted runner commands are plain token sequences.

Gitignore negations:
  OK — none present.

Deny-floor overlap:
  OK — no allow entries in .claude/settings.json or .claude/settings.local.json collide with the floor.

Stale managed entries:
  OK — all managed allows still resolve to known targets.

Reminders:
  - Restart Codex CLI for the new `.codex/rules/default.rules` to take effect.
  - Run `/setup-permissions` again after the runner gains new canonical targets.
```

Each gap line starts with `MISSING` or `WARN` so the user can grep for them. `OK` lines are kept so users see what *was* checked, not just what failed.

### Suggested target stubs

For each `MISSING` canonical intent, the audit includes a one-line suggestion: a target name plus a candidate body that fits the detected runner. These are **suggestions** — the skill never edits the runner file unless the user explicitly opts in (this is the "audit does not mutate" rule from the plan's optimization target).

## Invocation

```
/setup-permissions               # default progression, with confirmation gates
/setup-permissions detect        # detection only
/setup-permissions permissions   # detect + render + write the three config files
/setup-permissions docs          # detect + render + write the AGENTS.md section
/setup-permissions audit         # detect + print the gap report
```

The skill always runs detection first, even when a later phase is requested in isolation — the in-memory DetectionResult is the input to every other phase.

## Guidelines

- Plain text only. No emojis in skill output, in the produced configs, or in commit messages.
- Never overwrite a config file blindly. Merge into existing structure; surface conflicts.
- Ask before guessing. Exotic runners, ambiguous gitignore patterns, and conflicting existing entries all warrant a prompt.
- Re-runnability matters, but byte-identical output isn't required. The managed surface must converge across runs given the same DetectionResult; entries added by sibling skills (`/fewer-permission-prompts`, future siblings) or by hand are preserved, not pruned. Use judgment about exactly when and how to invoke optional integrations like `/fewer-permission-prompts` — the SKILL describes the integration point, not a rigid sequence.
