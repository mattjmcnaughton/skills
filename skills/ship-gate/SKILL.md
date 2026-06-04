---
name: ship-gate
description: Fast pre-ship checklist on the current branch's diff against `main`. Runs seven mechanical checks (secrets, garbage files, machine-specific paths, debug residue, dead/duplicated code, commit-message hygiene, local gate) and offers auto-fixes. Use before `/create-pr` (pre-push) and before `/merge-pr` (pre-merge), or whenever the user says "ship gate", "before pushing", "before merging", "pre-push check", "pre-merge check", or "risk check before pr". Not a substitute for `/review` or `/review-pr`.
---

`/ship-gate` is a downside-risk filter, not a code review. It runs a small set of cheap mechanical checks on the current branch's diff against `main` and reports anything that would be high-regret to ship. The intent is the kind of 60-second scan a human would do before pushing or merging.

For deeper coverage — design, correctness, test gaps — use `/review` (pre-commit, local) or `/review-pr` (open PR). `/ship-gate` is complementary and deliberately narrow.

## When to use

- Right before `/create-pr`, to catch what you don't want to push.
- Right before `/merge-pr`, to catch what you don't want to merge.
- Any time the user says "ship gate", "pre-push check", "risk check before pr", or similar.

## When not to use

- As a replacement for `/review` or `/review-pr` — this skill makes no judgment calls about design or correctness.
- As a security audit — the secret-detection is heuristic only. Layer a real scanner (gitleaks, trufflehog) in CI for that.
- On a branch with no diff against `main`.

## Scope

- Content diff: `git diff main...HEAD` plus any uncommitted edits (`git diff` and `git diff --cached`).
- Commit subjects: `git log main..HEAD --pretty=%s` (and SHAs via `--pretty=%h %s` for citations).
- Working-tree files touched by the diff (for local-gate detection).

The skill never reads `.agentic/<slug>/plan.md` and works on branches that never went through `/prep`.

## Checks

Each check ends in a severity: **CLEAN**, **WARN**, or **FAIL**. WARN means "look at this and decide". FAIL means "fix before shipping".

### 1. Secret patterns — FAIL on hit

Grep the diff for known-bad shapes. Cite `file:line` for each hit.

- AWS access key IDs: `AKIA[0-9A-Z]{16}`
- AWS secret access keys: surrounding `aws_secret_access_key` assignments with 40-char base64-ish values
- GitHub tokens: `ghp_[0-9A-Za-z]{36}`, `gho_`, `ghu_`, `ghs_`, `ghr_` prefixes
- Slack tokens: `xox[abprs]-[0-9A-Za-z-]+`
- Private-key headers: `-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----`
- Generic assignments: lines matching `(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['"][^'"]{6,}['"]` — exclude obvious placeholders (`changeme`, `xxx`, `your-key-here`, `<...>`).

```bash
git diff main...HEAD | grep -nE 'AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36}|xox[abprs]-|-----BEGIN .*PRIVATE KEY-----'
```

### 2. Garbage files — FAIL on hit, offer to gitignore

Files that should never be tracked.

- `.DS_Store`, `Thumbs.db`
- `node_modules/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/`, `target/`, `.next/`, `out/`
- `.env`, `.env.local`, `.env.*` (not `.env.example`)
- `.agentic/` and any path inside it
- IDE configs: `.idea/`, `.vscode/` (unless the repo already tracks `.vscode/`), `*.swp`, `*.swo`
- OS junk: `.Trashes`, `.Spotlight-V100`

```bash
git diff --name-only --diff-filter=A main...HEAD
```

Cross-reference against the above list. Report the path; offer to add a matching pattern to `.gitignore` and `git rm --cached` the file.

### 3. Machine/user-specific hardcoding — WARN on hit

Absolute paths or hostnames that won't make sense on another machine.

- `/Users/<name>/`, `/home/<name>/`, `C:\\Users\\<name>\\`
- The current user's name (resolve via `$USER` or `id -un`) appearing as a literal in non-test code
- Hardcoded hostnames the user mentioned (`*.local`, machine name from `hostname`)
- Absolute paths under `$HOME` other than well-known references in docs

```bash
git diff main...HEAD | grep -nE "/Users/[^/]+/|/home/[^/]+/|C:\\\\Users\\\\[^\\\\]+\\\\"
```

Test fixtures and documentation examples that show paths intentionally are fine — WARN, not FAIL, so the user can confirm.

### 4. Embarrassing residue — WARN on hit (FAIL on conflict markers)

- Merge-conflict markers: `^<{7} `, `^={7}$`, `^>{7} ` — **FAIL**.
- Debug prints in non-test code added by this diff:
  - JS/TS: `console.log`, `console.debug`, `debugger`
  - Python: bare `print(`, `breakpoint()`, `import pdb`
  - Go: `fmt.Println` in non-`_test.go` files (heuristic; WARN)
  - Ruby: `binding.pry`, `puts` in non-test code (WARN)
- Commented-out code blocks added by this diff: contiguous 3+ lines beginning with the language's comment marker that look like code (heuristic; WARN).
- New `TODO`, `FIXME`, `XXX`, `HACK` comments added by this diff — WARN, with the line so the user can confirm intent.

Cite `file:line` for each finding.

### 5. Dead or duplicated code — WARN on hit

Best-effort, not exhaustive.

- Verbatim duplicate blocks: identify 6+ contiguous lines that appear more than once in the added diff (use `git diff main...HEAD | grep '^+' | sort | uniq -c | sort -rn` as a cheap starting point, then dedupe).
- Obvious unused new symbols: a new top-level function/const that no other file in the diff references and isn't exported by the package's index file. This is a heuristic — flag with WARN and let the user judge.

Don't try to do whole-program dead-code analysis. The optimization target is "cheap mechanical checks", not "perfect coverage".

### 6. Commit-message hygiene — WARN (FAIL for empty)

For each subject from `git log main..HEAD --pretty='%h %s'`:

- **FAIL**: empty subject.
- **WARN**: single word, `wip`, `asdf`, `fix`, `update`, `stuff`, `temp`, `test` as the entire subject; all-caps yelling; doesn't follow Conventional Commits roughly (`type(scope): subject` or `type: subject` where `type` is one of `feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`).

Cite the short SHA for each flagged commit.

Offer to rewrite via `git rebase -i main` — this is destructive (rewrites history), so require explicit per-commit confirmation in the auto-fix step.

### 7. Local gate — WARN on missing, FAIL on failing

Detect a gate command by walking these in order and using the first match:

1. `justfile` present → `just gate` (or `just test` if `gate` recipe doesn't exist; inspect with `just --summary`).
2. `Makefile` present with a `test` target → `make test`.
3. `package.json` present with a `test` script → `npm test` (or `pnpm test` / `yarn test` per lockfile).
4. `pyproject.toml` or `setup.cfg` or `pytest.ini` present → `pytest`.
5. `Cargo.toml` present → `cargo test`.
6. `go.mod` present → `go test ./...`.

Run the command and capture exit status.

- Exit 0: **CLEAN**.
- Non-zero: **FAIL**, print the last ~40 lines of output.
- No gate detected: report `no gate found` as **WARN** — don't fail silently.

## Report format

Terminal-only. No artifact written to `.agentic/`. The skill works inside or outside a task workspace.

```
Ship-gate report
Branch: <current> vs main (<N> commits, <M> files changed)

[1] Secrets             CLEAN
[2] Garbage files       FAIL    (1 hit)
    + .DS_Store
[3] Machine-specific    WARN    (1 hit)
    src/config.ts:42  "/Users/alice/repos/foo"
[4] Embarrassing        WARN    (2 hits)
    src/api.ts:88     console.log("debug")
    src/api.ts:120    TODO: handle 429
[5] Dead/duplicated     CLEAN
[6] Commit hygiene      WARN    (1 hit)
    a1b2c3d  wip
[7] Local gate          FAIL    (`just gate` exited 1)
    ... last 40 lines of output ...

Summary: 2 FAIL, 3 WARN, 2 CLEAN
```

When everything is CLEAN, collapse the output:

```
Ship-gate report
Branch: <current> vs main (<N> commits, <M> files changed)
All seven checks CLEAN.
```

Don't render seven empty headers when there's nothing to say.

## Follow-up: auto-fixes

After printing the report, if any finding is auto-fixable, ask one multi-select question listing only the fixable items. Each option says exactly what will happen.

| Category | Auto-fix | Destructive? |
|---|---|---|
| Garbage files | Append pattern to `.gitignore`, `git rm --cached <path>`, stage `.gitignore` | No |
| Debug prints | Remove the flagged lines from the working tree | No |
| Commented-out code | Remove the flagged blocks from the working tree | No |
| `TODO`/`FIXME`/`XXX` | Not auto-fixable — surface only | — |
| Conflict markers | Not auto-fixable — surface only (the user must resolve) | — |
| Machine-specific paths | Not auto-fixable — surface only (replacement requires judgment) | — |
| Secrets | Not auto-fixable — surface only, recommend revoking the credential and rewriting history with a real tool (`git filter-repo`, BFG); never offer a one-click history rewrite | — |
| Commit messages | `git rebase -i main` with pre-written replacement subjects, per-commit confirmation | **Yes** |
| Dead/duplicated | Not auto-fixable — surface only | — |
| Local gate failure | Not auto-fixable — re-run after the user fixes | — |

Rules:

- Never bundle destructive fixes with non-destructive ones; if the user selects a commit rewrite, confirm a second time before running `git rebase`.
- After applying any fix, re-run the affected check and report the new state.
- If the user declines all fixes, exit quietly. Don't lecture.

## Guidelines

- Plain text only. No emojis in output.
- No AI attribution in any rewritten commit messages.
- Heuristics, not guarantees. If a check is uncertain, prefer WARN over FAIL so the user decides.
- Documentation and test fixtures legitimately contain example patterns (regexes, fake tokens, sample paths). When a hit lives in `*.md`, `docs/`, `tests/`, `__tests__/`, or `fixtures/`, downgrade FAIL to WARN and say so in the report — the user can confirm intent in one glance instead of fighting the gate.
- Don't auto-chain into `/create-pr` or `/merge-pr`. The user runs those themselves.
- Don't read or write `.agentic/<slug>/`. This skill is standalone.
- Point users at `/review`, `/review-pr`, and CI scanners for anything deeper than mechanical checks.
