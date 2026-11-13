---
name: ship-ticket
description: Executes one ticket through a full or opt-in lite coding loop and authorized delivery. Use to ship or resume a feature or bug fix, independently or as a run-wave worker.
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

Apply the run contract's workflow and proof choices. For a known bug, use `/prep`
to establish expected versus observed behavior and reproduce the reported failure
on the recorded base before changing implementation. Treat a proposed cause as a
hypothesis until checked. Carry the reproducer into the verification plan and rerun
it after the fix, with a nearby unaffected case. If reproduction is unavailable,
record the missing evidence and agree how to validate the fix; do not claim a
confirmed cause or successful reproduction. A bug report alone does not select lite.

## Execute the coding loop

1. Use `/create-worktree` for a new isolated task workspace, or reconcile and reuse
   the assigned worktree. Never nest a second worktree just because this is a
   delegated invocation. Initialize `.agentic/<slug>/` using the existing ignore
   and tracked-path checks; preserve ticket context, plan, and diary on resume.
2. Run `/prep`, supplying the approved requirements, project guide, base, delivery
   target, workflow, permission record, run-level choices, and applicable shared
   research/setup. Revalidate any provisional read-only prep against this base;
   finish its missing decisions and environment probes before building. Reuse
   settled decisions and source-backed findings; investigate ticket-specific gaps
   and route genuinely missing decisions to the user.
3. Run `/build` with `/prep`'s verification schedule: targeted checks during work,
   broader checks early where needed, and the full local gate at ticket readiness
   before review. Reuse recorded checkpoint/TDD choices. Keep local checkpoint/final
   commit handling distinct from acceptance or publication.
4. In full mode, run `/review-suite` on the complete ticket diff against its
   recorded base. Follow its risk-based allocation: combine selected lenses in one
   independent reviewer only for established low-risk changes; retain specialist
   fan-out for risky or uncertain changes. Reviewers are read-only or use an
   isolated copy. If independent review is unavailable, report that limitation;
   do not label self-review independent or claim the full workflow completed.
5. In full mode, run `/resolve-review`. Record every finding's disposition,
   including a no-fix outcome when appropriate. Recheck fixes under the recorded
   reuse policy and repeat affected review, not automatically the entire suite.
   Unresolved product/policy decisions remain blockers, not guessed requirements.
6. In full mode, plan proof early. With ticket proof, run `/prove` after review
   fixes settle, honoring its concrete capture-plan and tooling approval gates.
   Record its actual verdicts or a no-behavioral-claim not-applicable result;
   distinguish regression checks from falsifiable acceptance evidence. Do not turn
   UNPROVEN into PROVEN to ship. With wave proof, hand the parent exact claims,
   original base, candidate revision, build checks, artifacts, and pending capture
   approvals under `/prove`'s wave-proof rules; mark full proof pending
   integration. Deferral never becomes PROVEN by assertion. In lite mode, omit
   stages 4–6 under the recorded policy; run any agreed lightweight check as part
   of build verification and report its actual result, not a `/prove` verdict.
7. Inspect the final diff and explicitly staged paths, then use `/create-commit`
   for any remaining changes. Do not create an empty duplicate commit if `/build`
   already committed the final candidate. Changes after review/proof require
   affected checks and evidence to be refreshed before acceptance.

Load each stage's current instructions. If a required skill is unavailable,
report the missing stage and stop there; do not silently replace it with a weaker
workflow. Preserve stage-specific user approval gates, including commit messages
and proof capture. An orchestrator is not a substitute for a required human.

## Deliver and hand off

Local-ready follows the selected full or lite policy in the run contract, with
verification results and honest evidence limitations. Deferred wave proof is still
pending, not local-ready. If acceptance remains unmet, report a checkpoint or
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

For a wave worker, return the candidate and let the parent integrate it. A reviewed,
gate-passing candidate with explicitly deferred proof may enter local integration,
but is proof-pending, not local-ready or accepted for delivery. The parent must
complete that stage and check acceptance before publication.

Return the compact handoff defined in the run contract, including ticket identity,
worktree/branch, external writes performed, and remaining approvals. Link detailed
investigation and evidence rather than copying full diaries into parent context.
Preserve recovery material as described in the run contract. Do not remove the
worktree or branch automatically.
