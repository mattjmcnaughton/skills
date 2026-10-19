---
name: run-waves
description: Repeatedly coordinates run-wave batches within an agreed ticket scope and limits, preserving permissions and resumable progress. Use for sustained multi-wave execution or resuming that run.
---

# Run successive waves

Own continuation and stopping decisions. `/run-wave` owns each bounded batch;
`/ship-ticket` owns implementation. Read the installed sibling
`ship-ticket/references/run-contract.md` before execution. Resolve it from the
real skill directory's parent, not the consuming repository. Require both worker
skills; report missing dependencies rather than silently skipping their contracts.

## Agree the run before execution

Accept a supplied ticket list or bounded selector such as a milestone or label,
repository, optional project guide, delivery target, and concurrency limit.
Resolve the selector to a finite list and record it; newly created or newly
matching tickets are out of scope unless the user explicitly extends the run.
Do not interpret "keep going" as permission to consume the whole tracker.

Ask upfront for all proposed external-write permissions under the run contract.
Record grants, denials, destinations, and the selected ticket set in the outer
task's `plan.md`. No permission means no external writes in any wave. Pass the
record down; do not ask again for declined actions each wave. A supplied explicit
current-run authorization can be reused, but never inferred from credentials or
the requested delivery target.

Agree any time, ticket, or wave budget and the worker limit (default at most two
implementers). If no extra budget is supplied, the finite selected set bounds the
run. Clarify whether a deadline is a dispatch cutoff or requires stopping active
work; default to a dispatch cutoff with safe checkpointing of active workers.
Keep all progress in the outer diary and per-ticket task records. This skill is
active-session execution, not a scheduler or a promise to survive process loss.

## Repeat deliberately

1. Reconcile actual code, refs, ownership, and delivery with the diary. On resume,
   inspect surviving workers and uncertain external writes before doing anything
   twice. Carry forward permissions only for this same scoped run.
2. Refresh dependency readiness and priorities within the selected set. A ticket
   blocked on policy, approval, or failed acceptance stays blocked until its
   recorded condition changes. Do not retry unchanged failures indefinitely.
   Exclude already implemented and verified tickets from new implementation
   waves even if publication is pending; resume only their remaining delivery
   steps when permitted, never rebuild them to satisfy the delivery target.
3. Choose one finite, independent wave under the remaining budget. Call `/run-wave`
   with the exact integration base, project policy, permissions, delivery owner,
   worker limit, and handoff destination. Do not overlap successive waves.
4. Wait for its workers and integration outcome while handling permitted work.
   Verify its report and record completed, blocked, and failed tickets plus the
   new verified baseline. Do not advance the baseline past failed integration.
5. Continue only if another selected ticket is ready and limits allow it. Use
   locally integrated prerequisites when appropriate, but retain publication
   blocks separately: local readiness is not completion of a PR/merge target.

If a ticket needs a decision, preserve it and continue independent authorized
work. Do not invent policy, lower acceptance, broaden permissions, or add tickets
to keep workers busy. Honor stage-specific human approval gates; continuous
execution is not permission to answer them for the user.

## Stop and preserve

Stop when the selected set reaches the delivery target, a budget is exhausted,
the user stops the run, integration cannot safely advance, or no remaining ticket
can progress without changed inputs/approval. A partial run is not a completed run.
Do not poll indefinitely, automatically restart failed workers, install schedules,
or continue in another thread without authorization.

On stop, cease dispatch, checkpoint active work safely, and preserve recovery
material under the run contract. Report the selected scope and permission summary,
per-ticket delivery states, integrated baseline, verification/evidence limitations,
external writes performed, remaining blockers/approvals, budget usage, and exact
resume action. Explicitly disclose anything retained only in a disposable
environment. Do not clean up branches/worktrees or publish recovery artifacts
without the required authority.
