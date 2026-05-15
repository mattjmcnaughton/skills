---
name: review-pr
description: Review an open GitHub PR (yours or someone else's). Fetches the PR via `gh`, examines the diff with configurable depth, and posts review comments. Distinct from /review, which is local pre-commit self-review.
---

Review a GitHub PR by URL or number, examine the diff, and produce findings. Optionally post the review back to GitHub via `gh`. Adapts depth based on review mode.

## Input

- **PR reference** (required): URL, `#N`, or `org/repo#N` for cross-repo.
- **Review mode** (optional): `iteration`, `standard`, `critical`, `security`. Defaults are derived; see "Mode selection" below.
- **Focus** (optional): "focus on error handling", "check the API contract", etc.

## Fetch

```bash
gh pr view <ref> --json number,title,body,headRefName,baseRefName,author,labels,files
gh pr diff <ref>
```

Also `gh pr checks <ref>` to see CI state.

## Mode selection

If the user didn't say:
- **Security** when the changed files involve auth, sessions, input handling, secrets, or external HTTP.
- **Critical** when the files touch payments, data integrity, migrations, concurrency primitives, or core business logic.
- **Iteration** when the repo is pre-1.0 (check `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod` tags).
- **Standard** otherwise.

When ambiguous, ask once.

## Gather context

- Read related test files for the changed code.
- Find callers / consumers of modified symbols (`grep -r` the symbol name; or read import sites).
- Read `CLAUDE.md`, `AGENTS.md`, and any `.claude/rules/*.md` in the PR's repo — apply repo-specific conventions.
- Note documented test commands so suggested follow-ups are runnable.

## Mode focus

- **Iteration (light)**: direction and approach; major blockers only. Skip micro-style and edge cases.
  *Mindset*: "Is this heading the right way?"
- **Standard (medium)**: correctness, maintainability, conventions, error handling, test coverage.
  *Mindset*: "Would I merge this?"
- **Critical (deep)**: edge cases, failure modes, data integrity, race conditions, error propagation completeness.
  *Mindset*: "What could go wrong, and have we handled it?"
- **Security (deep)**: input validation, injection, auth/authz, sensitive data handling, CSRF/CORS, secret exposure.
  *Mindset*: "How would an attacker exploit this?"

## Categorize findings

- **Critical** — must address before merge.
- **Suggestion** — should consider.
- **Nit** — optional polish.

If the PR is solid, "No changes necessary" is a valid verdict.

## Output

Print a review document with this shape:

```markdown
# PR Review: <repo>#<N> — <title>

**Mode**: <mode>
**Scope**: <N files, +X/-Y>
**Verdict**: Approve | Approve with suggestions | Request changes | No changes necessary

## Findings

### Critical
- <file:line> — <issue, recommended fix>
(or "None")

### Suggestions
- <file:line> — <suggestion, rationale>

### Nits
- <file:line> — <optional polish>

## Coverage and impact
- **Test gaps**: <changed code lacking tests, or "adequate">
- **Breaking changes**: <list or "none">
- **Docs**: <updates needed or "none">

## Context examined
<files/areas read for context>
```

## Posting back to GitHub (optional)

Ask: "Post this review to the PR? (y/n)". On `y`:
- For a single approval/request-changes/comment-only review:
  ```bash
  gh pr review <ref> --approve|--request-changes|--comment --body-file <tmp>
  ```
- For inline line-comments, post the document as a single comment body. Inline line-level comments require the GitHub review API and the `--body-file` flow; if doing inline, post one batched review with multiple `-c file:line:msg` (gh doesn't expose this directly — fall back to a top-level comment listing file:line for each finding).

## Guidelines

- Be specific. Every finding needs file:line and a concrete suggestion.
- Praise what works. Honest assessment is more valuable than uniform criticism.
- Stay in scope of the PR. Don't expand into unrelated code.
- Suggest, don't demand, for non-critical items.
- Don't offer to implement fixes — `/review-pr` is advisory.
- Plain text only.
