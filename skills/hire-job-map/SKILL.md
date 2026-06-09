---
name: hire-job-map
description: >-
  Take a job map (typically produced by `/draft-job-map`, but any equivalent
  document works) and produce a stack-ranked list of candidate solutions to
  "hire" for each job — keeping the JTBD terminology end-to-end. Biased
  toward existing solutions over building, and toward open-source /
  self-hostable solutions over SaaS or closed-source. Honest about
  uncertainty: candidates the skill is not sure exist or are maintained get
  flagged and routed to a verification step rather than ranked confidently.
  Composes downstream with `/fetch-context` (read the candidate's source)
  and `/audit-third-party` (security/privacy audit before adoption). Use
  when the user has a job map and is ready to decide what to adopt, build,
  or stop using. Triggers include "hire for these jobs", "rank solutions
  for this job map", "what should we adopt for X", "build vs buy on this
  job", "stack-rank candidates for".
---

`/hire-job-map` is a planning skill. One conversation, one artifact: a stack-ranked candidate list per job, plus a portfolio view that surfaces solutions that cover multiple jobs at once.

The skill ranks. It does not adopt. The user decides which candidates to take to `/fetch-context` and `/audit-third-party` before pulling the trigger.

## When to use

- The user has a job map (from `/draft-job-map` or hand-written) and wants to decide what to "hire" for each job.
- The user is evaluating build vs. buy and wants the decision pinned to specific jobs, not generalities.
- The user wants to inventory the current "hires" (the competing-alternatives list from the job map) against possible replacements.
- The user wants an honest "the best fit here is to keep doing what you're doing" answer when that's true.

## When not to use

- The user does not yet have a job map — run `/draft-job-map` first. Ranking solutions without jobs produces feature lists, not decisions.
- The user has already chosen a candidate and wants to implement — go to `/prep`.
- The user wants a security/privacy audit of one candidate — go to `/audit-third-party`.
- The user wants vendor selection bake-offs with weighted scoring matrices — different artifact; this skill stays lightweight.

## Locate the job map

Look for inputs in this order; ask only if none are present.

1. `.agentic/<slug>/job-map.md` for the current branch.
2. `docs/job-map-*.md` or `<repo-root>/job-map-*.md`.
3. Pasted job-map text in the conversation.
4. A hand-written list of jobs the user names in chat — accept it but warn that thin job definitions will produce thin rankings; offer `/draft-job-map` if the user wants to sharpen first.

Read the map. Confirm with the user which jobs to rank — sometimes they want the full map, often a subset. Default: rank all jobs unless the user scopes down.

## The interview (calibration)

Before ranking, calibrate. The same candidate ranks differently depending on constraints. Cover at minimum:

- **Deployment posture.** Cloud SaaS allowed / cloud self-hosted / on-prem / air-gapped. Drives the SaaS-vs-self-hostable axis.
- **License constraints.** Are GPL/AGPL/SSPL acceptable in this context? Does the user need permissive (MIT/Apache) only? Are commercial licenses acceptable?
- **Budget posture.** Strong preference for free/OSS, moderate budget for vendors, generous budget. The OSS-self-hostable preference is the default but the user may have explicit budget.
- **Team capacity to operate.** Self-hosting a heavy OSS service has an ongoing cost. If the team can't operate it, "OSS self-hostable" becomes a worse choice than a managed SaaS — flag the trade-off, don't pretend it doesn't exist.
- **Time horizon for adoption.** "We need this in two weeks" vs. "we'll spend a quarter rolling it out" changes which candidates are realistic.
- **Existing stack.** What's already in the org that could be extended? A solution the team already operates ranks higher than a new one, all else equal.
- **Risk tolerance.** New, fast-moving projects vs. mature, boring tools. Some users explicitly want bleeding-edge; most don't.
- **Switching cost from the current alternative.** For each job, the job map already names a current "hire" (including "doing nothing"). Cheap-to-switch jobs rank differently than expensive-to-switch ones.

Persist nothing. The calibration stays in conversation context and drives Phase 2 scoring.

## Phase 1 — Enumerate candidates per job

For each job in scope, build a candidate list. Include:

1. **The current hire** (from the job map's competing-alternatives list). This is the baseline. Sometimes the right answer is "keep doing what you're doing" and the skill should be able to surface that.
2. **Adjacent in-house solutions.** Things the org already operates that could be extended to do this job.
3. **Open-source self-hostable candidates.** The preferred category. Prefer maintained, real-adopter projects over GitHub-stars-only ones.
4. **Open-source SaaS-only candidates.** OSS that the org would consume as a hosted service.
5. **Commercial self-hostable candidates.** Closed-source but deployable in the org's environment.
6. **Commercial SaaS candidates.** Vendor-hosted, no self-host option.
7. **Build-from-scratch.** Always include as a baseline so the skill can honestly say "everything available is worse than building this small thing yourself" when that's true.

Aim for 3–6 candidates per job, not 15. Concise beats comprehensive — the user is choosing one, maybe two.

### Honest uncertainty rules

This phase is where hallucination risk is highest. Apply these rules without exception:

- If the skill is not confident a named candidate exists, is maintained, or actually does the job: mark it `[unverified]` and add a one-line note: "verify maintenance status via `/fetch-context` before relying on this rank."
- Prefer to search (WebSearch, Bash, `/fetch-context`) over recalling. A specific URL and a recent commit date is worth more than a confident-sounding name.
- Do not fabricate product names, repos, or vendors. If the skill can only name the *category* of solution ("there is likely a Rust-based OSS workflow engine here, but I cannot name one I'm confident in"), say exactly that.
- For each non-current-hire candidate, capture: name, link (repo URL or vendor URL), license, hosting model, last-meaningful-update signal (recent commit / release / changelog entry), and a one-line "what it actually does." Missing fields are fine but must be marked missing, not invented.

If the user wants higher confidence on the candidate list, offer to fan out to `/fetch-context` against the top candidates before ranking — the rank improves a lot once the skill has read each repo's README.

## Phase 2 — Score each candidate

Score on a small, fixed set of axes. The aim is a defensible rank, not a spreadsheet exercise.

For each candidate, score each axis on a 1–5 scale (1 = poor, 5 = excellent). Use H/M/L if the user prefers; the math doesn't matter, the rationale does.

1. **Fit to success criteria.** Does this candidate actually make progress on the job's specific success criteria? A candidate that scores high here but middling elsewhere usually wins.
2. **Adoption effort.** How much work to get this in front of the actor doing the job. Existing in-house > extend existing > adopt OSS > adopt commercial > build new. Score inversely: low effort = high score.
3. **License and hostability.** Apply the user's calibration:
   - OSS + self-hostable + permissive license = 5
   - OSS + self-hostable + copyleft (acceptable to user) = 4
   - OSS + SaaS-only = 3
   - Commercial + self-hostable = 2-3 depending on budget
   - Commercial + SaaS-only = 1-2 depending on deployment posture
   - Build from scratch = N/A on this axis; scored elsewhere
4. **Maturity / community health.** Maintained, adopted, governed. Last meaningful commit, real production users, evidence of bus-factor > 1. A new shiny project scores low here unless the user explicitly wants bleeding-edge.
5. **Switching cost from the current alternative.** How disruptive to move users off what they're hiring now. Cheap switch = high score. Expensive switch = low score, which is a tax on adoption even when the candidate is technically better.
6. **Lock-in and exit risk.** How hard to leave this candidate later. OSS with portable data = high score. Proprietary data formats and APIs = low score.

Add the scores per candidate, then rank. But: do not pretend the sum is precise. The rank is a sort, not a measurement. Tie-breaks go to: lower adoption effort, then higher licensability score, then maturity.

The current hire gets scored on the same axes. If it ranks first, the skill says so plainly — "no change" is a legitimate output.

## Phase 3 — The portfolio view

After per-job rankings, walk the candidates as a portfolio. Surface:

- **Cross-job winners.** A candidate that ranks in the top 2 for three different jobs is a stronger bet than three different point solutions, even if each point solution ranks #1 for its job. Call these out explicitly.
- **Build-vs-buy clusters.** Are most top-ranked candidates OSS self-hostable, or is the user trending toward SaaS? Either is fine; the skill should observe the pattern so the user can sanity-check it.
- **Coverage gaps.** Jobs where the top candidate scores poorly on fit. These are the jobs where building from scratch — or living with the current alternative — may be the right call. Flag them.
- **Adoption sequencing hint.** Which one or two candidates would unlock the most jobs with the least adoption effort. This is a hint, not a roadmap.

Keep the portfolio view to half a page. Its job is to surface signal across the per-job rankings, not to re-do them.

## Phase 4 — Recommend verification, then hand off

For the top-ranked candidate per job (or the top portfolio winners), recommend:

- `/fetch-context` to clone the repo and skim the README, CHANGELOG, and recent commits.
- `/audit-third-party` to scan for data-exfiltration, defaults, and supply-chain risk before adopting.
- A small, time-boxed pilot for the actor on the job, with success defined against the job map's success criteria.

The skill does not run these itself — that's the user's call. But naming the next step keeps the rank honest: a #1 rank that no one verifies is just a guess.

## Output: render then write

Render the full output in the conversation first. Then ask where to write. Suggestions in order:

1. If `.agentic/<slug>/` exists, suggest `.agentic/<slug>/hire-map.md` alongside `job-map.md`.
2. Else suggest `docs/hire-map-<space-slug>.md` or `<repo-root>/hire-map-<space-slug>.md`.
3. Accept any user-supplied path.

Only write after the user confirms a path.

## Hire map template

```markdown
# Hire map: <space>

**Source job map**: <path or "pasted">
**Drafted**: <YYYY-MM-DD>

## Calibration

- Deployment posture: <SaaS | self-hosted cloud | on-prem | air-gapped>
- License constraints: <permissive only | copyleft OK | commercial OK>
- Budget posture: <free/OSS preferred | moderate | generous>
- Team capacity to operate: <high | medium | low>
- Time horizon: <weeks | quarter | year>
- Existing stack to lean on: <list>
- Risk tolerance: <conservative | balanced | bleeding-edge>

## Per-job rankings

### J1. <job title from job map>

**Job statement**: <one line from the source map>
**Current hire**: <from the source map's competing-alternatives list>

| Rank | Candidate | License / hosting | Fit | Effort | Lic/Host | Maturity | Switch | Lock-in | Total |
|---|---|---|---|---|---|---|---|---|---|
| 1 | <name> [link] | <e.g. Apache-2.0, self-hostable> | 5 | 4 | 5 | 4 | 3 | 5 | 26 |
| 2 | <name> [link] | <...> | 4 | 4 | 5 | 3 | 4 | 4 | 24 |
| 3 | <current hire> | <...> | 3 | 5 | n/a | 5 | 5 | n/a | 18 |
| 4 | Build from scratch | n/a | 5 | 1 | n/a | n/a | 3 | 5 | 14 |

**Rationale (top pick)**: <2–3 sentences. Lead with fit to success criteria.>
**Watch-outs**: <known risks for the top pick — license edge cases, operational burden, bus-factor concerns>
**Verify before adopting**: `/fetch-context <repo>` then `/audit-third-party` if the candidate will process sensitive data.
**Unverified candidates considered**: <list, with the one-line note for each>

### J2. ...

## Portfolio view

**Cross-job winners**: <candidates that rank top-2 for 2+ jobs, with which jobs they cover>
**Build-vs-buy pattern**: <observation about the shape of the top picks>
**Coverage gaps**: <jobs where the top candidate scored poorly on fit; recommend "keep the current hire" or "build small" with reason>
**Suggested adoption order**: <1–2 names; one-line "why this first">

## Open questions

<things the interview did not resolve — flagged for the user to answer before acting on the rankings>
```

## Guidelines

- **The rank is a sort, not a measurement.** Don't oversell the totals. Use them to break ties, not to claim precision.
- **The current hire competes honestly.** Score it on the same axes as the alternatives. "Keep doing what you're doing" is a legitimate top rank when the switching cost is high and the fit is decent.
- **Existing > adopt > build.** Default ordering, justified by adoption cost. If the user has explicit reasons to flip this (regulated environment, strategic differentiation, no acceptable alternatives), surface those reasons in the rationale.
- **OSS self-hostable > OSS SaaS-only > commercial self-hostable > commercial SaaS.** Default ordering, justified by control and exit cost. Calibration overrides this when the user names budget, capacity, or risk constraints that change it.
- **Don't fabricate candidates.** Naming a plausible-sounding tool that doesn't exist is worse than naming the category and recommending the user search. Mark uncertainty with `[unverified]` and route to `/fetch-context`.
- **Build-from-scratch is always a candidate.** Including it forces an honest comparison and prevents the "we evaluated four options" anchoring trap.
- **Cross-job winners are the highest-leverage finding.** Surface them prominently — they're often the difference between a 3-tool adoption and a 7-tool adoption.
- **Hand off; don't half-do.** When a top candidate looks real, recommend `/fetch-context` and `/audit-third-party` rather than guessing further about its source or its risks.
- **Plain text only. No emojis.** Match the rest of the skills.
