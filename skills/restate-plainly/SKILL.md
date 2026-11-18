---
name: restate-plainly
description: Restates the most recent explanation, or a named part of the conversation, in simpler everyday language without losing what matters. Use when the user asks for plain English, simpler terms, an ELI5, a non-jargon version, or says they did not follow.
---

# Restate in plain English

Rewrite something already said so the user can follow it on first read. Change
the wording, not the substance.

## Choose what to restate

- Use the user's argument when given, such as `/restate-plainly the rollback risk`.
- Otherwise restate your most recent substantive message. If the user quoted or
  pointed at one part of it, restate only that part.
- Use the rest of the conversation to judge what the user already knows. Do not
  re-explain things they have shown they understand, and do not skip a term they
  have not seen before.

## Rewrite it

- Open with the gist in one or two sentences: what is true, and why it matters to
  the user.
- Use short sentences and everyday words. Prefer active voice and concrete
  subjects: "the job retries three times", not "retry semantics are applied".
- Replace jargon with plain description. When a term is needed later, such as a
  function, file, or project term the user will see again, keep it and explain
  it in a short clause the first time.
- Keep every fact, caveat, and risk that affects what the user should believe or
  do. Drop detail that does not. If you drop something notable, say it in one
  line ("I left out the retry timing details; ask if you want them").
- Do not add new claims, recommendations, or analysis. If restating exposes an
  error or gap in the original, say so plainly rather than smoothing it over.
- Use an analogy only when it closely matches the mechanism, and say where it
  stops matching. A bad analogy is worse than none.
- Make it shorter than the original. Use a short list for sequences or several
  parallel points; otherwise use prose.
- Keep the tone direct and respectful. Simpler does not mean condescending.

End with what this means for the user: the decision, action, or question in
front of them, when there is one.

## Boundaries

This is explanation only. Do not edit files or continue the underlying task.
After the restatement, stop and let the user respond. If they want a concrete
walkthrough instead, `give-example` covers that.
