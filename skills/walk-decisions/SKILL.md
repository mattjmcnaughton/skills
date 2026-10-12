---
name: walk-decisions
description: Walks through a supplied set of decisions in manageable chunks, defaulting to one at a time, with an AI recommendation for each. Use when asked to walk through decisions, help choose between options, or work through a decision list together.
---

# Walk Decisions

Help the user make a supplied set of decisions without confronting them with the whole questionnaire at once. Recommend; do not decide on their behalf.

## Start

- Use the decisions supplied in the conversation or named document. If none are available, ask for the list or source and wait.
- Keep the scope to that set. Do not turn this into an exhaustive design interview or implementation plan.
- Default to **one decision per turn**. If the user requests a chunk size, use up to that many decisions per turn; they can change it at any point. Do not ask them to configure the default before starting.
- Give decisions stable labels (D1, D2, etc.), preserving supplied identifiers when present. Briefly state the number of decisions and begin the first chunk, without dumping every question up front.
- Address prerequisites before dependent choices. Preserve the supplied order otherwise. Do not put a dependent choice in the same chunk if its options or recommendation depend on an unanswered choice.

## Present each chunk

For each decision, show:

1. **Decision:** its label, a short title, and the concrete question to settle.
2. **Options:** the viable choices and their main tradeoffs, usually two or three. Do not invent alternatives merely to fill a quota.
3. **Recommendation:** explicitly name the recommended option and give a short rationale grounded in the user's goals, constraints, and previous answers. State the main downside and any assumption that could change the recommendation.
4. **Your choice:** ask the user to accept the recommendation, pick another option, propose an alternative, or defer.

End the turn and wait for the user's answer before presenting another chunk. A recommendation is not an accepted decision; silence is not consent.

Keep analysis proportional to the stakes. Inspect directly relevant available sources when a recommendation depends on facts; distinguish verified facts from assumptions. If missing context would materially change the recommendation, ask only the necessary clarification and wait. Give a provisional recommendation when useful, but do not manufacture certainty.

Example, with the default chunk size:

> **D1 — Where should the export run?**
>
> **A. In the request:** simpler, but long exports can time out.
> **B. In a background job:** handles long exports, but adds queue and status handling.
>
> **Recommendation: A**, assuming exports stay small and finish comfortably within the request timeout. It avoids operating a queue; the downside is that larger exports would need a different approach.
>
> Accept A, choose B, suggest another approach, or defer?

## Incorporate the answer

- Briefly acknowledge the choice and its rationale. Track each decision as pending, decided, or deferred in the conversation; keep the user's choice distinct from your recommendation.
- If the answer is ambiguous, clarify rather than guessing. For a partially answered chunk, keep unanswered items pending and resolve or explicitly defer them before advancing.
- If the user asks for more analysis, discuss the current decision without advancing. Respect requests to skip, revisit, change chunk size, or stop.
- Apply accepted choices to later recommendations. If a revised choice invalidates an earlier dependent decision, flag it for reconsideration rather than silently rewriting the user's answer.
- Do not repeatedly re-ask deferred items. Continue with independent decisions; when only deferred or blocked items remain, summarize and ask whether to revisit them or finish.
- If the user explicitly delegates a choice to you, record it as delegated and explain the selection. Otherwise leave the choice to them.

## Finish

When all decisions have been addressed, or the user asks to stop, provide a compact recap: decision label, chosen option, short rationale, and any deferred question or condition still open. Do not describe deferred decisions as resolved.

Keep the record in the conversation unless the user asks for a file or an update to an existing document. Choosing an option does not authorize implementation, publishing, or other external actions.
