---
name: audit-bug-patterns
description: >-
  Audits bug-fix patterns across the last N commits or a specific commit date
  range, classifies root causes and escape factors, and recommends durable
  prevention in code, tests, tooling, and progressively disclosed
  documentation. Uses local Git history by default and requires explicit
  confirmation before fetching remote history or reading ticket and bug
  trackers. Use for bug retrospectives, recurring-defect analysis, engineering
  process audits, and requests to prevent classes of bugs from recurring.
---

`/audit-bug-patterns` turns recent defect history into a small set of evidence-backed changes that prevent recurrence. It is not a commit-summary generator and does not assume every commit containing "fix" represents a product bug.

## Principles

1. **Local first.** Read the worktree and locally available Git objects without confirmation. Do not fetch, call an API, open a web page, or query a ticket system without explicit confirmation for that source.
2. **Evidence before classification.** Separate observed facts, likely interpretations, and unknowns. Never claim a root cause from a commit title alone.
3. **Two causes, not one label.** Identify both the proximate defect (what was wrong) and the escape factor (why existing controls allowed it to ship or persist).
4. **Prevent over remind.** Prefer eliminating invalid states, strengthening interfaces, or adding automated enforcement. Documentation and agent instructions are lower in the prevention hierarchy.
5. **Progressive disclosure.** Keep `CLAUDE.md` and `AGENTS.md` short and repository-wide. Put details in the narrowest owned document and link to it from a central file only when agents genuinely need that route.
6. **Patterns over anecdotes.** Recommend systemic changes only when evidence shows recurrence or when one high-impact defect exposes a clear invariant that can be enforced cheaply.

## When not to use

- A single known bug needs debugging or implementation rather than retrospective analysis.
- The user wants a general code-quality review of an uncommitted diff.
- There is no relevant history and the user does not want to provide incidents or authorize another source. Report the evidence gap instead of inventing patterns.

## Step 1 — Confirm scope

Ask one batched question covering any inputs the user has not supplied:

1. **Repository and refs** — default to commits reachable from local `HEAD`. The user may name a branch, tag, or already-present remote-tracking ref. Do not silently use `--all`; merged and duplicate histories can distort counts.
2. **Commit window** — choose exactly one:
   - **Count:** last N commits; default N = 50.
   - **Date range:** `since` and `until`; either bound may be open.
3. **History shape** — all commits reachable from the selected ref (default), or first-parent history when the user wants merged changes treated as one integration stream.
4. **External evidence** — none (default), refreshed Git remote history, and/or named ticket or bug trackers.
5. **Output** — terminal report (default) or a user-named Markdown path.

If the request names both N and a date range, ask which is the primary boundary. Do not combine them silently. A user may explicitly request a cap within a date range; in that case report that the range was truncated.

### Date semantics

- Use the commit's **committer date**, matching normal `git log` date filtering. Say so in the report.
- Date-only bounds are inclusive calendar dates in the user's local timezone. Normalize the lower bound to 00:00:00 and the upper bound to the start of the following day as an exclusive boundary.
- Timestamps with an offset or IANA timezone use that timezone. If a timestamp omits timezone, ask; do not guess when time-of-day matters.
- Record the normalized bounds and timezone in the report so the audit can be reproduced.
- Apply the same normalized window to approved external sources where their API permits it. If a tracker filters by creation or update time rather than incident/fix time, state the exact field used and the resulting limitation.

## Step 2 — Establish available evidence without network access

Inspect:

- Repository guidance and architecture: `README*`, `CLAUDE.md`, `AGENTS.md`, and relevant `docs/` indexes.
- Current ref and commit: `git branch --show-current`, `git rev-parse HEAD`.
- Local refs, including already-present remote-tracking refs: `git for-each-ref refs/heads refs/remotes`.
- Shallow state: `git rev-parse --is-shallow-repository`.
- The selected commit list using `git log` with the confirmed count or normalized dates, ref, and history shape.

Reading an existing `refs/remotes/...` ref is local and needs no confirmation. Running `git fetch`, `git pull`, `gh`, a tracker CLI, an MCP tool, `curl`, a browser, or any network-backed tool is external access.

If local history is shallow or the requested ref/window is unavailable:

1. Explain exactly what local evidence exists and how it limits the audit.
2. Ask whether to fetch the minimum required remote/ref/history. Name the remote and proposed read-only command or operation.
3. Continue with local evidence if the user declines, prominently marking the incomplete range.

Do not treat credentials, configured remotes, installed CLIs, ticket IDs in commits, or prior authorization for another service as permission.

## Step 3 — Gate each external source separately

Before external access, ask for confirmation that names:

- Service and repository/project, such as GitHub `owner/repo` or Jira project `ABC`.
- Read-only data to retrieve: remote commits, issue titles/bodies/comments, labels, links, or status history.
- Commit/date window and any tracker-specific filter.
- Why the local evidence is insufficient.

Approval for a Git fetch does not approve GitHub issues. Approval for GitHub issues does not approve Jira, Linear, Sentry, or another service. Do not post, comment, edit, transition, or otherwise mutate external data in this skill.

Query only the approved range and project. Minimize copied ticket content: retain IDs, concise facts, and links or citations needed to support findings; do not reproduce unrelated personal or sensitive content.

For tracker correlation:

- First use explicit ticket IDs in commits, merge commits, changelogs, or local metadata.
- Then use exact PR/commit links supplied by the tracker.
- Treat title or keyword similarity as a tentative match requiring an explanation and low confidence.
- Do not count the commit and its linked ticket as two separate bugs.

## Step 4 — Identify likely bug fixes

Build a candidate list from the selected commits. Signals include:

- Explicit bug, regression, incident, revert, hotfix, or ticket references in the commit message.
- A test changed from reproducing a failure to asserting corrected behavior.
- A code change that restores an invariant, adds missing validation, corrects an interface mismatch, fixes ordering/lifecycle behavior, or handles a previously failing path.
- A revert or follow-up correction shortly after an earlier change.

For each candidate, inspect the commit diff and enough surrounding code to understand ownership and behavior. When locally available, inspect the parent state and the introducing change. Do not use message keywords as proof.

Classify confidence:

- **Confirmed:** diff plus test, ticket, incident evidence, or explicit reproducible behavior establishes a defect.
- **Likely:** diff clearly corrects behavior, but no independent reproduction or linked evidence exists.
- **Tentative:** message or shape suggests a fix, but the defect cannot be established from available evidence.
- **Excluded:** refactor, formatting, dependency maintenance, typo, or feature work with no demonstrated defect.

Keep tentative candidates out of frequency totals, but list material ones under evidence gaps. When a large squash commit combines features and fixes, count distinct evidenced defects, not files changed; otherwise count it once and note the ambiguity.

## Step 5 — Classify causes

Assign one primary **proximate defect** and one primary **escape factor** per confirmed or likely bug. Add secondary labels only when evidence requires them.

### Proximate defect taxonomy

- `state-invariant` — an invalid state was representable or a required transition was unenforced.
- `interface-contract` — caller/provider, API, type, schema, serialization, or version assumptions disagreed.
- `input-validation` — malformed, missing, boundary, or untrusted input crossed a boundary unchecked.
- `error-handling` — failure was swallowed, misclassified, retried incorrectly, or surfaced too late.
- `concurrency-ordering` — race, stale read, non-atomic update, idempotency, or ordering failure.
- `lifecycle-resource` — initialization, cleanup, cancellation, ownership, caching, or resource lifetime error.
- `data-migration-config` — schema migration, persisted data, configuration, environment, or rollout mismatch.
- `integration-dependency` — external service or dependency behavior was assumed incorrectly.
- `logic-edge-case` — domain logic or a boundary case was wrong without a narrower category.
- `requirements-ambiguity` — implemented behavior matched one plausible interpretation but not the intended contract.

### Escape factor taxonomy

- `missing-automated-test` — the relevant behavior or regression path was not tested.
- `weak-test-oracle` — tests ran but assertions, fixtures, or mocks could not detect the defect.
- `missing-static-constraint` — types, schemas, linters, or compile-time checks allowed the mismatch.
- `missing-runtime-guard` — a boundary lacked validation, assertion, or fail-fast behavior.
- `unsafe-api-design` — the interface made incorrect use easy or valid use difficult.
- `observability-gap` — telemetry or diagnostics could not reveal or localize the failure.
- `rollout-process-gap` — review, migration sequencing, compatibility, canary, or release controls missed it.
- `documentation-discovery` — correct guidance existed or was needed but was absent, stale, or hard to find.
- `unknown` — evidence cannot support a stronger conclusion.

Do not use `documentation-discovery` merely because docs could be added after any bug. Show that missing or undiscoverable knowledge contributed to the defect.

## Step 6 — Find recurring patterns

Aggregate by cause, subsystem, boundary, and escape factor. A pattern is:

- At least two independently evidenced bugs with the same underlying cause or failed control; or
- One severe bug exposing an enforceable invariant whose absence creates continuing material risk.

Avoid false precision. Report raw counts and confidence rather than percentages for small samples. Separate:

- Bugs fixed inside the selected window.
- Bugs introduced inside the selected window, when introduction is known.
- Historical bugs merely referenced or backported in the window.

Check whether several commits repair the same incident; group them as one bug family and retain the commit sequence as evidence.

## Step 7 — Design prevention

For each pattern, recommend the highest feasible rung of this hierarchy:

1. **Eliminate the state or path:** remove the unsafe option, unify duplicate sources of truth, make transitions atomic, or derive values rather than synchronize them.
2. **Constrain the contract:** use types, schemas, database constraints, exhaustive matching, capability-based APIs, or compatibility checks.
3. **Enforce automatically at runtime or CI:** boundary validation, invariant assertions, migration checks, lint rules, generated artifacts, or release gates.
4. **Add the smallest regression coverage:** test the invariant at the lowest useful layer, plus integration coverage only where the boundary caused the bug.
5. **Improve observability or rollout controls:** actionable errors, metrics, canaries, compatibility staging, or rollback checks.
6. **Document durable knowledge:** only facts and decision rules that code or automation cannot express.
7. **Add agent guidance:** only a short repository-wide rule or navigation link when coding agents repeatedly need it.

For each recommendation include:

- Exact bug family and evidence it addresses.
- Proposed owner/file or the narrowest likely location.
- Why this rung is stronger than documentation alone.
- Expected prevention mechanism.
- Cost/blast radius and any behavior or migration risk.
- A verification method proving the control catches the historical failure mode.

Do not prescribe a specific code change without reading the current implementation. If implementation evidence is insufficient, recommend an investigation or state the desired invariant instead of inventing an API.

## Step 8 — Place documentation with progressive disclosure

Before recommending documentation, inspect what already exists and follow repository conventions.

Use this placement order:

1. Documentation or tests adjacent to the subsystem that owns the behavior.
2. A focused page under the repository's established `docs/` structure for cross-cutting concepts, operational runbooks, or architecture decisions.
3. An existing docs index or architecture page linking to the focused page.
4. `CLAUDE.md` or `AGENTS.md` only for a concise repository-wide rule or a link that helps an agent discover the focused guidance.

Never copy the same detailed rule into multiple instruction files. Prefer a stable link and one source of truth. Do not recommend creating a new document when an existing owned page is the natural home.

A good agent-file recommendation looks like:

```markdown
- Changes to database migrations must preserve mixed-version compatibility; see [migration compatibility](docs/engineering/migrations.md).
```

The linked page owns the actual compatibility matrix, examples, rollout order, and verification commands.

## Step 9 — Report, then offer changes

Print or write:

```markdown
# Bug pattern analysis

## Scope and evidence
- Repository/ref: <ref at SHA>
- Window: <last N | normalized since/until and timezone>
- History: <all reachable | first-parent>
- Sources: <local Git, local remote-tracking ref, approved external sources>
- Completeness: <complete | shallow/truncated, with exact limitation>
- Candidates: <confirmed>, <likely>, <tentative>, <excluded>

## Headline
<Two to five sentences naming the dominant patterns and strongest preventive action.>

## Recurring patterns
### <Pattern>
- Evidence: <commits/tickets and concise observed behavior>
- Proximate defect: <category>
- Escape factor: <category>
- Confidence: <high/medium/low and why>
- Recurrence: <distinct bug families, not raw commit count>

## Recommended prevention, ranked
1. **<Make the class impossible where feasible>**
   - Addresses: <patterns>
   - Location: <file/module/system>
   - Mechanism: <invariant or control>
   - Verification: <test/check that fails on historical case>
   - Cost/risk: <brief assessment>

## Documentation and guidance changes
| Target | Change | Why here | Link/navigation change |
|---|---|---|---|

## Evidence gaps
<Unknowns, tentative candidates, unavailable history, or tracker limitations.>
```

Rank recommendations by preventive strength, recurrence, impact, confidence, and implementation cost. A lower-cost automated constraint generally outranks a broad documentation campaign.

Do not edit code, tests, docs, `CLAUDE.md`, or `AGENTS.md` as part of the audit. After presenting the report, ask which recommendations the user wants applied. If asked to implement them, follow the repository's normal planning, implementation, and verification workflow.

## Quality bar

- Every classified bug cites a commit and, when used, a ticket or incident record.
- Every root-cause claim points to diff or source evidence, not only prose metadata.
- Counts represent distinct bugs or bug families, not commits, files, or ticket duplicates.
- Every recommendation identifies the historical failure it would catch and how to verify that.
- The report says when shallow history, squash commits, missing tickets, or date-field mismatch limits confidence.
- External access is always preceded by source-specific confirmation.
- Agent guidance remains a small navigation and policy surface, never the dumping ground for subsystem knowledge.
