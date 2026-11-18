---
name: cite-sources
description: Backs the claims in the most recent answer, or named claims from the conversation, with checkable sources such as file and line references, commits, command output, and documentation links with quoted passages, and marks what is unsupported or contradicted. Use when the user asks for sources, citations, evidence, "how do you know", or "where does it say that".
---

# Cite sources

Show where each claim comes from so the user can check it. Look the source up
now; do not cite from memory.

## Choose the claims

- Use the user's argument when given, such as `/cite-sources the timeout claim`.
- Otherwise cover your most recent substantive answer.
- Split it into the claims that matter: facts the user would act on or repeat.
  Skip framing, opinions you labeled as opinions, and claims the user supplied.
  For a long answer, cover the claims a decision rests on and say which ones
  you skipped.

## Find a source for each

Open or rerun the source and confirm it says what the claim says. Prefer the
most direct source:

1. **Code and config in the workspace:** the file path with a line range,
   pinned to the current commit when the file may change. Cite the line that
   does the thing, not a caller or a comment about it.
2. **Observed behavior:** a command you ran, a test, a log, or a query, with the
   command and the decisive lines of output. Note when and where it ran if that
   matters, such as which environment or branch.
3. **History:** the commit, pull request, or issue that introduced or decided it.
4. **External documentation and specifications:** the URL, the exact passage
   quoted, and the version or date it applies to. Prefer the official docs or
   source code of the project over blog posts and answers on forums. Check that
   the version matches the one the project uses.
5. **The conversation:** what the user or a tool said earlier, quoted.

Quote short excerpts, a line or two, so the user can see the support without
opening the source. Never invent a URL, path, line number, commit, or quote. If
you cannot reach a source, say so instead of citing it.

## Grade each claim

- **Supported:** the source states it directly.
- **Partly supported:** the source supports part of it, or only under a
  condition. Say which part or condition.
- **Inferred:** no source states it; it follows from sources you cite. Show the
  step from them to the claim.
- **Unsupported:** you found no source. Say what would settle it.
- **Contradicted:** the source says otherwise. Quote it and give the corrected
  claim.

## Present it

List the claims in the order of the original answer. For each: the claim in a
short sentence, its grade, and the sources with excerpts. Example:

> **Requests time out after 30 seconds.** Supported.
> `config/gunicorn.py` lines 12-13 at `a1b2c3d`: `timeout = 30`.
>
> **Retries are safe because the handler is idempotent.** Contradicted.
> `payments/handler.py` lines 40-48 create a charge on every call and send no
> idempotency key. Corrected: retries can double-charge.

Lead with any contradicted claims and corrections so they are not missed. End
with one line on what changed in the original answer, if anything.

## Boundaries

Read-only: look up, read, and rerun read-only commands to check sources. Do not
run commands with side effects, edit files, or continue the underlying task.
After the citations, stop and let the user respond.
