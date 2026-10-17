---
name: deployment-risk-review
description: Reviews whether a diff introduces incorrectness into existing deployed workflows, data, and clients, during rollout and in ongoing operation afterward. Categorizes regression, rollout, and rollback risk. Use for existing-behavior impact, deployment risk, backwards compatibility, or as a review-suite lens.
---

# Deployment Risk Review

Answer: **Does this change introduce incorrectness into existing behavior or data, during deployment or at any point afterward?** Review existing users and state through rollout, steady-state operation, delayed lifecycle events, and rollback. A successful deployment or a working new feature does not establish that existing workflows remain correct.

This is a read-only, diff-driven assessment, not deployment approval, a production audit, or acceptance proof. Do not apply fixes, run migrations, query live user data, deploy, or change infrastructure. Use repository evidence and deployment facts supplied by the user; request permission before accessing external operational systems. Do not require `plan.md` or a workflow catalog. `/correctness-review` owns general logic and test quality; `/security-review` owns exploitability; `/prove` owns executed evidence.

## Target and baseline

- In `/review-suite`, use its exact resolved diff command, mode, base commit, and explicit untracked paths. Inspect new-file content as well as the tracked diff; do not choose a different target.
- Standalone, default to `git diff HEAD` plus non-ignored untracked files. With `--against <ref>`, resolve `git merge-base <ref> HEAD` and review the net diff from that commit through the working tree plus untracked files. Resolve ambiguous or missing refs with the user. Collect untracked paths with `git ls-files --others --exclude-standard -z`; do not stage them or follow symlinks.
- Identify the comparison baseline separately from the deployed version. A merge base or `main` is not proof of what is running. Use supplied release facts or repository deployment records, stating their limits. If deployment facts are absent, assess the transition from the comparison baseline conditionally and name the assumptions.
- No diff means no assessment needed. No deployed surface means `not-applicable`, with a reason. Missing evidence about a relevant surface means `unknown`, not `low` or `not-applicable`.

## Trace existing consumers and state

Follow changed contracts into unchanged callers, readers, writers, configuration, migrations, deployment manifests, and tests. Use `docs/workflows.md` if present, but discover relevant workflows directly from code when it is absent or stale. Focus on surfaces the diff can affect:

| Surface | Questions |
|---|---|
| Existing workflows and clients | Do current users retain behavior, access, saved settings, links, API/CLI contracts, and defaults? Do old SDKs, integrations, or cached frontends still work? Identify intentional incompatibilities too. |
| Persisted data | Can the candidate read historical rows, files, enum values, serialized state, and caches? Can old code read newly written state after rollback? Are backfills, constraints, retention changes, or destructive transforms safe for existing records? |
| In-flight work | What happens to queued messages, scheduled jobs, retries, active sessions, and partially completed workflows? Can jobs be lost, duplicated, stranded, or replayed with different semantics? |
| Mixed versions and rollout | Can old/new servers, workers, clients, and schemas coexist? What ordering, feature-flag defaults, migration locks, or compatibility windows are required? Are those requirements actually enforced? |
| Operations and recovery | Could changed queries, indexes, dependencies, config, or resource use disrupt service at existing scale? Is rollback sufficient, or are restore, repair, or forward migration required? What signals would detect harm? |

For each affected surface, record the existing consumer/state, the transition or failure scenario, code/config evidence, blast radius, reversibility, and safeguards already present. Separate observed facts from assumptions; do not invent traffic volumes, data distributions, deployed versions, backups, or rollback capability. Tests and deployment scripts support a claim but do not prove live state.

## Check existing behavior after deployment

Do not stop at schema compatibility or rollout safety. For each affected existing workflow, trace representative existing inputs and historical state through the baseline and candidate paths. Compare observable outputs and side effects against the established contract: calculations, eligibility, permissions, ordering, filtering, notifications, persisted values, and downstream actions. Include unchanged callers that reach changed shared code. Old behavior is evidence of the contract, not proof it was correct; distinguish an intentional bug fix from a regression using documented requirements and tests.

Check the lifecycle events that can expose a delayed regression: the next renewal or scheduled run, retry/replay, expiration, cache eviction, reopening an old record, or recomputing a historical result. Select relevant events from the code, not a generic checklist. A field that still deserializes but now means something different is a correctness risk, even if deployment and rollback both succeed.

Classify each affected surface's behavior as `preserved`, `intentional-change`, `regression`, or `unknown`, and name when the impact appears (`rollout`, `steady-state`, `delayed`, or `rollback`; multiple may apply). Intent requires evidence, not an inference that all changed behavior was wanted. For a regression, give the existing input/state → expected result → candidate result, with code references and the missing or distinguishing regression test. If the intended contract is unclear, state the competing interpretations and mark behavior unknown rather than declaring either correct.

Report concrete existing-behavior bugs here even when correctness review also covers them; the suite deduplicates the root cause while retaining the affected population, timing, and risk. Do not downgrade a silent wrong result merely because it causes no exception or outage. This assessment predicts post-deployment effects; it does not start ongoing monitoring or claim to have observed production.

## Categorize risk

Assign each affected surface a risk level and confidence (`confirmed` or `conditional`). Confidence describes evidence, not impact: a conditional data-loss scenario is not low risk just because live data is unavailable.

| Level | Criteria |
|---|---|
| low | Existing contracts and state remain compatible; impact is bounded and readily reversible, with supporting evidence. |
| medium | A bounded workflow or cohort may be disrupted, or a coordinated but reversible rollout/backfill is needed. Recovery is understood. |
| high | A core workflow, broad client population, or persisted state is at risk; mixed-version compatibility or recovery needs substantial coordination or repair. |
| critical | A concrete transition can cause irreversible data loss/corruption, widespread unrecoverable disruption, or similarly severe harm. State the triggering conditions. |
| unknown | Missing evidence prevents a defensible rating. Name the missing fact and the decision it affects. |
| not-applicable | No existing deployed consumer or state can be affected; explain why. |

Rate the candidate with safeguards already evidenced, not with proposed mitigations assumed complete. Overall risk is the highest known surface level, never an average. Report assessment completeness separately as `complete` or `incomplete`: material unknowns make it incomplete even if another surface has a known high rating. If no surface can be rated, overall risk is `unknown`; use `not-applicable` only when every surface is inapplicable. Neither a low rating nor a complete assessment certifies production safety.

For each material risk or unknown, recommend the smallest mitigation or check that would change the decision: for example, expand/contract ordering, compatibility with an old payload, a representative legacy-data check on disposable fixtures, or an explicit restore rehearsal. Recommendations do not authorize execution. Do not turn generic deployment best practices into findings without a connection to this diff.

## Output

Standalone, print the target, deployed-baseline evidence/assumptions, overall risk and completeness, then a compact surface table (risk, confidence, behavior classification, timing, affected workflow/data, evidence, recovery), actionable findings, and material unknowns. Do not write a report file or alter the worktree.

For `/review-suite`, return this object instead of the ordinary findings array:

```json
{
  "assessment": {
    "overall_risk": "low|medium|high|critical|unknown|not-applicable",
    "completeness": "complete|incomplete",
    "baseline": "Known deployment facts or explicit comparison-baseline assumptions",
    "surfaces": [
      {"surface": "existing workflow/data/consumer", "risk": "low|medium|high|critical|unknown|not-applicable", "confidence": "confirmed|conditional", "behavior": "preserved|intentional-change|regression|unknown", "timing": ["rollout|steady-state|delayed|rollback"], "impact": "Expected versus candidate behavior, blast radius, and recovery", "evidence": ["path:line"], "mitigation": "Existing safeguards and any recommended check"}
    ],
    "unknowns": ["Missing fact, why it matters, and how to resolve it"]
  },
  "findings": []
}
```

Use the suite's ordinary finding fields (`file`, `line`, `line_end`, `severity`, `summary`, `rationale`, `source`), with `source: "deployment-risk-review"`. Anchor each finding to a relevant changed line. Include risk level, confidence, existing consumer/state, failure sequence, and mitigation in its rationale. Use `critical` severity for an evidenced serious failure; `warn` for conditional risks, coordination requirements, or material evidence gaps. Keep unlocatable environment unknowns in the assessment rather than inventing file locations. Low-risk and inapplicable surfaces need no finding.

Always return the assessment, even with zero findings. Risk level and finding severity are separate: intentional high-risk migrations still deserve a risk assessment without being labeled incorrect. If inspection itself fails, report failure to the suite; do not disguise a failed review as an empty or low-risk result.
