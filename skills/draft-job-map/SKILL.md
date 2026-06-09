---
name: draft-job-map
description: >-
  Interview the user about a broad space (a market, a domain, a workflow, an
  internal initiative) and produce a concise, precise job map in the
  Jobs-to-Be-Done tradition. Each job in the map is a unit of progress an
  actor is trying to make in a circumstance, paired with competing
  alternatives and success criteria — specific enough that the user can pick
  a subset and target it. Borrows the relentless-interview style of
  `/grill-me` but is domain-focused on JTBD framing rather than generic plan
  stress-testing. Use when the user wants to break a vague space into
  targetable bets, find under-served jobs in a market, segment a product
  surface by user progress rather than features, or sharpen a strategy doc.
  Triggers include "map the jobs", "draft a job map", "JTBD this space",
  "what are people hiring X for", "break this space into jobs", "job
  landscape for".
---

`/draft-job-map` is a planning skill. One conversation, one artifact: a job map for a space the user names. The map enumerates the discrete jobs people are hiring something to do in that space, each pinned to a circumstance, a set of competing alternatives, and success criteria — so the user can pick the jobs worth targeting.

The skill does not pick winners. It does not generate strategy. It produces the map; the user decides which jobs to bet on.

## When to use

- The user is staring at a broad space ("agentic engineering at a tech company", "developer onboarding", "internal-tools sprawl") and wants to decompose it into things they could actually build, sell, or staff against.
- The user has a feature list and suspects it doesn't match what users are *hiring* the product for.
- The user is writing a strategy doc, PRD, or roadmap and wants the jobs-side of the framing before committing to solutions.
- The user has heard "we should JTBD this" and wants the output, not a tutorial.

## When not to use

- The user wants a competitive analysis or market sizing — different artifact; this skill is about progress, not market structure.
- The user already has a precise job and wants to design a solution for it — go straight to `/prep` or `/draft-api-client`.
- The user wants a persona doc — different (and weaker) framing; this skill deliberately avoids demographic personas.
- The user wants the *answer* to "what should we build" — this skill produces the map, not the bet.

## The interview style

This is not a flat script. Borrow from `/grill-me`: ask, listen, ask again, resolve branches before moving on. Push back when an answer is vague, solution-flavored, or demographic. The user explicitly invited grilling — use it.

Two hard rules during the interview:

- **No solutions in job statements.** "Use Claude Code to ship a PR" is a solution. "Ship a PR I'm confident in before EOD" is a job. If the user names a tool, ask what progress the tool is being hired for.
- **Circumstance over demographics.** "Senior engineers" is a demographic. "When I'm reviewing my third PR of the day and want to clear my queue before standup" is a circumstance. Jobs live in circumstances; segments live in demographics. This skill maps jobs.

If the user resists either rule, explain why once, then keep enforcing it. The map is worthless if these slip.

## The interview

### Phase 1 — Lock down the space

The space the user names is almost always too vague on the first pass. Sharpen it before doing anything else.

- **What's inside, what's outside?** "Agentic engineering at a tech company" — does that include data science notebooks? Customer-support agents? Internal tooling? The space's boundary determines which jobs are in scope.
- **Whose space?** A space exists for someone. Is this the space as seen by ICs, by EMs, by the platform team, by the CTO? Different vantage points yield different maps. Pick one (or commit to producing one map per vantage point).
- **Time horizon.** Is this the space as it exists today, or the space as the user expects it to exist in 18 months? Future-state maps are valid but must be labeled.
- **Why now?** What decision is this map feeding? A roadmap, a hire, an investment, a positioning doc? The downstream decision shapes what "precise enough" means.

Restate the sharpened space back to the user in one sentence before moving on. If they push back, sharpen again.

### Phase 2 — Identify the actor(s)

Most spaces have more than one actor doing different jobs. Don't collapse them.

- Who is doing jobs in this space? List candidates (often 2–5).
- For each actor, name the circumstance they're in when they enter this space — not their title.
- If two "actors" turn out to do the same jobs in the same circumstances, collapse them. If one actor does jobs from two different circumstances, split them.

Default: produce one job map per actor, but call out cross-actor jobs explicitly.

### Phase 3 — Surface candidate jobs (broad)

Now enumerate. Aim for breadth before precision; you'll prune in Phase 4.

Prompts that surface jobs well:

- "When you're in this space, what are you trying to make progress on?"
- "What are you currently doing — tools, hacks, workarounds — and what job is each of those *actually* doing for you?"
- "When was the last time something in this space frustrated you? What were you trying to do?"
- "What would 'a good day in this space' look like — what got done?"
- "What do people complain about?"

Capture 8–15 candidate jobs in raw form. Don't polish yet. Don't deduplicate yet.

Watch for three failure modes and call them out as they appear:

1. **Solution-flavored jobs.** "Have a better dashboard." → "What progress does the dashboard make possible?"
2. **Aspirational mush.** "Be more productive." → "Productive *at what*, in *what circumstance*?"
3. **Mixed-altitude jobs.** One says "stay employed" and another says "rename this variable safely." Flag the gap and decide together which altitude the map lives at. A useful map lives at one altitude.

### Phase 4 — Pressure-test each candidate

For each candidate that survives, fill in:

- **Job statement.** Format: *When [circumstance], I want to [motivation], so I can [outcome].* Tight. One sentence.
- **Circumstance.** The trigger — what's happening in the world when the job becomes active. Not who the person is; what the moment is.
- **Competing alternatives.** What is currently being "hired" for this job, including non-product alternatives: a senior teammate, a Slack channel, a shell alias, *doing nothing*, *avoiding the situation*. If there are no competing alternatives, the job probably isn't real — push back.
- **Success criteria.** How does the person know they made progress? One or two concrete signals. Avoid "satisfaction"; prefer "the PR merged before EOD without revert" or "I closed the ticket without paging anyone".
- **Hiring/firing forces** (light touch — one line each, skip if obvious):
  - *Push:* what about the current situation is unsatisfactory.
  - *Pull:* what about a new solution is attractive.
  - *Anxiety:* what makes switching scary.
  - *Habit:* what makes the current approach sticky.
- **Emotional / social dimensions** (only if non-obvious). "I don't want to look junior in code review" is a real, often-load-bearing job dimension. Capture it when present; skip when forced.

A job that can't fill in circumstance, alternatives, *and* success criteria is not a job. Drop it or merge it into one that can.

### Phase 5 — Stress-test the map

Before drafting the output, walk the map as a whole:

- **Non-overlap.** Two jobs with the same circumstance and the same success criteria are the same job. Merge.
- **Comparable altitude.** All jobs should be at the same altitude. If one is "ship a PR by EOD" and another is "advance my career", split into two maps or pick one altitude.
- **Coverage.** Are there obvious gaps? The actor wakes up, does jobs across a day — does the map cover what they actually do? Walk a representative day with the user.
- **Targetability.** For each job, can the user imagine a thing they'd build, hire, or buy to do it better? If not, the job is too abstract.
- **Honest count.** Concise beats comprehensive. A precise 5-job map beats a fuzzy 15-job map. Push to merge or cut.

The Phase-5 grilling is the single highest-leverage part of this skill. Don't rush it.

## Output: render then write

When the map is ready, **render it in the conversation first**. Don't write to disk yet.

Then ask the user where to save. Suggestions, in order:

1. If `.agentic/<slug>/` exists for the current branch, suggest `.agentic/<slug>/job-map.md`.
2. Else suggest `docs/job-map-<space-slug>.md` or `<repo-root>/job-map-<space-slug>.md`.
3. Accept any user-supplied path.

Only write after the user confirms a path. If they want to iterate on the map in chat first, do that — the file write is the last step.

## Job map template

```markdown
# Job map: <space>

**Vantage point**: <whose view of the space>
**Time horizon**: <today | future state, with date>
**Feeds decision**: <what this map is for>
**Drafted**: <YYYY-MM-DD>

## Space boundary

**In**: <what's inside this space>
**Out**: <what's deliberately excluded>

## Actors

1. **<actor name>** — <one-line circumstance, not demographic>
2. ...

(If multiple actors, label each job below with the actor(s) it belongs to.)

## Jobs

### J1. <one-line job title>

**Actor(s)**: <list>
**Job statement**: When <circumstance>, I want to <motivation>, so I can <outcome>.
**Circumstance**: <the trigger — what's happening in the world>
**Competing alternatives**:
- <current "hire" #1 — including non-product alternatives>
- <current "hire" #2>
- <doing nothing / avoidance, if applicable>
**Success criteria**:
- <concrete signal #1>
- <concrete signal #2>
**Forces** (optional):
- Push: <...>
- Pull: <...>
- Anxiety: <...>
- Habit: <...>
**Emotional / social** (optional): <only if load-bearing>

### J2. ...

## Cross-actor jobs

<jobs shared by multiple actors, if any — otherwise omit>

## Notes on what this map is NOT

- <explicit exclusions the user wanted recorded — e.g., "does not cover hiring/retention jobs">
- <known gaps the user accepted — e.g., "the platform-team vantage point is out of scope for this draft">

## Open questions

<anything the interview did not resolve — flagged so the user can answer before acting on the map>
```

## Guidelines

- **The space is the first thing to sharpen.** A fuzzy space produces a fuzzy map no matter how good the rest of the interview is. Spend disproportionate time in Phase 1.
- **Concise, precise, targetable.** Three words to repeat to yourself when pruning. A 5-job map the user can act on beats a 15-job map they can't.
- **Push back on solutions in job statements.** Every time. Solutions in job statements are the most common failure mode and they make the map useless for targeting.
- **Competing alternatives are diagnostic.** If a job has no competing alternative — not even "doing nothing" — it isn't a real job; it's a wish. Cut or merge.
- **One altitude per map.** If the user wants jobs at multiple altitudes, produce multiple maps. Don't mix.
- **Don't fabricate forces or emotional dimensions.** Only fill them in when the user surfaces them. A fabricated "anxiety" line is worse than no line.
- **The map is descriptive, not prescriptive.** The skill maps what's true; the user decides what to do about it. Resist the urge to recommend which jobs to target — that's the user's call, downstream.
- **Plain text only. No emojis.** Match the rest of the skills.
