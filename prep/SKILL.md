---
name: prep
description: Interview the user and produce `.agentic/<slug>/plan.md` defining goal, optimization target, acceptance criteria, verification plan, research, environment readiness, and implementation approach. Use after /create-worktree and before /build.
---

`/prep` is one conversation that produces one artifact: `.agentic/<slug>/plan.md`. It interviews the user, probes the codebase, verifies the environment is ready for autonomous execution, and writes everything `/build` and `/review` will need.

## Locate the workspace

If the current directory contains exactly one `.agentic/<slug>/` dir, use it. If there are multiple, pick the one whose `<slug>` matches the current git branch; otherwise ask. If `.agentic/` doesn't exist, suggest `/create-worktree` first.

## Read ticket context first

If `.agentic/<slug>/ticket.json` exists, read it. Use it to seed the goal, acceptance, and out-of-scope sections — but treat it as a starting point, not the final word.

## The interview

Conduct a conversational interview to fill the sections below. Build on the user's answers; don't run through a flat script. Pull from `ticket.json` and codebase exploration to make questions specific.

May fan out to Explore sub-agents in parallel when research spans multiple domains or a subsystem needs deep reading. Use them to find implementation templates (existing features that solve analogous problems) and test fixtures.

### Sections to fill

**Goal.** What we're building, in 1-2 paragraphs. Cite the ticket if relevant.

**Optimization target.** What we're optimizing for *and* what we're explicitly NOT optimizing for. Guide the user to make this concrete: "maintainability" alone is vague; "maintainability — readable by someone who hasn't seen the codebase, accepting slower runtime" is useful. Common values: correctness, maintainability, performance, security, simplicity, user experience.

**Acceptance criteria.** 3-5 testable bullets. Each must have a concrete verification (a test, a command, a demonstration). Avoid "code is clean" — say "API returns 200 for valid input". For measurable improvements (latency, error rate), include baseline + target + how to measure.

**Verification plan.** How `/build` and the user will confirm the work. Specific commands to run, URLs to visit, what output looks like when correct. Designed *now* so `/build` knows how to present its work and `/review` knows what to check.

**Research / context.** Codebase patterns and file paths the implementation will mirror. External docs or best practices. Domain concepts. Be concrete with paths and function names; this is what `/build` reads to avoid re-discovering everything.

**Environment readiness.** This is non-optional. Before declaring `/prep` done, verify the agent has what it needs to work independently:

1. **Test commands.** Identify the gate (`just gate`, `npm test`, `pytest`, etc.) from `justfile`, `CLAUDE.md`, `AGENTS.md`, or by asking. Then dry-run each: `just --list`, `npm test --help`, etc. Record exact commands.
2. **Dev runtime.** If the task touches a runnable surface (web app, CLI, service), confirm it boots from a clean state — `just dev` or equivalent. If it can't, surface the blocker now.

If anything is broken or missing, list it as a blocker at the top of plan.md. Don't continue silently.

**Implementation approach.** Step-by-step. Each step: what to do, which files to touch, which acceptance criteria it advances. Order so each step leaves the tree compilable. End with a "Validation and Verification" step that runs the gate and the verification plan.

## plan.md template

```markdown
# Plan: <task name>

**Slug**: <slug>
**Gate command**: <e.g., just gate>
**Optimization target**: <single concept + what we are NOT optimizing for>

## Goal
<1-2 paragraphs>

## Acceptance criteria
1. <criterion> — verified by <test/command>
2. ...

## Verification plan
- Commands to run: <...>
- URLs / surfaces to inspect: <...>
- Expected outputs: <...>

## Research
**Patterns to mirror**: <files, functions, with paths>
**External references**: <links>
**Domain notes**: <...>

## Environment readiness
- Gate command: <command> — dry-run: PASS|FAIL (notes)
- Dev runtime: <command> — boots: YES|NO (notes)
- Blockers: <list or "none">

## Implementation approach
### Step 1: <name>
- <action>
- Files: <paths>
- Acceptance criteria advanced: <numbers>

### Step 2: ...

### Final step: Validation and verification
- Run gate: <command>
- Walk through verification plan
- Confirm each acceptance criterion passes
```

## Guidelines

- One conversation, one file. Don't fragment into separate goal/acceptance/research files — that's the old SACF shape; we deliberately moved away from it.
- Lead with questions that surface optimization-target tradeoffs. "What are we willing to give up?" usually clarifies more than "what are we optimizing for?".
- The environment readiness probe is the most-skipped section and the most expensive to skip — agents that hit missing tooling mid-`/build` waste a lot of work.
- Plain text only. No emojis.
