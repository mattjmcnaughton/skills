---
name: run-wave
description: Coordinates one bounded wave of dependency-ready tickets with parallel ship-ticket workers, isolated workspaces, and combined verification. Use to execute or resume a single ticket batch.
---

# Run one wave

Own selection, worker coordination, and integration for one finite ticket batch.
`/ship-ticket` owns each ticket's coding loop; `/run-waves` owns repetition.
Read the installed sibling `ship-ticket/references/run-contract.md` before
execution, resolving it from this skill's real parent directory, not the target
repository. If it or `/ship-ticket` is missing, report the dependency and stop.

## Establish the wave

Accept a finite ticket set or bounded selector, repository, optional project
execution guide, integration baseline, delivery target, and worker limit. Read
applicable guidance, actual tickets, current ownership, worktrees, and refs.
Ask about ambiguous scope. Default to at most two implementers, fewer when memory,
shared services, or overlapping changes make concurrency unsafe.

Before dispatch, ask upfront for external-write permissions under the run
contract, unless the parent supplies the user's explicit current-run decision.
Without permission, perform no external writes, including remote ticket claims.
Record the wave and permissions in the outer task's plan and diary, using the
existing task-workspace ignore checks. A nested wave reuses the parent's record.

Assess dependency readiness on the exact integration base. Shared prerequisites
identified below may establish a new verified base before dependent dispatch.
Do not place a prerequisite and its dependent in the same parallel batch; defer
the latter until the prerequisite is integrated and verified. Do not infer code
availability from ticket closure. Choose independent work; serialize shared-file,
schema/migration, or service changes when isolation cannot prevent conflicts.

One orchestrator owns assignments. Check existing claims before assigning work;
ticket comments are not atomic locks. In local-only mode, record local ownership
without pretending other orchestrators can see it. Conflicting external ownership
must be resolved before work; do not assume a stale claim is abandoned.

## Bring shared work forward

Before dispatch, compare the selected tickets for repeated research, repository
discovery, setup, fixtures/test infrastructure, and implementation
prerequisites. Reuse applicable parent findings and run-level choices under the
run contract. Research common code paths, architecture, dependency behavior, and
implementation patterns once; record source paths/revisions, findings,
commands/setup results, applicable environments, and gaps in the existing outer
plan. Keep this bounded to questions the selected tickets need, not a
repository-wide survey.

Perform common setup once where it is safely reusable, retaining worker-specific
isolation and readiness checks. A shared implementation prerequisite needs an
explicit scope, owner, dependent tickets, and verification in the plan. Complete
it through `/ship-ticket` and integrate and verify it before dependent workers
start; do not have parallel workers edit the same prerequisite or bypass
review/acceptance by calling it setup. If needed work exceeds selected scope,
ask rather than adding a ticket or speculative cleanup. Unrelated ready tickets
need not wait for research or prerequisites they do not use; preserve the worker
limit and single integration owner.

Unless the parent supplied it, choose the publication unit (per-ticket PRs or a
wave PR) before dispatch, following repository policy and the user's target, and
record it with the run contract's proof placement. Wave placement defers only
full `/prove`; do not defer cheap useful checks merely to concentrate all
failures at the end.

## Prepare ahead without starting implementation

Offer the run contract's prep-ahead choice when parallel agents are available.
When enabled, dispatch `/prep` in read-only mode for a selected ticket B while
ticket A builds, even if B has no build slot yet. A not-yet-ready dependent may
be researched, but not implemented or counted as part of this wave's build batch.
In `/run-waves`, it must belong to the finite selected set; otherwise ask before
adding a ticket outside this invocation's scope.

Give the prep worker the exact ticket, inspected revision, dependency
assumptions, read-only boundary, relevant shared research references, and
handoff destination. Use a stable snapshot or isolated read-only copy, not a
writer's changing checkout. The worker returns provisional research; the
orchestrator alone persists it in the existing task records. Keep prep workers
within their separate limit and machine capacity. A completed prep does not
claim a writer slot, satisfy dependency readiness, or authorize build. When B
becomes build-ready, its owner revalidates the provisional plan against the
actual assigned base and completes normal `/prep`. Preserve useful research and
reopen only decisions invalidated by changed code or dependencies.

## Dispatch and collect

Give each `/ship-ticket` worker the ticket and acceptance criteria,
authoritative documents, relevant shared research/setup references, run-level
choices, exact verified base (including completed prerequisites), absolute
worktree/branch, allowed scope, permission record, workflow, proof
placement/owner, provisional prep if any, delivery owner, and retained handoff
destination. Initialize or assign its task workspace without overwriting
existing work. One writer per worktree; isolate databases, ports, browser
sessions, migration identifiers, and generated artifacts.

Use supported agent facilities for independently owned workers. New environments
must receive the exact code and required setup: remote branch names and commit
IDs do not transfer local changes. If parallel workers are unavailable, offer a
serial execution of the same finite batch and report the concurrency limitation;
do not claim parallel execution or spawn agents through unsupported interfaces.

Keep publication with the orchestrator by default. Workers return local candidates
and stage results; they must not separately open PRs or merge the same changes.
Route human approval gates back to the user, preserving the child's instructions.
Let independent workers continue when one ticket is blocked. Do not replace a
blocked ticket by expanding this wave's agreed scope.

Inspect each returned diff and relevant evidence, not just the success summary.
Use compact handoffs under the run contract; deepen investigation for missing or
contradictory evidence, conflicts, or cross-ticket interactions rather than
repeating the worker's research and independent review. Distinguish policy-omitted
lite stages and deferred wave proof from unexpectedly missing stages; failed
checks or unmet acceptance remain explicit. Preserve checkpoints
and transfer recovery material before releasing a worker environment. A blocked
worker does not make the entire wave successful.

## Integrate and stop

Integrate candidates that satisfy their pre-integration stages, including
reviewed full-gate-passing candidates whose only pending acceptance work is
parent-owned wave proof, locally in dependency order on a dedicated branch.
Proof-pending integration is provisional, not acceptance or a verified baseline
for the next wave. Preserve unrelated work. Inspect conflicts and migration
ordering; repeat affected review and checks after resolutions. Run combined
verification on the exact integrated candidate; isolated green results do not
prove compatibility. Use the recorded verification schedule and `/prep`'s reuse
policy, but run combined checks for a new integrated candidate. Refresh
invalidated proof under `/prove`'s policy and verify ticket-level acceptance
before publication or advancing the verified baseline. If integration fails or
required acceptance remains pending, retain candidates and stop publication
until corrected and reverified.

With wave proof selected and full-mode tickets included, run `/prove` once on
the integrated candidate after combined checks and integration fixes, choosing
each claim's counterfactual under `/prove`'s wave-proof rules. Supply all
full-mode tickets' acceptance claims, preserving ticket identity and wording,
plus claims introduced by integration. Identify lite tickets and their omitted
stages explicitly; mixed waves do not acquire a claim of full review from this
proof. Follow `/prove`'s artifact and mutation rules when the wave baseline
cannot host a check; setup failure is not behavioral failure. Obtain its
concrete capture-plan/tool approvals here; choosing wave placement did not
approve capture. Map actual verdicts back to each ticket and retain gaps as
blockers where acceptance is unmet. If the wave is partial, prove only the
included candidates and leave excluded tickets pending. No candidate awaiting
required wave proof may be published or marked local-ready.

Use the publication unit recorded before dispatch; do not silently change it.
Use `/create-pr` and `/merge-pr` only within the grant and their own approval/CI
gates. For per-ticket delivery, revalidate each changed head against its actual
base; combined local checks do not replace required CI on each PR. Do not mix
publication strategies or close tickets merely because candidates are integrated
locally. Preserve provenance from each ticket to the delivered revision.

Report each ticket's state, integrated revisions, combined checks, evidence gaps,
external actions, retained work, blockers, and next ready tickets. Stop after this
wave, including when partially blocked. Suggest `/run-waves` for sustained work;
do not start a second wave automatically.
