---
name: draft-api-client
description: >-
  Interview the user about an API client they want to build, then draft a plan
  covering four deliverables: a clean functional client, contract tests, a fake
  client that emits realistic data from the spec, and an opt-in focused
  integration test. Accepts an OpenAPI spec file, a docs URL, pasted spec text,
  or a GitHub reference repo as input. Language-agnostic. Use when the user
  wants to add or replace a wrapper around an HTTP API, integrate a new
  third-party service, or stand up a typed SDK for an existing backend. Triggers
  include "draft an API client", "wrap this API", "plan a client for", "write
  an SDK for", "integrate with <service>". Produces a plan only — hand off to
  /build to execute it.
---

`/draft-api-client` is a planning skill. One conversation, one artifact: a plan that `/build` can execute to produce a clean client, contract tests, a fake, and a focused integration test for a chosen HTTP API.

The skill does not generate code. It does not pick a language for the user — it reads the host repo (or asks) and mirrors what the project already uses.

## When to use

- User wants to wrap a new third-party API.
- User wants to replace an ad-hoc client (`requests.get` scattered through the codebase) with a structured one.
- User has an OpenAPI spec and wants a real client + a fake + tests in one pass.
- User wants to integrate with a service and asks "where do I start".

## When not to use

- The user wants the code generated right now — this skill stops at the plan. Run it, then `/build`.
- The user wants a one-off script that calls one endpoint — overkill; just write the call.
- The wrapper already exists and the user wants to extend it — use `/prep` so the existing client is part of the research.

## Inputs the skill accepts

Ask the user which form their spec/docs are in. Support any of:

1. **OpenAPI / Swagger spec file** — local path to `.json` or `.yaml`. Read it directly.
2. **Docs URL** — public docs page. Fetch via `/fetch-context` (`https://r.jina.ai/<URL>`). Confirm the URL before fetching; never wrap a URL that carries credentials.
3. **Pasted spec or docs text** — user pastes into the conversation.
4. **GitHub reference repo** — e.g. an existing client in another language, or the service's own server repo. Use `/fetch-context` to shallow-clone into `.agentic/sources/<repo>/`, then Read/Grep against it.

If the user has more than one source (a spec *and* a docs URL, say), take all of them — they complement each other.

If the user has no spec at all, stop and say so. This skill needs a concrete contract; an interview alone cannot substitute for it.

### Spec triage

Before interviewing, skim the spec and surface:

- The API's base URL(s) and auth scheme (Bearer, API key, OAuth2, mTLS, none).
- Total operation count, grouped by tag/resource.
- Any pagination conventions (cursor, offset, page tokens) and rate-limit headers.
- Anything unusual: long-poll endpoints, streaming/SSE, file uploads, webhook callbacks.

Use this to make interview questions concrete — "the spec lists 47 operations across `accounts`, `transactions`, and `webhooks`; which of those does this client need?" beats "what scope?".

## The interview

Conversational, not a flat script. Build on answers. Cover at minimum:

**Scope.** Full coverage of the spec, or a subset? If subset: which resources, which operations, which auth modes. List the cuts explicitly so the plan can name them as out-of-scope.

**Language and runtime.** Detect from the host repo first (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`, etc.). If ambiguous or absent, ask. Note the version constraint that matters (e.g. Python 3.11+, Node 20+).

**HTTP client and test framework conventions.** Look for an existing client in the repo to mirror. Ask only if there is no existing pattern. Examples: `httpx` vs `requests` in Python; `fetch` vs `axios` vs `undici` in TS; `net/http` vs `resty` in Go. Same for tests: `pytest`, `vitest`, `go test`, `rspec`, etc.

**Auth source.** Where do credentials come from at runtime — env var, config file, secret manager, caller-supplied? The plan needs to name this so contract tests don't accidentally bake real creds in.

**Error model.** Should the client raise typed exceptions per error class, return result/either types, or surface raw HTTP errors? Mirror repo convention if one exists.

**Sync vs async.** Match the host repo. If the repo is mixed, ask.

**Pagination, retries, rate-limit handling.** Which of these should the client own vs leave to the caller? Default: the client owns pagination (returns an iterator/stream) and respects `Retry-After`; it does not silently retry on 5xx without the caller opting in.

**Fake-client realism.** The fake's job is to emit data that exercises the shapes a real caller will see. Walk the spec's schemas, not just sample one value per field. Ask the user:

- Determinism — seeded RNG so tests don't flake. Almost always yes.
- Coverage gallery — should the fake expose a `realistic_examples(operation)` helper that returns a *gallery* of cases: typical, each `enum` branch, each `oneOf`/`anyOf` arm, boundary values (`min`/`max`, `minLength`/`maxLength`), format-specific (email, uuid, date-time, uri), `nullable` → include null, optional fields → both present and absent. This is the high-value default.
- Failure injection — caller forces a specific error on the next call or for a given operation.
- Latency simulation — usually skip; flag the option.

**State model.** Default to **stateless**: every call generates fresh spec-conformant data. Climb the ladder only if the user's downstream code needs it:

1. **Stateless** (default) — covers most unit testing. No memory between calls.
2. **Scripted scenarios** — caller pre-registers `(request matcher) -> response` pairs in order. Cheap to implement; handles "POST then GET returns the same thing" without an in-memory store.
3. **In-memory store** — fake maintains a keyed store and `POST` mutates it so subsequent `GET`s reflect the write. Only worth it when callers genuinely orchestrate multi-step CRUD flows against the fake.

Pick the lowest tier that meets the need and record the choice in the plan.

**Integration-test surface.** Which one or two end-to-end flows are worth a real-network test? Default to the smallest set that proves "the client can talk to the real service at all." Confirm the credentials and test account/sandbox the integration will hit.

**Out of scope.** What is the user explicitly *not* asking for? Common cuts to confirm: webhook receiver, retry middleware beyond `Retry-After`, OpenTelemetry/metrics, caching layer, CLI wrapper, generated docs site.

## The four deliverables — what the plan must cover

Every plan this skill produces specifies all four. If the user wants to drop one (e.g. "skip the fake"), record it as an explicit cut, with the reason, in the Out-of-scope section. Do not silently omit.

### 1. Clean, functional client

Thin wrapper over the HTTP layer. Each operation maps one-to-one to a spec operation. No business logic, no caching, no orchestration across endpoints.

The plan should specify:

- Module/package layout (one file per resource, or one flat module — match repo convention).
- Type definitions for requests and responses, sourced from the spec.
- Single configuration entry point: base URL, auth, timeout, custom HTTP client injection.
- Pagination shape (iterator, async iterator, stream, page-at-a-time).
- Error mapping: which HTTP status maps to which exception/result variant.
- What is explicitly *not* in the client (retries beyond `Retry-After`, observability, etc.).

### 2. Contract tests

Verify the client's *request shape* and *response parsing* against the spec, without hitting the network.

The plan should specify:

- Fixture source: spec-derived sample payloads, recorded responses (e.g. from a sandbox), or schema-driven generation.
- For each in-scope operation: one test that builds the request and asserts URL, method, headers, query params, body match the spec.
- For each in-scope operation: one test that feeds a spec-conformant response into the client and asserts the parsed result.
- Schema-conformance assertion: where feasible, validate fixtures against the spec (e.g. `openapi-core`, `ajv`, `kin-openapi`) so a spec drift breaks the test, not just behavior.
- These run in the default test suite. No network, no credentials, no flakiness.

### 3. Fake client

A second implementation of the same client interface that returns realistic, spec-conformant data without any network. Used by downstream code's unit tests, by local dev, and by demos.

The plan should specify:

- Interface parity: a static check or a shared abstract base/trait that both real and fake implement, so swapping is trivial.
- Data generation strategy: walk the spec's schemas to cover the data shapes a real caller will see — `enum` branches, `oneOf`/`anyOf` arms, boundary values from `min`/`max`/`minLength`/`maxLength`, format-specific values (email, uuid, date-time, uri), nullability, optionality. Name the library or approach (`schemathesis` / `hypothesis-jsonschema` in Python, `json-schema-faker` in JS, schema-walker + `gofakeit` in Go, etc.). Note any field-level overrides the user asked for.
- Coverage gallery: expose a `realistic_examples(operation)` helper that returns the full gallery of cases — typical, each enum/oneOf branch, boundary, null, optional present/absent — so contract tests and downstream tests iterate the gallery rather than gambling on one value.
- Determinism: seeded RNG, exposed via the constructor.
- State model: pick the lowest tier that meets the need — **stateless** (default), **scripted scenarios** (pre-registered request/response pairs), or **in-memory store** (POST mutates a keyed store, GET reads it back). Name the tier and the reason.
- Failure injection API: how callers force a specific error on the next call (or for a given operation).
- File location and how downstream code imports it (often a `testing/` or `fakes/` subpackage).

### 4. Focused integration test — opt-in only

A small number of tests that hit the real API. They prove the wire format is right and the auth works. They are not the place to test the full surface — that's contract tests' job.

The plan should specify:

- Opt-in gate: env var (`RUN_INTEGRATION=1`, `INTEGRATION_TESTS=1`) or test tag/marker (`pytest -m integration`, `go test -tags=integration`, `cargo test --features integration`). Match repo convention. The gate must default to off — `npm test`/`pytest`/etc. with no flags must skip these.
- Credentials source: same env vars the production client reads. Document them in plan and in the test file's docstring.
- Sandbox vs production: name which environment the test hits. Refuse to plan against a destructive production endpoint without explicit user confirmation.
- Test scope: one happy-path test per resource the client claims to support. Maybe one auth-failure test. That is usually enough.
- Cleanup: if the test creates data, it deletes it (or the sandbox auto-resets). Name the cleanup strategy.
- CI policy: by default these run on demand, not on every PR. The plan should say so; if the user wants nightly CI runs, capture that as a separate follow-up.

## Output: render then write

When the plan is ready, **render it in the conversation first**. Don't write to disk yet.

Then ask the user where to put it. Suggestions, in order:

1. If `.agentic/<slug>/` exists for the current branch, suggest `.agentic/<slug>/plan.md` (overwrites — confirm) or `.agentic/<slug>/api-client-plan.md` (alongside an existing plan).
2. Else suggest `docs/api-client-plan.md` or `<repo-root>/api-client-plan.md`.
3. Accept any user-supplied path.

Only write after the user confirms a path. If they want to iterate on the plan in the chat first, do that — the file write is the last step, not the first.

## Plan template

```markdown
# API client plan: <service name>

**Spec source(s)**: <file path(s), URL(s), repo(s)>
**Language / runtime**: <e.g. Python 3.11+, TypeScript with Node 20+>
**HTTP client**: <library, with version range>
**Test framework**: <library>
**Async or sync**: <sync | async | both>

## Scope

**In-scope operations**: <list, grouped by resource>
**Out of scope**: <explicit cuts — webhooks, retries, metrics, CLI, etc.>
**Auth**: <scheme + credentials source>
**Pagination**: <strategy>
**Error model**: <typed exceptions | result type | raw HTTP>

## Deliverable 1: client

**Layout**: <files, package structure>
**Types**: <how request/response types are defined and where they live>
**Configuration entry point**: <function/class signature>
**Pagination shape**: <iterator | async iterator | etc.>
**Error mapping**: <table or bullets — status -> error variant>
**Explicitly not in the client**: <list>

## Deliverable 2: contract tests

**Fixture source**: <spec-derived | recorded | generated>
**Per-operation tests**: <request-shape test + response-parse test>
**Schema validation**: <library + how it's wired in>
**Run command**: <e.g. `pytest tests/contract`>

## Deliverable 3: fake client

**Interface parity mechanism**: <abstract base | trait | structural check>
**Data generation**: <library/approach; how the schema is walked; field-level overrides>
**Coverage gallery helper**: <signature of `realistic_examples(operation)` and what it returns>
**Determinism**: <seed source>
**State model**: <stateless | scripted | in-memory> — <reason for the tier choice>
**Failure injection**: <API shape>
**Location**: <import path>

## Deliverable 4: integration test (opt-in)

**Opt-in gate**: <env var or tag>
**Credentials**: <env vars, documented>
**Environment**: <sandbox | production — with confirmation if production>
**Test surface**: <list of flows>
**Cleanup**: <strategy>
**CI policy**: <on-demand | nightly | per-PR>
**Run command**: <e.g. `RUN_INTEGRATION=1 pytest tests/integration`>

## Implementation order (for /build)

1. Types and configuration scaffolding.
2. Single operation end-to-end: client method, fake method, contract test, integration test. Prove the pattern works.
3. Remaining operations, one resource at a time. Each lands with its contract test + fake support.
4. Documentation: README section on real vs fake client and how to run integration tests.

## Open questions

<anything the interview did not resolve — the user should answer these before /build, or /build should pause on them>
```

## Guidelines

- **One spec source is fine; multiple is better.** If the user has both an OpenAPI file and human docs, read both — specs lie by omission, docs lie by being out of date.
- **Detect language and conventions from the repo before asking.** Cuts down on dumb questions and makes the plan immediately fit the project.
- **Never invent endpoints, fields, or types** that are not in the spec. If the user wants something the spec does not describe, surface it as a question — do not paper over it.
- **The fake is interface-compatible with the real client.** That is the whole point. If the plan does not specify *how* parity is enforced, callers will drift.
- **Integration tests default to off.** A test suite that requires real credentials to pass is a broken default. The opt-in gate is non-negotiable.
- **Plain text only. No emojis.** Match the rest of the skills.
