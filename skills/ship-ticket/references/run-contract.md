# Run permissions and recovery

Shared contract for `/ship-ticket`, `/run-wave`, and `/run-waves`. Each outermost
invocation applies this before execution; nested invocations inherit the record.

## Ask upfront; default to no external writes

Read-only discovery may identify scope and side effects before the question.
Before implementing or dispatching workers, present the planned external writes
and ask which the user permits for this run. Name actions and destinations:

- Ticket creation, claims, comments, labels, assignments, status changes/closure.
- Branch pushes, PR/MR creation or edits, review comments, merges, remote deletion.
- Artifact uploads, externally hosted previews, notifications, and subscriptions.
- Any other operation that mutates shared/external state, including test calls.

For example: "For these tickets in owner/repo, may I push task branches and open
PRs? Ticket updates and merges will remain disabled unless you authorize them."
List only actions relevant to the proposed run; do not request broad account access.
If the user's current request already explicitly authorizes specific writes,
acknowledge and record those grants without asking for the same permission twice;
ask about any additional proposed actions upfront.

Wait for the decision. A denial, omission, ambiguous answer, or no answer grants
nothing. If the user says to continue without deciding, run local-only. Record
explicit denials as well as grants. Read-only authenticated access and available
credentials do not grant write permission. Local files, worktrees, and commits
are not external writes, though stage-specific approval gates still apply.

Record in the outer task's `plan.md`: selected tickets/repositories, delivery
target, approved actions and destinations, denied/unapproved actions, run limits,
and the user's authorization. Pass that record to every worker. Children may
narrow it, never expand it. A parent grant covers only the selected run, including
its waves; it does not cover unrelated tickets or future invocations. Resume the
same run only after reconciling the record with the latest user instructions.

No response is not a reason to retry permission prompts. Do not repeatedly ask
for declined writes. A newly discovered action outside the grant stays blocked;
finish independent authorized work and report the specific approval needed.
Permission for one action does not imply another: pushes do not grant merges,
PRs do not grant ticket edits, and a delivery target is not an authorization.

Inspect commands, hooks, tests, and repository automation for external effects
before running them. A local-looking command can call shared services; a push or
merge can trigger a deployment. Disclose consequential effects not covered by the
grant and obtain approval first. Use local disposable test dependencies. Never
deploy, release, change infrastructure/access, or write shared databases under
ordinary ticket-delivery permission. Keep these actions separate and explicit.

Inspect content and provenance before any allowed publication. Exclude secrets,
private records, session storage, and raw sensitive logs. Use synthetic fixtures.
If a write times out or its outcome is unknown, inspect remote state before
retrying; avoid duplicate PRs, comments, and other non-idempotent actions.

## Preserve one recoverable record

Use `.agentic/<slug>/plan.md` and `diary.md`, not a parallel planning system. The
outer diary records ticket ownership, worker/run identity, absolute worktree,
branch, exact base/candidate/checkpoint revisions, stage and delivery status,
checks/evidence references, blockers, and next action. Per-ticket diaries own
implementation detail. Record completed actions immediately to prevent duplicates.

Keep one writer per worktree. Save local checkpoints using the applicable commit
approval rules before planned stops or handoffs; unfinished checkpoints are not
accepted candidates. Retain branches and do not discard uncommitted work.

Ignored notes and temporary environments are not durable backups. Before deleting
or abandoning a worker environment, transfer the exact code and sanitized handoff
to the retained parent workspace or a project-approved retained location. A commit
ID alone cannot transfer code between clones. Use a tracked handoff only when
project policy permits it; do not silently stage ignored scratch files. A local
commit protects against worktree deletion, not loss of its whole environment.
If durable retention needs an unauthorized upload/push, do not perform it; report
the location and loss risk and preserve the environment where possible.

On resume, reconcile files, refs, ownership, remote writes, and actual delivery
against the diary before retrying or allocating a new writer. Never infer worker
abandonment from a timeout alone. Stop and surface contradictory state rather
than overwriting work. Reports distinguish checkpointed, reviewed, verified,
locally integrated, pushed, PR-open, and merged states.
