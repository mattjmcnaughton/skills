---
name: ship-ticket
description: Executes one ticket through preparation, implementation, review, evidence, and authorized delivery. Use to ship or resume a single ticket, independently or as a run-wave worker.
---

# Ship one ticket

Own one ticket from understood scope to an explicitly agreed delivery target.
Compose the installed coding-loop skills; do not duplicate their implementations.
Read [the run contract](references/run-contract.md) before execution. It governs
permissions and recovery for this skill, `/run-wave`, and `/run-waves`.

## Establish the task

Accept a ticket URL/identifier or supplied ticket text, repository, optional
project execution guide, and delivery target: local-ready, PR opened, or merged.
Resolve ambiguous tracker identifiers before fetching. Pasted context is valid
when an integration is unavailable; do not require a particular tracker.

Read applicable repository guidance and relevant product/domain documents. Use
the consuming repository's paths, not paths relative to this installed skill.
Inspect current code, worktrees, changes, ticket ownership, and dependencies.
Preserve unrelated work. A closed ticket is not proof its implementation exists
on the selected base; verify the revision and required behavior.

Before execution, ask upfront for external-write permissions as the run contract
requires, unless a parent supplied the user's explicit current-run decision.
Absent permission means no external writes. Agree the target separately from
permissions; if publication is declined, prepare locally and report the gap.

When delegated, verify the brief contains the exact repository, base revision,
ticket, allowed scope, writer ownership, delivery owner, permissions, and recovery
location. The parent owns integration/publication unless it explicitly assigns
those actions to this worker. Do not independently publish a wave candidate.

## Execute the coding loop

1. Use `/create-worktree` for a new isolated task workspace, or reconcile and reuse
   the assigned worktree. Never nest a second worktree just because this is a
   delegated invocation. Initialize `.agentic/<slug>/` using the existing ignore
   and tracked-path checks; preserve ticket context, plan, and diary on resume.
2. Run `/prep`, supplying the approved requirements, project guide, base, delivery
   target, and permission record. Reuse settled decisions rather than inventing
   answers or reopening them. Route genuinely missing decisions to the user.
3. Run `/build`; record checkpoint/TDD choices when answered. Keep its local
   checkpoint/final commit handling distinct from acceptance or publication.
4. Run `/review-suite` on the complete ticket diff against its recorded base.
   Arrange review independent of the implementer using available reviewers and
   allowed delegation tools. Reviewers are read-only or use an isolated copy.
   If independent review is unavailable, report that limitation; do not label
   self-review independent or claim the full workflow completed.
5. Run `/resolve-review`. Record every finding's disposition, including a no-fix
   outcome when appropriate. Recheck meaningful fixes and repeat affected review.
   Unresolved product/policy decisions remain blockers, not guessed requirements.
6. Run `/prove` on the reviewed candidate, honoring its concrete capture-plan and
   tooling approval gates. Record its actual verdicts; distinguish regression
   checks from falsifiable acceptance evidence. If there is no behavioral claim,
   record its not-applicable result. Do not turn UNPROVEN into PROVEN to ship.
7. Inspect the final diff and explicitly staged paths, then use `/create-commit`
   for any remaining changes. Do not create an empty duplicate commit if `/build`
   already committed the final candidate. Changes after review/proof require
   affected checks and evidence to be refreshed before acceptance.

Load each stage's current instructions. If a required skill is unavailable,
report the missing stage and stop there; do not silently replace it with a weaker
workflow. Preserve stage-specific user approval gates, including commit messages
and proof capture. An orchestrator is not a substitute for a required human.

## Deliver and hand off

Local-ready means a committed, reviewed candidate with verification results and
honest evidence limitations. If acceptance remains unmet, report a checkpoint or
blocked candidate instead. It does not mean pushed, merged, or deployed.

For a standalone ticket, invoke `/create-pr` only when push and PR permissions
cover the exact destination. Invoke `/merge-pr` only when merging is authorized
and its review/CI conditions hold for the current head. Required CI must actually
pass; local checks cannot replace it. Orchestrated delivery does not use
`/merge-pr`'s standalone failing-CI override. Honor those skills' own confirmation
gates and pass the permission record to every delivery stage, including commits
made by `/build`. Remote branch deletion needs its own permission. Never close a
ticket merely because a branch or PR exists. Closing syntax in commit messages
and PR bodies is also a planned ticket-status write and needs permission.

For a wave worker, return the candidate and let the parent integrate it. In either
case report ticket identity, base/candidate revisions, worktree/branch, stage
status, review dispositions, exact checks/results, proof verdicts/limitations,
external writes performed, remaining approvals/blockers, and the next action.
Preserve recovery material as described in the run contract. Do not remove the
worktree or branch automatically.
