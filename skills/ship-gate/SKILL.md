---
name: ship-gate
description: Fast pre-ship checklist on the current branch's diff against `main`. Runs nine mechanical checks (secrets, garbage files, machine-specific paths, debug residue, dead/duplicated code, commit-message hygiene, local gate, new data sinks, unpinned dependencies) and offers auto-fixes. Use before `/create-pr` (pre-push) and before `/merge-pr` (pre-merge), or whenever the user says "ship gate", "before pushing", "before merging", "pre-push check", "pre-merge check", or "risk check before pr". Not a substitute for `/review` or `/review-pr`.
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

### 7. New data sources (inputs and outputs) — WARN on hit

List every data source this diff newly **reads from** or **writes to**. The point is to surface each one so the user can confirm it's intentional, named correctly, scoped to the right environment, and (for writes) covered by retention / backup / alerting policy.

Scan added lines (`git diff main...HEAD | grep '^+'`) and bucket each finding as **IN** (read) or **OUT** (write) — a source that's read-then-written counts as both.

- **Databases**: new `SELECT` / `INSERT` / `UPDATE` / `DELETE` / `UPSERT` / `MERGE`; new `CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`; migration files under `migrations/`, `alembic/`, `db/migrate/`, `prisma/migrations/`; new ORM model classes; new connection strings.
- **Object storage**: `s3://`, `gs://`, `azure://` URIs; SDK calls — reads (`GetObject`, `download_file`, `Bucket(...).get`) and writes (`PutObject`, `upload_file`, `blob.upload_from_*`).
- **Filesystem**: new read-mode (`open(..., 'r'|'rb')`, `fs.readFile`, `os.ReadFile`, `Path(...).read_text`) and write-mode opens (`open(..., 'w'|'a'|'wb'|'ab')`, `fs.writeFile`, `fs.appendFile`, `os.WriteFile`, `ioutil.WriteFile`, `Path(...).write_text`).
- **Queues / streams / pubsub**: consumers (`subscribe`, `consume`, `ReceiveMessage`, `GetRecords`) and producers (`producer.send`, `producer.produce`, `publish(`, `SendMessage`, `PutRecord`, `topic.publish`).
- **External HTTP**: any newly-called hostname — reads (`GET`) and writes (`POST` / `PUT` / `PATCH` / `DELETE`); new webhook URLs configured.
- **Logs / telemetry sinks**: new logger configured to ship somewhere (Datadog, Sentry, Honeycomb, OTel exporter) or new metric/event names emitted to an external system.
- **Config / env naming sources**: new env vars or config keys like `*_BUCKET`, `*_TABLE`, `*_TOPIC`, `*_QUEUE`, `*_DSN`, `*_WEBHOOK_URL`, `*_API_URL`, `DATABASE_URL_*`.

Report each source with direction, `file:line`, and a one-line description:

```
OUT  src/audit.py:42       INSERT into users_audit (new table)
OUT  src/uploader.py:88    s3://prod-events PutObject
IN   src/loader.py:14      GET https://api.partner.example/v2/orders
IN/OUT  config/db.yml:3    new postgres dsn ANALYTICS_DSN
```

Group by direction. Heuristic — prefer over-reporting; under-reporting is the failure mode that matters. Not auto-fixable.

### 8. New dependencies — WARN, escalated nudge on unpinned

List every new image, package, action, module, or system package this diff adds. For each, show the version constraint as-written and flag unpinned ones with a concrete pin suggestion. Floating versions are the most common cause of "it worked yesterday" regressions.

Check newly-added or modified lines in:

- **Dockerfiles / Containerfiles**: `FROM` lines. Flag `image` (no tag), `image:latest`, or floating major tags (e.g. `node:20`) and nudge to `image:tag@sha256:<digest>`.
- **docker-compose / k8s manifests**: `image:` keys.
- **Helm**: chart dependencies under `dependencies:` in `Chart.yaml`; flag missing `version:`.
- **Python**: `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`. Flag entries without `==` (or without `~=`/range constraints in `pyproject.toml`); `*` or no specifier is strongest nudge.
- **JS/TS**: `package.json` `dependencies` / `devDependencies` / `peerDependencies`. Flag `*`, `latest`, or git refs without a SHA. `^` / `~` are common with lockfiles — list but don't push hard; verify a lockfile is committed.
- **Go**: new `require` lines in `go.mod`.
- **Rust**: `Cargo.toml` `[dependencies]`; flag `*` or no version.
- **Ruby**: `Gemfile`; flag entries without a version constraint.
- **GitHub Actions**: `uses:` lines in `.github/workflows/*.yml`. Nudge `@<branch>` and `@v<major>` to `@<sha>`, especially for third-party actions.
- **Terraform**: `module` blocks (flag missing `version`), provider blocks (flag missing `version`).
- **System packages**: `apt-get install foo`, `apk add foo`, `brew install foo` — flag missing `=version`.

Report each with `file:line`, name, and constraint, marking pin status:

```
PINNED    Dockerfile:1               python:3.12.4-slim@sha256:abc...
UNPINNED  Dockerfile:8               node:20            -> pin to node:20.11.1-alpine@sha256:<digest>
UNPINNED  requirements.txt:4         httpx              -> pin to httpx==0.27.0
LOOSE     package.json:14            react ^18.2.0      (lockfile commits the actual version — verify package-lock.json is tracked)
UNPINNED  .github/workflows/ci.yml:22  actions/checkout@v4  -> pin to actions/checkout@<sha>
```

Group by manifest file. Not auto-fixable — resolving a pin requires looking up the current digest/version, which is a judgment call.

### 9. Local gate — WARN on missing, FAIL on failing

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
[7] Data sources        WARN    (2 hits)
    OUT  src/audit.py:42       INSERT into users_audit (new table)
    IN   src/loader.py:14      GET https://api.partner.example/v2/orders
[8] Dependencies        WARN    (2 hits)
    UNPINNED  Dockerfile:8                node:20  -> pin to node:20.11.1-alpine@sha256:<digest>
    UNPINNED  .github/workflows/ci.yml:22 actions/checkout@v4  -> pin to @<sha>
[9] Local gate          FAIL    (`just gate` exited 1)
    ... last 40 lines of output ...

Summary: 2 FAIL, 5 WARN, 2 CLEAN
```

When everything is CLEAN, collapse the output:

```
Ship-gate report
Branch: <current> vs main (<N> commits, <M> files changed)
All nine checks CLEAN.
```

Don't render nine empty headers when there's nothing to say.

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
| Data sources (in/out) | Not auto-fixable — surface only (user verifies naming, environment, ownership, retention) | — |
| Unpinned dependencies | Not auto-fixable — surface only (resolving a pin requires looking up the current digest/version) | — |
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
