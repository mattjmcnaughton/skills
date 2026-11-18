---
name: give-example
description: Walks through a concrete, step-by-step example of a concept, mechanism, or proposal from the current conversation, using its actual code, data, and names; for a bug or edge case, real or hypothetical, shows the actions that would actually trigger it. Use when the user asks for an example, a worked example, a walkthrough, or "show me how that works".
---

# Give an example

Make the idea the user is trying to understand concrete. The example must come
from the current conversation, not from a generic textbook case.

## Choose what to illustrate

- Use the user's argument when given, such as `/give-example the retry backoff`.
- Otherwise illustrate the main point of your most recent substantive
  explanation, proposal, or answer. If the last message covered several ideas,
  pick the one most likely to be confusing and name it in your first sentence so
  the user can redirect you.
- Ask which idea they mean only when the candidates are equally likely and an
  example of the wrong one would waste their time. Then wait.

## Build the example

- Use the conversation's own material: the files, functions, data shapes,
  commands, tickets, and terms already discussed. When the example depends on
  how the code actually behaves, read the relevant source rather than guessing.
- Pick small, concrete values: three items rather than N, a real-looking ID
  rather than `foo`. Choose values that exercise the interesting part, such as
  the branch, boundary, or failure the explanation was about.
- Say which values are invented for illustration and which come from the actual
  code or data.
- Do not introduce new concepts, alternatives, or recommendations. The example
  explains what was already said.

## Present it

1. **Setup:** one or two sentences naming what the example shows and the
   starting state or input.
2. **Steps:** a numbered list. Each step says what happens and the resulting
   state, such as variable values, file contents, request and response, or
   queue contents. Show code or output only where it carries the step. Mark the
   step where the key behavior happens.
3. **Result:** the final state or output, and one or two sentences tying it back
   to the original explanation.

### When the topic is a bug or edge case

When the explanation describes a bug or failure, whether observed, suspected,
or hypothetical, or an edge case the code might mishandle, answer "what would
actually cause this to happen?" The example is the sequence of actions that
triggers it:

- Work backward from the outcome. Name the conditions that must all hold at
  once, such as specific data, timing, configuration, input, or an earlier
  failure. Then find real actions that produce each one. Read the code paths
  involved rather than assuming them.
- If no realistic sequence reaches it, for example because validation upstream
  rejects the input or the only caller never passes that value, say so and show
  where the path is blocked. That is a useful answer, not a failure.
- If several distinct triggers exist, show the most likely one in full and list
  the others in one line each.
- Start from a realistic state that users or callers actually reach, such as
  existing data, configuration, or a logged-in session.
- Make each step an action at a real entry point: a UI click or form input, an
  API request, a CLI command, a job run, or a function call from its actual
  caller. Then show what the code does in response, naming the function or file.
- For races and ordering bugs, interleave the actors on one timeline and show
  the order that breaks.
- Mark the step where the behavior goes wrong and show expected versus actual
  there.
- When it is cheap, give the trigger in a form the user can rerun, such as a
  `curl` command, a test case, or click-by-click steps.
- Say whether the sequence was observed, for example in a log, a failing test,
  or a reproduction earlier in the conversation, or only traced from the code.
  Do not run it to find out unless the user asks.

Add a short contrast case only when the idea is a distinction, such as
"before vs. after the fix" or "cache hit vs. miss", and the contrast is what makes
it click. Keep it to the steps that differ.

Keep it proportionate: usually 4 to 8 steps. If the full trace would be long,
collapse routine steps ("steps 3 to 5 repeat for the remaining items") and keep
detail on the interesting one.

## Boundaries

This is explanation only. Do not edit files, run commands with side effects, or
continue the underlying task. Read-only inspection to get the example right is
fine. After the example, stop and let the user respond.
