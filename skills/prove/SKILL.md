---
name: prove
description: Produce falsifiable evidence that a change does what it claims. Extracts claims from `plan.md` acceptance criteria or infers them from the diff, picks the cheapest falsifiable evidence per claim, then proves each artifact by running its counterfactual — the new test on the base ref, the same screenshot before the change, the same benchmark on both trees. Proposes its capture plan — naming the tooling, such as agent-browser versus Playwright, and any install it would need — and waits for approval before capturing anything. Reports PROVEN, VACUOUS, or UNPROVEN per claim and packages the result as a reviewer-facing `EVIDENCE.md` ready to paste into a PR or MR. Read-only; never edits the repo. Use after `/build` and before `/create-pr`, or when the user says "prove it", "show it works", "evidence for this change", "red-green proof", "before and after".
---

`/prove` answers one question a reviewer cannot answer from a diff: **does this change actually do what it claims?** It gathers evidence per claim, then attacks each piece of evidence to see whether it survives.

It is the acceptance-criteria counterpart to `/review-suite`. `/review-suite` judges how the code is written; `/prove` judges whether it works. Neither substitutes for the other.

## The rule

**Evidence that would look identical if the change did not work is not evidence.**

Every artifact needs a counterfactual — the same artifact produced from a world without the change. A test that was never seen failing, a screenshot with no "before", a single benchmark run: these are decorations. `/prove` produces the counterfactual for each artifact and reports the ones that don't survive.

## When not to use

- On a diff with no behavioral claim (formatting, comments, dependency bumps with no version-gated behavior). Say so and exit.
- As a code review. `/review-suite` owns that.
- As a gate. `/prove` reports; it never blocks and never fixes.

## Target

Same grammar as `/review-suite`. Default is branch-vs-main, since that's what a reviewer sees.

| Invocation | Scope |
|---|---|
| `/prove` | `git diff main...HEAD` plus uncommitted edits |
| `/prove --against <ref>` | `git diff <ref>...HEAD` plus uncommitted |

If the target has no diff, report that and exit.

## Step 1: Claims

A claim is one falsifiable statement about behavior. "Rejects negative quantities with a 422" is a claim; "improves validation" is not.

- If `.agentic/<slug>/plan.md` exists, take the acceptance criteria as the claims verbatim. Do not re-derive them.
- Otherwise, infer 3-5 claims from the diff and confirm them with the user in a single question before doing any work. Getting the claims wrong wastes the whole run.

Claims the diff implies but nobody stated — a changed default, a new outbound call, a widened permission — get added as claims too. Unstated behavior changes are exactly what reviewers miss.

## Step 2: Pick evidence per claim

Cheapest evidence that is still falsifiable. Not the most impressive. A pure-function change gets a unit test, never a video.

| Claim shape | Evidence | Counterfactual |
|---|---|---|
| Pure function, new validation, deterministic bug fix | Unit test | Same test on the base tree must fail |
| Behavior spanning modules, a DB, or an HTTP boundary | Integration test | Same |
| User-visible flow through the real stack | E2E test | Same |
| CLI output, API response, generated file | Command transcript from both trees | The diff between the two transcripts |
| Rendering, layout, visual state | Screenshot pair | The "before" shot lacks the thing |
| Interaction, timing, animation, multi-step flow | Screencast | Base-tree run of the identical script |
| Latency, throughput, memory | Benchmark, n>=10, both trees | Overlapping distributions kill the claim |
| Refactor with no intended behavior change | Existing suite green on both trees, plus coverage of the touched lines | A behavior difference would surface |

If a claim has no affordable falsifiable evidence, say so and move on. That gap is a finding, not a failure.

## Step 3: Propose the capture plan and wait

**Capture nothing and install nothing before the user approves this plan.** Reading the diff, resolving the forge, and detecting available tooling are fine; producing artifacts is not.

Present one table covering every claim, then stop and wait. The point is that the user sees the tooling choice and the cost before any of it is spent — swapping a video for a screenshot pair, or dropping a claim, is nearly free here and expensive afterwards.

| Claim | Evidence | Tool | Counterfactual | Cost |
|---|---|---|---|---|
| 1. Rejects negative quantity | Unit test | pytest, existing | base tree | seconds |
| 2. Banner renders on checkout | Screenshot pair | agent-browser | pixel diff | ~2 min, needs both dev servers |
| 3. Retry animation is smooth | Screencast | **Playwright `recordVideo` — not installed** | base-tree run of same script | ~10 min plus a new dependency |
| 4. No SSO regression | none | — | — | UNPROVEN, no test covers this path |

Name the tool explicitly, never just "a screenshot". The choice the user most needs to see is the visual one:

| Tool | Use for | Cost to the user |
|---|---|---|
| `agent-browser` | Screenshots, pixel diff | Already this repo's default; localhost-allowlisted |
| Playwright | Video, scripted multi-step interaction | New runtime dependency, plus browser download |
| asciinema / vhs | Terminal interactivity or timing | New binary |
| none — test or transcript | Everything else | Free, and diffable |

Flag anything that would be installed, in bold, in the row that needs it. A plan that silently adds Playwright to prove a claim a screenshot pair would have covered is the failure this gate exists to prevent.

The user may approve, drop claims, downgrade evidence, or swap tools. Honor the amended plan without re-arguing it.

## Step 4: Falsify

All execution happens in throwaway worktrees. The user's working tree is never touched.

```bash
BASE=$(git merge-base main HEAD)
WORK=$(mktemp -d)
git worktree add "$WORK/base" "$BASE"
git worktree add --detach "$WORK/head" HEAD
git diff HEAD | (cd "$WORK/head" && git apply)   # only when uncommitted work exists
```

Run every artifact in `$WORK/head`, then the identical command in `$WORK/base`. Capture both. Remove both worktrees when done (`git worktree remove --force`).

**Mutation fallback.** When the base tree cannot run the artifact at all — the test imports a module that does not exist yet, a new dependency isn't installed, the file is new — falsify by mutation instead: in `$WORK/head`, neutralize the smallest piece of the change (flip the new condition, delete the new call, restore the old constant), rerun, confirm red, then `git checkout -- .` in that throwaway tree.

Record which mode was used. They prove different things: base-ref proves *this diff* causes the behavior; mutation proves *this line* does.

### Capturing visual evidence

Screenshots and video are the artifacts most likely to come out VACUOUS, because two captures of the same page differ for reasons unrelated to the change. Determinism is a falsifiability requirement here, not polish. Both captures must come from one script run against both trees, with the same viewport and device scale, the same seeded fixture data rather than live data, animations disabled and the caret hidden, and dynamic regions — timestamps, generated IDs, avatars — masked.

A before/after pair that differs in a rendered timestamp and nothing else is VACUOUS. Say so rather than shipping it.

**Screenshots — agent-browser** (see `docs/browser.md`), which also does the comparison:

```bash
agent-browser screenshot --full base.png    # against the base tree's server
agent-browser screenshot --full head.png    # against the head tree's server
agent-browser diff screenshot base.png head.png
```

The pixel diff *is* the counterfactual. An empty diff on a claim that asserts a visual change is the VACUOUS verdict, reached directly.

**Video — agent-browser cannot record.** It streams (`stream enable`) but writes no file. Recording needs Playwright's `recordVideo` context option, which emits a WebM per context on close. That pulls in a runtime `docs/browser.md` deliberately avoids, so the Step 3 plan must name Playwright and flag the install rather than burying it under "screencast".

Prefer not to. Video is not diffable, not searchable, and not regression protection — a reviewer cannot check a claim against it faster than against a test. Most claims that feel like they need video are better served by a screenshot pair at the two interesting moments. Reserve it for claims genuinely about motion, timing, or a multi-step interaction.

**Terminal claims** — a plain transcript beats a recording, since it diffs and greps. Reach for asciinema or vhs only when the claim is about interactivity or timing rather than output.

## Step 5: Verdicts

| Verdict | Meaning |
|---|---|
| PROVEN | Artifact passes on head and its counterfactual failed as required |
| VACUOUS | Artifact exists but the counterfactual also passed — the test is green on base, the screenshots are identical. Report loudly; this is worse than no evidence because it looks like evidence |
| UNPROVEN | No falsifiable artifact could be produced |
| ASSERTED | Prose reasoning only. Never counts as evidence; label it so the reviewer knows what they are trusting |

Lead the report with VACUOUS and UNPROVEN. The claims that failed to prove are the most useful thing `/prove` produces.

## Does not count as evidence

- A test written after the implementation that was never observed failing.
- An assertion that restates the implementation (`assert format(x) == format(x)`).
- A test whose mocks are deep enough that it asserts the mock, not the system.
- An "after" screenshot with no "before".
- A single benchmark run, or two runs on different machines or trees with different build flags.
- A green CI badge. It proves the suite passes, not that the suite tests the claim.

When an artifact falls into one of these, mark it VACUOUS and name which one.

## Output

`.agentic/<slug>/evidence/` — already gitignored, so nothing is committed by default. Outside a task workspace, use `$(mktemp -d)` and print the path.

```
evidence/
  EVIDENCE.md      reviewer-facing summary, pasteable into a PR or MR
  logs/            raw transcripts from both trees
  media/           screenshots and casts, only when requested
```

`EVIDENCE.md` leads with the matrix:

```
Claim 1: POST /orders rejects negative quantity with 422
  Evidence:     test_orders.py::test_negative_quantity_rejected (unit)
  Falsified by: base ref a1b2c3d -> FAILED (returned 201)
  Verdict:      PROVEN

Claim 2: retry backoff caps at 30s
  Evidence:     test_retry.py::test_backoff_cap (unit)
  Falsified by: base ref a1b2c3d -> PASSED
  Verdict:      VACUOUS -- test is green without the change; it asserts the loop
                bound, not the cap

Claim 3: 30% faster under load
  Evidence:     logs/bench.txt (n=20, p50 412ms head vs 588ms base)
  Falsified by: same harness, both trees
  Verdict:      PROVEN (p95 distributions overlap; the p50 claim holds, a p95
                claim would not)

Claim 4: no regression for existing SSO users
  Evidence:     none -- no test exercises the SSO path
  Verdict:      UNPROVEN
```

Print the same matrix to the terminal. It is the primary output; the file exists so it can be pasted.

## Delivery

Text-shaped evidence pastes inline and needs no hosting — prefer it for everything that is not inherently visual.

1. Print the matrix.
2. Offer once to post `EVIDENCE.md` as a comment on the open PR or MR for the branch.
3. Media only for the claims the Step 3 plan approved. Run each tree's dev server on its own port and capture both, per "Capturing visual evidence" above.

### Getting media into the review

Resolve the host from `git remote get-url origin` **before** capturing anything. The two forges are not comparable here, and the difference is large enough to change what evidence is worth producing:

| | GitLab | GitHub |
|---|---|---|
| Official upload API | Yes — documented | None |
| Works on private repos | Yes | No |
| Getting a rendered image | `glab api` uploads it | The user drags the file in |

On GitLab, media is a solved problem — capture freely when a claim is visual. On GitHub there is no upload path at all, so a screenshot costs the reviewer a manual step that a transcript would not. When either would prove the same claim on GitHub, produce the transcript.

**GitLab — `glab` does it.** [`POST /projects/:id/uploads`](https://docs.gitlab.com/api/project_markdown_uploads/) returns a ready-to-paste `markdown` field, private projects included. Go through `glab` rather than `curl`: it reuses the existing `glab auth` session, so there is no PAT to plumb and no instance URL to construct.

```bash
glab api --method POST "projects/:fullpath/uploads" \
  --form "file=@evidence/media/checkout-after.png"
```

Paste the response's `.markdown` value into the MR comment verbatim. Use `--form` for the file — it cannot be combined with `--field` or `--raw-field`. If `glab` is not installed or not authenticated, say so and fall back to printing local paths; do not hand-roll the upload with `curl`.

**GitHub — no upload path.** There is no official API, and `gh` has no attachment command; `/upload/policies/assets` rejects token auth with a 422 (cli/cli#12960, cli/cli#13256). Do not push media to a branch, and do not shell out to third-party extensions.

Print the local paths and tell the user the files are there to drag into the comment:

```
Media captured (drag into the PR comment to embed):
  .agentic/<slug>/evidence/media/checkout-before.png
  .agentic/<slug>/evidence/media/checkout-after.png
```

`gh-attach` and `gh-image` are gh extensions that automate this against an undocumented internal endpoint. Mention they exist if the user asks; do not invoke them.

## Guidelines

- Read-only. `/prove` never edits repo source, never touches the user's working tree, and never pushes anything. Mutations happen in throwaway worktrees and are discarded.
- Never capture and never install before the Step 3 plan is approved. Detecting what is available is fine; spending on it is not.
- Never chain into `/create-pr` or `/build`. An UNPROVEN claim routes the user back to `/build`; say so and stop.
- Report VACUOUS findings first and without softening. A reviewer trusting a vacuous test is the failure mode this skill exists to prevent.
- Do not judge code quality, naming, or structure. That is `/review-suite`.
- Prefer under-claiming. "The p50 claim holds, the p95 claim does not" beats "faster".
- Clean up worktrees even on failure.
- Plain text only. No emojis. No AI attribution in any posted comment.
