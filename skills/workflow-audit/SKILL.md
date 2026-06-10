---
name: workflow-audit
description: >-
  Read an existing `docs/workflows.md` (produced by `/workflow-catalog`) and
  report unit / integration / end-to-end test coverage per workflow. For each
  workflow ID, find tests that exercise it via explicit `<!-- tests: ... -->`
  annotations, embedded `WF-<DOMAIN>-NNN` references, test-name matches against
  the workflow title, or code-path heuristics tied to the workflow's source
  files. Classify hits by test layer and write a coverage report (default
  `docs/workflow-coverage.md`). Use when the user asks to "audit our workflow
  test coverage", "what workflows aren't tested", "coverage report by
  workflow", "which workflows have e2e tests", or "find untested user flows".
  Pairs with `/workflow-catalog`, which produces the input file.
---

`/workflow-audit` answers one question per workflow in `docs/workflows.md`: *do tests exist that look like they exercise this workflow, and at what layer?*

It is not a line-coverage tool. It does not run the test suite. It scans test files, links them to workflows by ID, name, or code-path heuristic, classifies each hit by layer (unit / integration / e2e), and writes a markdown report the user can read in one pass. False positives and false negatives are expected; the report surfaces ambiguous matches for confirmation, and users can pin truth by adding `<!-- tests: ... -->` annotations to `docs/workflows.md`.

## When to use

- The user has a `docs/workflows.md` (or equivalent path) from `/workflow-catalog` and wants a coverage snapshot.
- A workflow shipped and the user wants to confirm the test layers actually exercise it.
- Pre-release sweep: "which user-facing flows have no e2e coverage?"
- A teammate asks "where are the gaps in our test coverage by feature, not by line?"

## When not to use

- No `docs/workflows.md` exists yet — route the user to `/workflow-catalog` first. Do not invent workflows in this skill.
- The user wants line / branch coverage — that's a coverage tool (`nyc`, `coverage.py`, `go test -cover`), not this skill.
- The user wants to *run* the tests to confirm they pass — that's the project's own test command, not this skill. This skill only checks whether tests *exist* that look like they exercise the workflow.
- The user wants test recommendations / generation — deferred to a future `workflow-test` skill.

## Prerequisites

- `docs/workflows.md` (or the user-named path) must exist and follow the format `/workflow-catalog` writes:

  ```
  ## <DOMAIN>

  WF-<DOMAIN>-NNN — <title> — <one-line description>
  ```

  with optional `<!-- tests: <file>[:<test-name>][, <file>[:<test-name>]...] -->` annotations on the line below.

- A test directory or convention exists in the repo. If the repo has no tests at all, the report is trivially "all workflows missing" — flag this up front rather than running.

## Process

### Step 1 — Confirm inputs and output path

Ask the user, in one batched prompt:

1. **Input file** — default `docs/workflows.md`. The user can pick a different path.
2. **Output report path** — default `docs/workflow-coverage.md`. Configurable.
3. **Scope** — full audit (default) or a subset of domains (e.g. `AUTH,CHECKOUT`)?
4. **Test roots** — let the user override the auto-detected test directories if the heuristics get it wrong.

Read `.agentic/<slug>/plan.md` if a slug workspace exists.

### Step 2 — Parse `docs/workflows.md`

Read the file and parse workflows. The format `/workflow-catalog` writes is the contract.

Parser rules:

- Domain heading: `^## (?P<domain>[A-Z0-9_]+)\s*$`
- Workflow line: `^(?P<id>WF-[A-Z0-9_]+-\d{3}) — (?P<title>.+?) — (?P<desc>.+)$`
- Optional pin line, immediately after a workflow line: `^<!-- tests: (?P<pins>.+) -->\s*$`
  - `pins` is comma-separated. Each entry is `<file>` or `<file>:<test-name>` (test-name may be quoted).
- Ignore lines that don't match either pattern. If a `WF-`-prefixed line fails the format check, stop and surface it: the catalog is malformed and the user should fix it (or re-run `/workflow-catalog`) before proceeding.

Build an in-memory list: `[{id, domain, title, desc, pins: [(file, test_name?)]}]`.

### Step 3 — Detect test frameworks and roots

Probe the repo to figure out which frameworks are in use. Cheap signals:

| Signal | Framework |
|---|---|
| `jest.config.*` or `jest` key in `package.json` | Jest |
| `vitest.config.*` or `vitest` dep | Vitest |
| `playwright.config.*` | Playwright |
| `cypress.config.*` or `cypress/` dir | Cypress |
| `pytest.ini`, `pyproject.toml` `[tool.pytest.ini_options]`, `conftest.py` | pytest |
| `**/*_test.go` files | go test |
| `Gemfile.lock` has `rspec`, `spec/` dir | RSpec |
| `RSpec.describe` in `spec/**/*_spec.rb` | RSpec |
| `phpunit.xml` | PHPUnit |
| `Cargo.toml` `[dev-dependencies]` + `#[test]` in files | Rust built-in tests |

Record which frameworks fire. If none fire, ask the user where the tests live.

### Step 4 — Enumerate test cases per framework

For each detected framework, list test files and (where possible) individual test names. The goal is to build a flat catalog `[(file, layer, test_name?, code_imports?)]` that the linker can search.

#### Jest / Vitest (JS / TS)

- **Files**: `**/*.test.{ts,tsx,js,jsx}`, `**/*.spec.{ts,tsx,js,jsx}`, `__tests__/**`.
- **Test names**: grep `^\s*(it|test|describe)\(\s*['"\`](?P<name>[^'"\`]+)`. `describe` names compose with the `it` inside (concatenate with " > ").
- **Layer classification**:
  - Files under `e2e/`, `tests/e2e/`, or with `.e2e.` in the name → e2e (only if not Playwright/Cypress, which classify separately).
  - Files under `integration/`, `tests/integration/`, or with `.integration.` → integration.
  - Files that import `supertest`, `msw`, `nock`, or hit a real DB / fixture → integration.
  - Otherwise → unit.
- **Code imports** (for heuristic linking): grep top-of-file `import ... from '<path>'` and `require('<path>')`. Resolve relative paths against the test file's location.

#### Playwright / Cypress (browser e2e)

- **Files**: `tests/**/*.spec.{ts,js}` (Playwright config), `e2e/**/*.spec.{ts,js}`, `cypress/e2e/**/*.cy.{ts,js}`.
- **Test names**: grep `test\(\s*['"\`](?P<name>[^'"\`]+)` for Playwright, `it\(\s*['"\`](?P<name>[^'"\`]+)` for Cypress.
- **Layer**: always **e2e**. Browser-driven.
- **Page hints** (for heuristic linking): grep `\.goto\(\s*['"\`](?P<url>[^'"\`]+)` (Playwright) and `cy\.visit\(\s*['"\`](?P<url>[^'"\`]+)` (Cypress). The URL fragment is a strong workflow signal.

#### pytest (Python)

- **Files**: `tests/**/*.py`, `**/test_*.py`, `**/*_test.py`.
- **Test names**: `^def (test_[A-Za-z0-9_]+)\(` (top-level), and inside `class Test...:` blocks.
- **Layer**:
  - Files under `tests/e2e/` or marked `@pytest.mark.e2e` → e2e.
  - Files under `tests/integration/`, marked `@pytest.mark.integration`, or that use `testcontainers`, `pytest-postgresql`, real `httpx` against a running server → integration.
  - Files that use `respx`, `httpx_mock`, or fully mock external I/O → unit.
  - Otherwise → unit.
- **Code imports**: grep `^from (?P<mod>[\w.]+) import` and `^import (?P<mod>[\w.]+)`. Module name maps to a file path under the source root.

#### go test

- **Files**: `**/*_test.go`.
- **Test names**: `^func (Test[A-Za-z0-9_]+)\(`.
- **Layer**:
  - Files with build tag `//go:build e2e` or path under `e2e/` → e2e.
  - Files using `httptest.NewServer`, `dockertest`, or `testcontainers-go` → integration.
  - Otherwise → unit.
- **Code imports**: grep the import block at the top of the file. Internal package paths (`<module>/...`) are the link signal.

#### RSpec (Ruby)

- **Files**: `spec/**/*_spec.rb`.
- **Test names**: `RSpec\.describe\b.*do`, `describe\b.*do`, `it\b.*do`. Names compose.
- **Layer**:
  - `spec/features/`, `spec/system/` (Capybara) → e2e.
  - `spec/requests/`, `spec/integration/` → integration.
  - `spec/models/`, `spec/services/`, `spec/lib/` → unit.

#### PHPUnit (PHP)

- **Files**: `tests/**/*Test.php`.
- **Test names**: `public function (test[A-Za-z0-9_]+)\(`.
- **Layer**: by directory convention (`tests/Unit/`, `tests/Integration/`, `tests/E2E/`).

#### Other / unknown

If the user's stack isn't covered, ask them up front:

- Where do tests live?
- What naming convention?
- How do you distinguish layers?

Encode the answers as a quick ad-hoc probe for that run.

### Step 5 — Link tests to workflows

For each workflow, walk through the linking strategies in this priority order. Stop at the first strategy that yields hits — but record the strategy used, so the report can show *why* a test was linked.

#### Strategy A — Explicit pin

If the workflow has `<!-- tests: ... -->` pins, every pinned `(file[, test-name])` is a confirmed hit. Layer is whatever the test catalog says for that file. Strategy: `pinned`.

#### Strategy B — ID reference in test file

Grep all test files for the literal workflow ID:

```
git grep -E 'WF-<DOMAIN>-\d{3}' -- tests/ spec/ '**/*.test.*' '**/*.spec.*' '**/*_test.go'
```

If a test file mentions `WF-AUTH-001` in a comment, name, or string, that's a hit. Strategy: `id-reference`.

#### Strategy C — Title string match in test names

For each test name in the catalog, lowercase and strip punctuation; compare to the workflow title under the same normalization.

- Exact match → hit. Strategy: `exact-name-match`.
- Substring match (workflow title is a substring of the test name, or vice versa, with both at least 3 words) → ambiguous hit. Strategy: `substring-name-match`. Surface for user confirmation.
- Don't fuzzy-match below substring. Levenshtein and embeddings produce too many false positives at this scope.

#### Strategy D — Page-URL hint (e2e only)

For Playwright / Cypress hits, compare the `goto` / `visit` URL against the workflow's evidence files. If `workflow-catalog` recorded `apps/web/app/checkout/page.tsx` for `WF-CHECKOUT-002`, then a `goto('/checkout')` test is a likely hit. Strategy: `e2e-url-match`. Mark as ambiguous unless name also matches.

#### Strategy E — Code-path import heuristic

Workflow evidence files (from `workflow-catalog`'s probe) include route handlers, page components, CLI command handlers. For each test file, check whether its imports / required modules include any of those evidence files. If so, the test exercises code on the workflow's path — likely hit. Strategy: `import-heuristic`. Always mark as ambiguous.

For this to work, you need the original evidence files. Options:

- **If `workflow-catalog` was just run in the same session:** evidence is in memory.
- **If working from `docs/workflows.md` alone:** re-probe the workflow titles against the codebase using the patterns in `/workflow-catalog`'s probe table. Cheap because you only need rough matches for the titles already in the file.
- **If neither:** skip Strategy E and note it in the report.

#### Recording results

Per workflow, accumulate `[(layer, test_file, test_name, strategy)]`. Deduplicate by `(test_file, test_name)` — same test linked by multiple strategies counts once but record the strongest strategy.

#### Layer roll-up

Per workflow, derive a per-layer status:

- **covered** — at least one non-ambiguous hit (strategies A, B, or C-exact) at this layer.
- **partial** — only ambiguous hits (substring, URL, import) at this layer.
- **missing** — no hits at this layer.
- **unknown** — framework for this layer not detected in the repo (e.g. no Playwright config → e2e layer is "unknown" for the whole project; report this once at the top, not per workflow).

### Step 6 — Write the coverage report

Default path `docs/workflow-coverage.md`. Re-run behavior: **overwrite**. The report has a timestamp at the top so the user can tell when it was generated; older reports are not preserved (use git history if needed).

Report structure:

```markdown
# Workflow coverage report

**Generated**: <ISO date>
**Source**: docs/workflows.md
**Workflows**: <count>
**Frameworks detected**: <list, e.g. Jest, Playwright, pytest>
**Layers in scope**: unit, integration, e2e
<!-- Unknown layers (no framework detected): list, or empty -->

## Summary

| Domain | Workflows | Unit | Integration | E2E |
|---|---|---|---|---|
| AUTH | 4 | 4 covered | 3 covered, 1 partial | 2 covered, 2 missing |
| CHECKOUT | 3 | 2 covered, 1 missing | 1 covered, 2 missing | 0 covered, 3 missing |
| ... | ... | ... | ... | ... |

## Workflows

### WF-AUTH-001 — Log in

- **Unit**: covered
  - `apps/web/auth/login.test.ts` > "validates credentials" (exact-name-match)
  - `apps/api/tests/test_auth.py::test_login_valid` (id-reference)
- **Integration**: covered
  - `apps/api/tests/integration/test_auth_session.py::test_login_creates_session` (substring-name-match) — ambiguous, please confirm
- **E2E**: missing

### WF-AUTH-002 — Sign up

- **Unit**: covered
  - `apps/web/auth/signup.test.ts` > "rejects existing email" (exact-name-match)
- **Integration**: missing
- **E2E**: covered
  - `e2e/auth.spec.ts` > "user can sign up and log in" (e2e-url-match: goto('/signup'))

### WF-CHECKOUT-001 — Place order

- **Unit**: missing
- **Integration**: partial
  - `apps/api/tests/test_orders.py::test_create_order_persists` (import-heuristic: imports routers.orders) — ambiguous, please confirm
- **E2E**: missing

## Gaps

Workflows with missing coverage at the most user-visible layer (e2e if detected, else integration, else unit):

- WF-AUTH-001 — Log in — e2e missing
- WF-AUTH-003 — Log out — e2e missing
- WF-CHECKOUT-001 — Place order — e2e missing
- WF-CHECKOUT-002 — View orders — e2e missing
- WF-CHECKOUT-003 — View order detail — e2e missing

## Ambiguous matches

These hits are heuristic. Confirm or pin to lock them in (add `<!-- tests: ... -->` to docs/workflows.md):

- WF-AUTH-001 (Integration) — `apps/api/tests/integration/test_auth_session.py::test_login_creates_session` (substring-name-match)
- WF-CHECKOUT-001 (Integration) — `apps/api/tests/test_orders.py::test_create_order_persists` (import-heuristic)
```

After writing, tell the user the path and a one-line summary (e.g. "5 workflows missing e2e coverage; 2 ambiguous matches need confirmation").

## Confirming ambiguous matches and persisting truth

When the user wants to lock in (or reject) ambiguous matches:

1. Show the ambiguous list with prompts: keep / drop / re-assign to a different workflow.
2. For matches the user keeps, propose adding an annotation to `docs/workflows.md`:

   ```markdown
   WF-AUTH-001 — Log in — User authenticates with email and password and receives a session.
   <!-- tests: apps/web/auth/login.test.ts:"validates credentials", apps/api/tests/integration/test_auth_session.py::test_login_creates_session -->
   ```

3. On the next `/workflow-audit` run, Strategy A picks these up directly and the match is no longer ambiguous.

Do not edit `docs/workflows.md` without explicit user confirmation — that file is owned by `/workflow-catalog`.

## Guidelines

- **Best-effort, not authoritative.** This is a discovery tool. Surface what looks like it lines up; let the user confirm. Don't claim "0% coverage" when the linker just couldn't find the connection.
- **Strict parsing of the input.** If `docs/workflows.md` has a malformed `WF-` line, stop and report. Better to bail than to silently miss workflows.
- **Read the code, don't guess at file paths.** Before reporting an import-heuristic hit, the test file's import line must actually exist in the test file — grep it; don't infer.
- **Show the strategy.** Every hit in the report is annotated with how it was linked. The user needs to know the difference between a pin (truth) and an import-heuristic hit (guess).
- **Layer classification is by directory and convention.** When in doubt, classify down (an unclear file is integration, not e2e). Better to under-report e2e coverage than over-report it.
- **Don't run the tests.** This skill scans, it does not execute. If the user wants to run the suite, that's their test command, not this skill.
- **Plain text only.** No emojis in the report or in interview prompts.
- **No AI attribution** in the generated file. Header comment is the only generator marker.
- **Overwrite, don't append.** Reports stay in `docs/workflow-coverage.md`. Older versions live in git history.
