---
name: setup-permissions
description: Configure the current repo so an agent (Claude Code or Codex CLI) can run lint, fmt, test, and gate commands without permission prompts, while still being blocked from reading gitignored files or running unsafe commands. Writes `.claude/settings.local.json`, `.codex/config.toml`, `.codex/rules/default.rules`, and an AGENTS.md command-reference section. Use when bootstrapping a repo for autonomous agent work, when a teammate added a new task runner, or when the audit phase should report runner gaps. Triggers include "set up agent permissions", "make this repo agent-ready", "let the agent run tests without asking", "audit my runner for agent gaps".
---

`/setup-permissions` makes the current repository ready for autonomous agent work. It detects the task runner, derives a deny scope from `.gitignore`, and writes coherent permission artifacts for both Claude Code (`.claude/settings.local.json`) and Codex CLI (`.codex/config.toml` plus `.codex/rules/default.rules`). It also updates `AGENTS.md` (and a sibling `CLAUDE.md`) with the canonical commands the agent should call, and audits the runner for missing targets.

The skill is **re-runnable**: a second invocation against an unchanged repo produces zero diffs. Existing user-authored entries in the config files are preserved; only the skill's own managed regions are rewritten.

## Phases

The skill is split into four phases. Each one is independently invocable:

- `/setup-permissions detect` — identify the task runner(s), enumerate runner targets, classify the `.gitignore` into deny globs. Prints a summary; writes nothing.
- `/setup-permissions permissions` — render and write `.claude/settings.local.json`, `.codex/config.toml`, `.codex/rules/default.rules`.
- `/setup-permissions docs` — render and write the managed command-reference section into `AGENTS.md` (and `CLAUDE.md`).
- `/setup-permissions audit` — check the detected runner for missing canonical targets (`lint`, `fmt`, `test`, `test-one`, `lint-fix`, `gate`) and print a plain-text gap report.

With no arguments, `/setup-permissions` runs the default progression: **detect → permissions → docs → audit**, pausing after each phase to show the proposed diff and ask for confirmation. Users can decline an individual phase and continue; the next phase will see whatever state is on disk.

## Phase 1: Detect

The detect phase reads the repository and builds an in-memory **DetectionResult**:

```
DetectionResult {
  runners: [Runner],           # may be empty; may be multiple
  primary_runner: Runner?,     # one of the above, picked per the rules below
  runner_targets: {Runner: [Target]},
  gitignore_entries: [str],    # raw lines, unfiltered
  existing_artifacts: {        # what's already on disk
    claude_settings: Path?,
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

Read `.gitignore` from the repo root only (do not recurse into nested `.gitignore` files in v1 — flag this as a known limitation in the printed summary). Translate each non-blank, non-comment line to a glob suitable for `.claude/settings.local.json` (Read deny) and `.codex/config.toml` (filesystem deny).

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

The translation is intentionally a 90% solution. The audit phase reminds the user to review the produced deny list before accepting.

### Detect output

At the end of the detect phase, print:

```
Detected runners: just (primary), pnpm
Targets covered: lint=just lint, fmt=just fmt, test=just test, gate=just gate
Targets missing: test-one, lint-fix
Gitignore entries translated: 7 (0 skipped due to negations)
Existing artifacts: .claude/settings.local.json (will merge), .codex/ (absent, will create)
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
  allow_git_ro:  [str],   # read-only git subcommands
  allow_git_rw:  [str],   # write-side git the agent may run unprompted (add, commit, worktree add)
  forbid_git:    [str],   # destructive/remote git the agent must NEVER run
}
```

Fixed contents (independent of detection):

- `allow_reads`: `Read`, `Glob`, `Grep` on the entire tree. The deny globs do the narrowing.
- `allow_git_ro`: `status`, `diff`, `log`, `show`, `blame`, `ls-files`, `branch` (no `-d`/`-D`), `rev-parse`, `remote -v`, `worktree list`, `for-each-ref`, `config --get`.
- `allow_git_rw`: `add`, `commit`, `worktree add`.
- `forbid_git`: `push`, `reset`, `clean`, `rebase`, `cherry-pick`, `checkout` (when used with `.` or paths — see Claude matcher note below), `restore`, `branch -D`.

Variable contents (depend on detection):

- `deny_globs`: the translated `.gitignore` list, deduplicated and sorted. Plus a hardcoded floor: `**/.env`, `**/.env.*`, `**/*.pem`, `**/*.key`, `**/secrets/**`, `**/credentials.json` regardless of `.gitignore`. The floor is non-removable; it protects against missing entries.
- `allow_runner`: the union of the primary runner's *canonical-intent targets* (lint, fmt, test, test-one, lint-fix, gate) plus any explicit extra targets the user named. Targets that didn't match a canonical intent are **not** allowlisted by default — the agent should ask before running them. Each entry is the full command string (e.g., `just lint`, `pnpm run test`).

### Claude renderer

Render to `.claude/settings.local.json` using this matcher syntax (already in the cheatsheet in `plan.md`):

| Model field | Claude matcher form |
|---|---|
| `allow_reads` (broad) | `"Read"`, `"Glob"`, `"Grep"` (entire-tool allow) |
| `deny_globs` (file glob) | `"Read(./<glob>)"` in `permissions.deny` |
| `allow_runner` (exact command) | `"Bash(<command>)"` in `permissions.allow` |
| `allow_runner` (prefix) | `"Bash(<runner> *)"` only when the user opts in (off by default — too broad) |
| `allow_git_ro` | one entry per subcommand: `"Bash(git status)"`, `"Bash(git status:*)"`, etc. The `:*` suffix lets arguments through. |
| `allow_git_rw` | `"Bash(git add:*)"`, `"Bash(git commit:*)"`, `"Bash(git worktree add:*)"` |
| `forbid_git` | one entry per subcommand in `permissions.deny`: `"Bash(git push)"`, `"Bash(git push:*)"`, etc. |

Claude's `Bash(git checkout)` matcher has no argument distinction, so we deny `Bash(git checkout)` and `Bash(git checkout:*)` outright. The agent can still ask the user to run a checkout manually.

### Worked example (this repo)

Given `.gitignore`:
```
.agentic
.worktrees
```

and a detected `just` runner with targets `lint`, `fmt`, `test`, `gate`, the renderer produces (showing only the managed regions; existing entries are preserved):

```json
{
  "permissions": {
    "allow": [
      "Bash(git add:*)",
      "Bash(git blame:*)",
      "Bash(git branch)",
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
      "Bash(just fmt)",
      "Bash(just gate)",
      "Bash(just lint)",
      "Bash(just test)",
      "Glob",
      "Grep",
      "Read"
    ],
    "deny": [
      "Bash(git branch -D)",
      "Bash(git checkout)",
      "Bash(git checkout:*)",
      "Bash(git cherry-pick:*)",
      "Bash(git clean:*)",
      "Bash(git push)",
      "Bash(git push:*)",
      "Bash(git rebase:*)",
      "Bash(git reset:*)",
      "Bash(git restore:*)",
      "Read(./.agentic/**)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./.worktrees/**)",
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

Both are required: `config.toml` alone does not block command execution, and `default.rules` is silently ignored unless the project layer is trusted (covered in audit, below).

#### `.codex/config.toml`

The renderer manages exactly three top-level surfaces and leaves everything else (e.g., `[features]`, `[mcp_servers.*]`, `[projects."<path>"]`) untouched:

- `default_permissions = "agent-default"`
- `approval_policy = { granular = { sandbox_approval = true, rules = true, request_permissions = true, mcp_elicitations = true, skill_approval = true } }`
- the named profile `[permissions.agent-default]`

The profile body:

```toml
[permissions.agent-default]
extends = ":workspace"

[permissions.agent-default.filesystem]
# Generated from .gitignore; do not edit by hand.
".agentic/**" = "deny"
".worktrees/**" = "deny"
"**/.env" = "deny"
"**/.env.*" = "deny"
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

# --- git: read-only -----------------------------------------------------
prefix_rule(
    pattern = ["git", ["status", "diff", "log", "show", "blame", "ls-files",
                       "branch", "rev-parse", "remote", "worktree", "for-each-ref",
                       "config"]],
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

# --- git: forbidden ----------------------------------------------------
prefix_rule(
    pattern = ["git", ["push", "reset", "clean", "rebase", "cherry-pick",
                       "checkout", "restore"]],
    decision = "forbidden",
    justification = "Destructive or remote-affecting git; run manually.",
)
```

Notes:

- `pattern = ["git", ["a", "b", ...]]` matches `git a ...` or `git b ...`; inner-list alternation is token-level.
- Default decision is `allow`, so omitting a rule does not forbid the command — denials must be explicit.
- The strictest matching rule wins (`forbidden` > `prompt` > `allow`), so the read-only allow above is correctly overridden by the forbidden push/reset/etc. rule below.
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

#### Trust-level note (also surfaced in audit)

Project-local `.codex/` layers are silently ignored unless the user has marked the project trusted in their **user-level** `~/.codex/config.toml`. The renderer cannot do this for them (it's outside the project tree), but the docs phase prints the exact snippet they need to paste:

```toml
[projects."/abs/path/to/this/repo"]
trust_level = "trusted"
```

The audit phase repeats this if the trust check fails.

#### Restart note

Codex loads `.rules` files at startup. After running `/setup-permissions`, the user must restart Codex for new rules to take effect. The skill prints a reminder at the end of the run.

### Claude merge rules

The settings file frequently contains user-authored entries from earlier sessions (the existing `.claude/settings.local.json` in this repo proves the point — it holds two ad-hoc `Bash(...)` allows the user added during research). The renderer **must preserve them**.

Algorithm:

1. Read the existing JSON if it exists. If parse fails, refuse to overwrite — show the file path and the parse error, ask the user to fix it manually.
2. Compute the desired `allow`/`deny` arrays from the PermissionModel as **managed entries**.
3. Treat any existing entry not in the managed set as a **user entry**; preserve it.
4. Union: `final_allow = sort_unique(managed_allow + user_allow)`. Same for deny.
5. If a user entry contradicts a managed deny (e.g., user has `Bash(git push)` in allow but the model wants it denied), keep the user entry and emit a warning in the diff preview — the user gets the final call.
6. Write the file with stable 2-space indentation, arrays sorted, trailing newline.

The "managed entries" set is derived deterministically from the PermissionModel, so a second invocation against the same repo computes the same managed set, finds the same union, and produces a byte-identical file.

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

Filesystem scope: agent reads/writes the working tree; `.agentic/`, `.worktrees/`, and any `.gitignore` entries are denied. Destructive git (`push`, `reset`, `clean`, `rebase`, `cherry-pick`, `checkout`, `restore`) is forbidden — ask the user to run those manually.

For Codex CLI: this project's `.codex/` layer must be marked trusted in your user-level `~/.codex/config.toml` for the rules to load.
<!-- /managed:setup-permissions -->
```

Rules:

- Render the table from the DetectionResult: an intent appears as a row only if its canonical-intent target was found in detect. Intents with no matching target are skipped (the audit phase reports them separately).
- The trust-level note is always present when the skill writes to a repo that contains a `.codex/` directory (after the permissions phase). It's omitted when only `AGENTS.md` is being written without Codex config — but in the default progression Codex config is always written first, so the note is always present in practice.
- The body text outside the table is fixed and managed.

### Locate and replace

1. Read `AGENTS.md` if present.
2. Search for `<!-- managed:setup-permissions -->` ... `<!-- /managed:setup-permissions -->`. If found, replace the entire region (markers included) with the freshly rendered block.
3. If not found, append the block at the end of the file with one blank line of separation.
4. If `AGENTS.md` does not exist, create it with only the managed block.

The locate-and-replace is exact-string based, not regex, so user-authored content before/after the markers (including reorderings, surrounding sections) is preserved untouched.

### AGENTS.md / CLAUDE.md coupling

Three concrete scenarios:

| `AGENTS.md` | `CLAUDE.md` | Action |
|---|---|---|
| absent | absent | Create `AGENTS.md` with the managed block. Create `CLAUDE.md` as a symlink to `AGENTS.md`. |
| present (file) | absent | Update `AGENTS.md` as above. Create `CLAUDE.md` as a symlink to `AGENTS.md`. |
| present (file) | present (file, not a symlink) | Update both: write the managed block into each. Ask the user once whether they want to consolidate to a symlink (`y` → delete `CLAUDE.md`, replace with symlink; `n` → keep both as real files). |
| present (file) | present (symlink to AGENTS.md) | Update only `AGENTS.md`; the symlink follows. |
| absent | present (file) | Create `AGENTS.md` with the managed block. Leave `CLAUDE.md` alone unless the user opts in to symlinking. |

The skill never replaces an existing real file with a symlink without explicit confirmation. Asymmetric content (the user has different guidance in `AGENTS.md` vs `CLAUDE.md`) is left untouched outside the managed region.

### Re-runnability

Because the markers are exact strings and the table content is deterministic from the DetectionResult, a second run produces a byte-identical block. The whole file diffs to zero unless detection picked up a new target.

## Phase 4: Audit

The audit phase prints a plain-text report identifying gaps that would block autonomous agent work. It does not modify the runner file. It is the last phase in the default progression and is also invocable standalone.

### Checks

**Canonical-intent coverage.** For each canonical intent (`lint`, `fmt`, `test`, `test-one`, `lint-fix`, `gate`), report whether the primary runner has a matching target. Use the intent-matching table from the detect phase.

**Codex trust-level.** If `.codex/config.toml` exists in the repo, check whether the user's `~/.codex/config.toml` contains a matching `[projects."<abs-path>"]` entry with `trust_level = "trusted"`. If absent, surface the gap and print the exact snippet to paste. (The skill cannot edit the user-level config — that's outside the project tree.)

**Bash-wrapper simplicity.** If the runner's matching commands contain shell metacharacters (`$`, backticks, redirects, globs), warn that Codex execpolicy will fail to split-and-match these, falling back to sandbox/approval. Recommend simpler target bodies.

**Gitignore negations.** If any `.gitignore` lines started with `!`, repeat the warning emitted during detection: those denies need manual review.

**Deny-floor overlap.** If the user-authored `permissions.allow` list contains entries that overlap with the deny floor (e.g., a `Read(./.env)` allow), surface this as a security gap — the floor will lose to the user allow only when the user explicitly placed the entry, so it deserves a prompt.

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

Codex trust level:
  MISSING in ~/.codex/config.toml. Paste:

    [projects."/abs/path/to/repo"]
    trust_level = "trusted"

Bash-wrapper simplicity:
  OK — all allowlisted runner commands are plain token sequences.

Gitignore negations:
  OK — none present.

Deny-floor overlap:
  OK — no user allow entries collide with the floor.

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
- Re-runnability is a hard requirement. Every render must be deterministic given the same DetectionResult.
