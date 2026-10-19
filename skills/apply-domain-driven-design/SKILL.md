---
name: apply-domain-driven-design
description: Discovers and evolves a domain model in a new or existing codebase, establishes ubiquitous language and invariants, and implements agreed scoped changes. Use when asked to apply DDD, clarify domain boundaries, or refactor code around business behavior.
---

# Apply Domain-Driven Design

Model business behavior first. Introduce DDD patterns only when they clarify or
protect it. This is a standalone discovery-to-implementation workflow, not a
requirement to install a framework or run a particular coding loop.

## Establish the scope

Use the supplied repository and desired outcome. If either is missing, inspect
available guidance and ask only for the missing consequential input, then wait.
An unqualified "apply DDD" starts discovery and recommendations, not a broad rewrite.
Default to one workflow or problem area. If asked for a repository-wide assessment,
map the areas first and propose a bounded implementation slice.

Honor explicit existing authorization to implement a settled scope without asking
again. Acceptance of a model recommendation alone is not implementation permission.
Keep discussion and proposed edits inline unless a document is requested or needed
for the authorized implementation. Reuse existing task artifacts when present.

## Discover intended behavior

Read the constitution, repository guidance, domain vocabulary, relevant product
and architecture documents, code, and tests. Respect their ownership and locations;
do not force a glossary-only `CONTEXT.md` or a new folder hierarchy onto the project.
Treat external examples as evidence, not authority over the user's requirements.

For a new codebase, start from actors, activities, and business scenarios rather
than tables or classes. For an existing codebase, trace the selected workflow from
entry point through rules and persistence. Distinguish intended behavior, observed
implementation, and assumptions. Surface contradictions; neither code nor prose
automatically wins.

Identify terms, identity and lifecycle, commands and outcomes, invariants, ownership,
and external dependencies. Ask one unresolved domain question per turn with a
concrete example, alternatives, and a recommendation; wait for the answer. Honor
a requested chunk size. Track agreed, delegated, pending, and deferred decisions.
Clarify partial answers, continue independent questions around deferrals, and stop
with a recap when only blocked items remain or the user asks to stop.

## Stress-test the model

Use examples and counterexamples that distinguish competing meanings. Probe
rejection, stale state, retry, concurrency, and lifecycle boundaries where relevant.
Derive expected outcomes from agreed rules, not existing implementation formulas.

For example, in a learning product: a Proposal suggests an edit; Apply creates a
Change. If the learner attempts the target lesson before Apply, should the stale
Proposal still be applicable? Resolve what "engaged" means before designing a class.
These are example concepts, not vocabulary to impose on other products.

Define consistency boundaries from what must stay true atomically, not foreign-key
relationships. Distinguish pure rule evaluation from authorization and transactional
enforcement. Name bounded contexts only when meanings or ownership differ; specify
translations between them rather than automatically creating services or databases.

## Propose the smallest useful change

Present the agreed vocabulary and rules, concrete scenarios, and a focused mapping:
rule or concept -> current implementation -> proposed owner/enforcement -> verification.
Include open decisions and evidence gaps. Preserve code that already expresses the
model well; recommending no code change is a valid result.

Prefer a domain name, an explicit transition, or extracting a pure rule over a new
framework. Do not require entities, aggregates, value objects, repositories, domain
events, CQRS, or event sourcing as a checklist. Explain any pattern in terms of
the behavior or invariant it protects. Do not equate DDD with classes or a folder
layout, and do not spread one small change across unrelated modules.

Separate behavior-preserving refactoring from changes to domain policy. Identify
API, persisted-data, and client compatibility effects before implementation. Ask
for any unsettled scope or policy approval and wait; do not silently resolve it
by changing tests to fit current code.

## Implement the authorized scope

Follow repository architecture and testing guidance. Preserve and verify existing
observable behavior before changing rules; use characterization tests where the
current contract lacks coverage. For an agreed behavior change, write a failing
behavioral test first when the repository requires TDD, then implement the rule.
Use independent expectations and boundary cases. Database guarantees require
database-backed checks, not just a fake or a pure-function test.

Update domain documentation and terminology in the affected code, contracts, and
tests together. Preserve established document ownership. Record an ADR only for a
consequential, hard-to-reverse tradeoff whose rationale would otherwise be lost.
Do not rewrite published history, migrate shared data, deploy, publish, or perform
unrelated cleanup without explicit authorization. If reality invalidates an agreed
domain decision, pause that dependent work and ask rather than expanding scope.

## Finish

Report the resulting model and why it fits the scenarios, what changed or should
remain unchanged, verification results and limitations, and unresolved decisions.
State whether work is proposed, locally edited, committed, or published. Stop at
the authorized outcome; do not automatically start another domain or an audit.
