---
name: pressure-testing-scope
description: >-
  Pressure-tests PRDs, technical design documents, and implementation plans to
  identify scope that should be kept, cut, deferred, or justified with
  evidence. Produces the minimum coherent scope while preserving the stated
  outcome and essential product, operational, security, migration, and
  compliance constraints. Use before implementation when reviewing proposed
  features, architecture, rollout work, or roadmap commitments. Triggers
  include "pressure-test the scope", "pressure test this PRD", "cut scope",
  "what can we defer", "is this over-scoped", and "find the minimum coherent
  scope".
---

`/pressure-testing-scope` audits a proposed body of work before implementation. It asks one question of every commitment in the document:

> If this were removed or deferred, would the document still achieve its stated outcome safely?

The output is a scope decision, not a general document review. Recommend what to keep, cut, defer, or substantiate, then render the smallest coherent version worth delivering.

## When to use

- A PRD contains more features, audiences, variants, or launch requirements than the team may need initially.
- A technical design document proposes components, abstractions, dependencies, compatibility layers, migration machinery, or operational infrastructure before implementation begins.
- An implementation plan may contain speculative steps or work that does not advance an acceptance criterion.
- The user wants to reduce delivery risk, time, or conceptual surface without losing the intended outcome.

## When not to use

- The user wants to discover or fully specify every unresolved decision. Use `/grill-me`.
- The user wants an executable coding plan. Use `/prep`.
- Code already exists and the user wants an over-engineering review. Use `/ponytail-review`.
- The user wants correctness, security, performance, or prose review of the document. Those are separate review lenses.
- The artifact has no discernible outcome and the user will not supply one. Scope cannot be judged without knowing what it is meant to accomplish.

## Boundaries

- Smaller is not automatically better. Preserve the minimum coherent and safe outcome, not the minimum number of bullets.
- Do not classify security, privacy, compliance, accessibility, data integrity, migration safety, rollback, or necessary observability as optional merely because they are non-functional.
- Do not add desirable features under the guise of finding missing scope. Flag an omission only when the retained scope would otherwise be unsafe, incoherent, or unverifiable.
- Do not turn the review into line editing, architecture review, or a generic list of risks.
- Do not rewrite or modify the source artifact unless the user explicitly asks after reviewing the report.
- Judge the commitments the document actually makes. Do not penalize it for hypothetical future requirements.

## Process

### 1. Locate and calibrate the artifact

Read the artifact the user names or provides. If they identify a local file, read the whole relevant document rather than isolated excerpts. Record its path and use heading or line references in findings.

Identify from the document:

- stated outcome and target user or operator
- success criteria
- release, phase, or time horizon
- explicit non-goals
- non-negotiable product, operational, security, migration, and compliance constraints
- downstream decision this document is intended to support

Do not start classifying scope if the intended outcome is absent or materially ambiguous. Ask one batched set of only the questions needed to establish the outcome, success signal, horizon, and non-negotiable constraints. Do not conduct a broad design interview.

Treat constraints asserted in the artifact as real unless they contradict available evidence. If a local codebase or linked source can verify a factual claim, inspect it rather than asking the user.

### 2. Build the scope inventory

Extract every meaningful commitment, including hidden commitments implied by the prose. Group them at a comparable level of detail.

For a PRD, inspect:

- target users, jobs, and use cases
- workflows and feature variants
- platforms, integrations, and compatibility promises
- launch, rollout, support, and measurement requirements
- customization, configurability, and future-facing extensibility

For a technical design document, inspect:

- services, components, data stores, queues, and APIs
- abstractions, extension points, and configuration surfaces
- dependencies and new operational machinery
- compatibility paths, migrations, backfills, and rollout stages
- failure handling, rollback, observability, and test infrastructure

For an implementation plan, inspect:

- steps that do not advance an acceptance criterion
- speculative refactors and cleanup
- sequencing constraints and parallel workstreams
- new helpers, adapters, files, or layers proposed for one use
- optional validation or polish presented as required delivery scope

Separate independent commitments. Do not hide several decisions inside one inventory item.

### 3. Pressure-test each commitment

Apply these tests in order:

1. **Outcome dependency** - Which stated outcome or essential constraint fails without it?
2. **First coherent release** - Must it exist in the first useful version, or can it follow after evidence from real use?
3. **Evidence** - Is its value supported by requirements, user evidence, measured risk, or an external obligation, or merely asserted?
4. **Cheaper substitute** - Can an existing capability, manual step, narrower interface, or operational procedure deliver the required outcome?
5. **Coupling multiplier** - Does it create more platforms, states, integrations, migrations, support paths, or permanent promises elsewhere?
6. **Reversibility** - Is deferral cheap and reversible, or would omitting it now force destructive rework later?
7. **Coherence and safety** - Would removing it make the retained product misleading, unsafe, inoperable, or impossible to verify?

Classify each commitment exactly once:

- **KEEP** - Required for the stated outcome or an essential constraint in this phase.
- **CUT** - Does not materially advance the outcome, duplicates another commitment, or introduces unjustified permanent surface.
- **DEFER** - Valuable but unnecessary for the first coherent release; later evidence can determine whether to build it.
- **NEEDS EVIDENCE** - Plausibly valuable, but the document does not justify its cost well enough to commit. Name the evidence that would resolve it.

Record **MISSING CONSTRAINT** separately when the retained scope would be unsafe, incoherent, or unverifiable without it. This is not permission to grow the product; propose the smallest constraint or safeguard that closes the gap.

When uncertain between KEEP and DEFER, prefer DEFER only if the omission is reversible and the first release remains coherent. When uncertain because a factual premise is unverified, use NEEDS EVIDENCE rather than pretending the item is unnecessary.

### 4. Check the proposed reduction as a whole

After classifying individual commitments, test the reduced set end to end:

- Can the target user complete the primary job?
- Can success be measured against the stated criteria?
- Can operators deploy, observe, recover, and roll it back to the degree the design requires?
- Are migrations and compatibility obligations still safe?
- Do retained commitments depend on anything marked CUT or DEFER?
- Is the result a coherent release, or only disconnected fragments?

Promote the minimum necessary item if a cut creates a real hole. State why. Do not preserve surrounding optional machinery.

### 5. Report

Return the report in the conversation. Do not write a file unless the user asks.

Use this format:

```text
Scope pressure test: <artifact>

Verdict: LEAN | REDUCIBLE | OVER-SCOPED | CANNOT JUDGE
Potential reduction: <N> of <M> commitments cut or deferred

Stated outcome
<One concise restatement. Note any ambiguity that affects confidence.>

Minimum coherent scope
1. <retained commitment>
2. ...

Decisions
KEEP
- <location> - <commitment>. Required because <specific outcome or constraint>.

CUT
- <location> - <commitment>. Remove because <reason>. Replace with <nothing or cheaper substitute>.

DEFER
- <location> - <commitment>. Reconsider when <specific evidence or trigger exists>.

NEEDS EVIDENCE
- <location> - <commitment>. Commit only if <specific evidence>.

Missing constraints
- <location or affected section> - <smallest safeguard required and why>.

Resulting tradeoffs
- Gain: <delivery, complexity, risk, or cost reduction>
- Give up: <capability or promise removed from this phase>
- New risk: <risk introduced by the reduction, or "none identified">

Open decisions
- <only decisions that prevent a confident scope call>
```

Omit empty classification sections. For `CANNOT JUDGE`, stop after naming the missing outcome or constraints and asking the minimum questions needed.

## Verdicts

- **LEAN** - No meaningful cut or deferral preserves the stated outcome and constraints.
- **REDUCIBLE** - Some commitments can be removed or deferred without changing the core proposition.
- **OVER-SCOPED** - The document contains substantial speculative or weakly justified commitments that materially increase delivery or permanent complexity.
- **CANNOT JUDGE** - The outcome, horizon, or essential constraints are too ambiguous to distinguish necessary scope from optional scope.

## Quality bar

- Cite the artifact for every scope decision. Use `path:line` for local files and section names for pasted documents.
- Tie every KEEP to a stated outcome or essential constraint. "Seems important" is not sufficient.
- Tie every CUT to a concrete deletion or cheaper substitute. Avoid vague advice such as "consider simplifying."
- Give every DEFER and NEEDS EVIDENCE item a specific reconsideration trigger.
- Quantify commitments, not document lines. A shorter document can still encode the same scope.
- State tradeoffs honestly. A reduced scope is a choice, not a free improvement.
- If there is nothing worth removing, say so. Do not manufacture findings to make the review appear useful.
- Keep the report concise enough to support a decision. The source document remains the detailed record.
- Plain text only. No emojis.
