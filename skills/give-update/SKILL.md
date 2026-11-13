---
name: give-update
description: Reports percentage complete, current work, blockers, and next actions for a ship-ticket, run-wave, or run-waves run. Use when asked for a progress update on one of these runs.
---

# Give a run update

Give a concise, read-only progress snapshot in the conversation. Do not start,
resume, or change the run, dispatch workers, write status files, or publish updates
to a tracker. An update during active execution does not cancel that execution.

## Find the run and its evidence

Accept an optional task path, ticket, or run/thread reference. Default to the run
in the current conversation. Otherwise inspect the relevant `.agentic/` task
records; if multiple runs fit, ask which one and wait. If no run is available,
ask for its reference or task path rather than inventing progress.

Read the outer `.agentic/<slug>/plan.md` and latest relevant entries in `diary.md`
for the selected scope, delivery target, limits, worker references, and blockers.
Read per-ticket plans, diaries, and handoffs only as needed to establish status.
Use available read-only worker/thread, Git, and PR/CI status to resolve stale or
uncertain claims. Do not wait for workers to finish just to give an update.
When evidence is inaccessible or conflicting, name the gap and qualify the
affected status; silence or an idle worker is not proof of completion.

## Calculate progress transparently

- **Ship-ticket:** use the applicable milestones: preparation (workspace and
  approved plan), implementation, review, review resolution, proof, final commit,
  and any delivery steps needed for the target (PR opened, then merged). Report
  completed milestones / applicable milestones as a rounded whole percentage,
  labeled **stage-based estimate**, not effort or time remaining. Count a milestone
  only with supporting evidence on the current candidate. An explicit valid
  not-applicable result satisfies that stage; a missing stage does not. Exclude
  stages explicitly omitted by the recorded lite policy from the denominator and
  disclose those omissions. Deferred wave proof remains incomplete until the
  parent records its result for this ticket. Provisional read-only prep is not
  completed preparation until revalidated and finished on the build base. Reopened
  stages are incomplete. Reserve 100% for meeting acceptance and the agreed target.
- **Run-wave:** report tickets at the agreed target / tickets selected for this
  wave. Worker candidates alone do not count as delivered: required integration
  and combined verification must also be satisfied.
- **Run-waves:** use the entire finite selected ticket set, not just the current
  wave or tickets dispatched so far. Show current-wave progress separately when
  useful. Count each ticket once, and include blocked, failed, deferred, and
  unstarted tickets in the denominator unless scope was explicitly changed.

For batches, round to a whole percentage and show the fraction. Label it
**ticket completion**, not an estimate of effort; partially finished tickets earn
no fractional credit, but describe their current work. Apply the recorded target
(local-ready, PR-open, or merged), not ticket closure or implementation alone.
If scope, target, or evidence is insufficient, report the percentage as unknown
and say what is missing. An empty scope is not 100% complete. Do not invent an ETA.

## Report and stop

Keep the update short, normally five bullets; use a compact per-ticket table only
when needed to explain a batch:

- **Progress:** run identity, percentage and fraction/basis, delivery target, and
  whether it is running, paused, blocked, stopped, or complete.
- **Completed:** meaningful finished work and actual delivery state; distinguish
  local candidates, integrated work, open PRs, and merges.
- **In progress:** active stage/tickets and current wave; include unstarted work
  and remaining budget when relevant and known.
- **Blockers:** each blocking condition, affected tickets, and who or what can
  unblock it. Include pending approvals and failed checks. Say "none known" when
  supported, or "unknown" when visibility is missing; distinguish ticket-local
  blocks from a run-wide stop.
- **Next:** the next action and any specific user decision needed. Link the main
  evidence and disclose stale or unavailable status without dumping logs.

Stop after the snapshot. Do not treat reporting a next action as authorization
to perform it or change existing run permissions.
