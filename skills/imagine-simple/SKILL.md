---
name: imagine-simple
description: Steps back from the current problem or approach, imagines what it would look like if it were simple, and proposes specific constraints the user could relax to get there, with what each relaxation buys and costs. Use when a solution feels complicated, when the user asks "what if this were simple", or when a design keeps growing.
---

# What if it were simple?

Stop working forward from the current approach. Picture the simple version,
find the constraints that keep you from it, and offer the user specific ones to
relax. The user decides; you suggest.

Other skills keep the constraints fixed: `ponytail` minimizes an implementation
of fixed requirements, and `pressure-testing-scope` cuts commitments while
preserving the stated outcome. This skill questions the constraints themselves.

## Choose the subject

- Use the user's argument when given, such as `/imagine-simple the sync design`.
- Otherwise use the problem and approach currently under discussion: the plan,
  design, bug fix, or implementation the conversation is working on.
- Read what you need to ground the constraints: the code, plan, ticket, docs,
  and earlier messages. Inspection only.

## Think it through

1. **Restate the goal** in one sentence as the outcome someone needs, not the
   approach. "Customers see their order status," not "build a status WebSocket."
2. **Sketch the simple version.** Describe in a few concrete sentences what the
   solution would be if it were easy: the obvious, boring design someone would
   build in an afternoon. Ignore the awkward constraints for now.
3. **Find what stands in the way.** List the constraints that separate the
   current approach from the simple version. Look for:
   - stated requirements, such as real time, every platform, or zero downtime;
   - unstated assumptions, such as "it must be general", "it must handle any
     scale", or "users will expect X";
   - inherited constraints, such as an existing API, data model, compatibility
     promise, tool choice, or team convention;
   - self-imposed ones from the current approach itself.
4. **Check each one.** Say where it comes from: who asked for it, which code or
   document requires it, or that nobody stated it. Check the evidence when it is
   cheap, such as usage data, callers, or a ticket, and say when a constraint is
   unverified.
5. **Check the approach too.** If the complexity comes from the approach rather
   than any constraint, say so and name the simpler approach under the same
   constraints.

Hold security, privacy, data integrity, legal and compliance, and accessibility
fixed. Do not propose relaxing them unless the user raises it; list any that
drive the complexity as "held".

## Present it

- **Goal:** the one sentence.
- **The simple version:** the sketch.
- **Constraints worth relaxing:** at most five, ranked by simplicity gained
  for the cost. For each:
  - the constraint and where it comes from (stated, assumed, or inherited;
    verified or not);
  - the concrete relaxation, such as "nightly batch instead of real time",
    "one region only", "a manual step for the rare case", or "drop v1 clients,
    which made no calls in 30 days";
  - what it removes: components, code paths, states, dependencies, or work;
  - what it costs and who notices;
  - how easily it can be reversed later.
- **Held:** constraints that are real and drive complexity but should stay, in
  one line each.
- **Recommendation:** which relaxations you would take together, and what the
  approach becomes if the user accepts them, in two or three sentences.

Example of one entry:

> **Real-time updates** (stated in the ticket; the only consumer is the daily
> ops review). Relax to a page that refreshes every five minutes. Removes the
> WebSocket server, reconnect logic, and the pub/sub dependency. Cost: status
> can be up to five minutes stale. Easy to reverse; the read API stays the same.

If the current approach is already close to the simple version, say so in a
sentence or two and stop. Do not invent relaxations to fill the list.

## Boundaries

End by asking which relaxations the user wants, then wait. A suggested
relaxation is not an accepted one. Do not change plans, code, or tickets until
the user chooses, and then only as far as the task they ask for.
