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

Select tickets whose dependencies are implemented on the exact integration base.
Do not place a prerequisite and its dependent in the same parallel batch; defer
the latter until the prerequisite is integrated and verified. Do not infer code
availability from ticket closure. Choose independent work; serialize shared-file,
schema/migration, or service changes when isolation cannot prevent conflicts.

One orchestrator owns assignments. Check existing claims before assigning work;
ticket comments are not atomic locks. In local-only mode, record local ownership
without pretending other orchestrators can see it. Conflicting external ownership
must be resolved before work; do not assume a stale claim is abandoned.

## Dispatch and collect

Give each `/ship-ticket` worker the ticket and acceptance criteria, authoritative
documents, exact base, absolute worktree/branch, allowed scope, permission record,
delivery owner, and retained handoff destination. Initialize or assign its task
workspace without overwriting existing work. One writer per worktree; isolate
databases, ports, browser sessions, migration identifiers, and generated artifacts.

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

Inspect each returned diff and evidence, not just the success summary. Missing
review, failed checks, or unmet acceptance remain explicit. Preserve checkpoints
and transfer recovery material before releasing a worker environment. A blocked
worker does not make the entire wave successful.

## Integrate and stop

Integrate accepted candidates locally in dependency order on a dedicated branch,
preserving unrelated work. Inspect conflicts and migration ordering; repeat
affected review and checks after resolutions. Run combined verification on the
exact integrated candidate; isolated green results do not prove compatibility.
Refresh affected proof after substantive integration changes. If integration
fails, retain candidates and stop publication until corrected and reverified.

Choose the publication unit before external writes: per-ticket PRs or a wave PR,
following repository policy and the user's chosen target. Record this in the plan.
Use `/create-pr` and `/merge-pr` only within the grant and their own approval/CI
gates. For per-ticket delivery, revalidate each changed head against its actual
base; combined local checks do not replace required CI on each PR. Do not mix
publication strategies or close tickets merely because candidates are integrated
locally. Preserve provenance from each ticket to the delivered revision.

Report each ticket's state, integrated revisions, combined checks, evidence gaps,
external actions, retained work, blockers, and next ready tickets. Stop after this
wave, including when partially blocked. Suggest `/run-waves` for sustained work;
do not start a second wave automatically.
