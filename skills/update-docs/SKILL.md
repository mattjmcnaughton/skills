---
name: update-docs
description: Audit the repo's documentation against the current code, then update what's stale and add what's missing. Use when the user asks to "refresh the docs", "check the docs", or after a feature lands that may have left docs behind. Optional final step in the coding loop, after /review.
---

`/update-docs` finds every doc in the repo (and the docs that *should* exist but don't), checks each against the current code, and proposes a concrete set of edits. The user approves before any file is written.

This is broader than `/review`'s "Docs to update" line: it walks the whole repo, not just the current diff.

## Determine scope

Ask if the user hasn't already said:

- `full` — audit every doc in the repo against current code (default).
- `diff <ref>` — only audit docs touching code changed since `<ref>` (e.g. `main`, `HEAD~10`, last tag). Faster; appropriate after a feature lands.
- `path <glob>` — scope to a subtree (e.g. `docs/api/`, `packages/auth/`).

If `.agentic/<slug>/plan.md` exists, read it first — the optimization target and recent changes there frame the audit.

## Inventory: docs that exist

Find documentation files. Treat all of these as in-scope:

```bash
git ls-files \
  'README*' '*/README*' \
  'CHANGELOG*' '*/CHANGELOG*' \
  'CONTRIBUTING*' 'AGENTS.md' 'CLAUDE.md' \
  '*.md' '*.mdx' '*.rst' '*.adoc' \
  'docs/**' '.claude/rules/**' \
  'mkdocs.yml' 'docusaurus.config.*' 'docs.json'
```

Also include:

- Per-package/module READMEs in monorepos.
- API reference output (OpenAPI/Swagger, generated doc sites).
- Code-level docstrings on public APIs (Python `"""..."""`, JSDoc `/** */`, Go doc comments, Rust `///`).
- `--help` output strings in CLI entry points.
- Top-of-file header comments that describe purpose.
- Example files (`examples/`, `cookbook/`) — they double as documentation.

## Inventory: docs that *should* exist

For each, check the repo and flag if missing:

| Should exist | Trigger |
|---|---|
| Root `README.md` | Always |
| `CHANGELOG.md` (or release notes) | Repo has tagged releases or a `version` field |
| `CONTRIBUTING.md` | Repo accepts external contributions (public, has issues/PRs) |
| `CLAUDE.md` or `AGENTS.md` | Repo has non-trivial conventions an agent should know |
| Per-package README | Package is independently consumable (separate `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`) |
| Module/feature doc | New feature directory has no README/doc and the public surface is non-obvious |
| API reference | Public HTTP/gRPC/library API with no generated or hand-written reference |
| CLI usage doc | Binary entry point exists but `--help` isn't surfaced anywhere in markdown |
| ADR or design note | Significant architectural decision visible in code without rationale anywhere |

Don't manufacture work. If the repo is a 200-line script, it doesn't need an ADR directory.

## Staleness checks

For each doc, look for drift against the current code. Concrete checks:

1. **Named identifiers.** Grep the doc for function, class, command, flag, env var, file path, and config-key names. For each, verify the name still exists in the code (`git grep`, file lookup). Flag references to renamed or deleted symbols.

2. **Code blocks and examples.** For every fenced code block, check:
   - Imports/paths resolve.
   - Commands are real (binary exists, subcommand exists, flags exist).
   - API signatures match current source.
   - For runnable examples in a known language, consider running the snippet if the repo has the toolchain set up. Ask before executing.

3. **Versions and dependencies.** Compare versions cited in docs (`requires Node 18+`, `python >= 3.10`, `react 17`) against lockfiles, `engines`, `python_requires`, `go.mod`, etc. Flag mismatches.

4. **CLI `--help` vs docs.** If a CLI is documented, run `<bin> --help` (and per-subcommand help) and diff against the documented flags/subcommands. Ask before invoking unfamiliar binaries.

5. **Links.** Internal repo links (`./foo.md`, `../src/bar.ts`) must resolve to real files. For external links, do not fetch them as part of this skill — call them out as "out-of-scope, run a link checker" unless the user explicitly asks.

6. **Config and env vars.** Cross-reference documented env vars / config keys against the code that reads them (e.g. `process.env.X`, `os.getenv("X")`, `viper.GetString("x")`). Flag undocumented vars used in code, and documented vars no longer used.

7. **Setup / install / quickstart sections.** Walk the steps mentally against the current repo layout. Flag steps that reference moved/removed files, deprecated package managers, or commands that no longer exist.

8. **Diagrams and screenshots.** Note them but do not regenerate. Flag if the underlying UI or architecture obviously changed.

9. **Generated docs freshness.** If the repo has a doc generator (Sphinx, TypeDoc, OpenAPI codegen, `cargo doc`), check the generated-output timestamp / hash against the source. If stale, propose regeneration rather than hand-editing.

10. **Repo-specific conventions.** Read `CLAUDE.md`, `AGENTS.md`, `.claude/rules/*.md`. Apply any project rules about how docs are written or where they live.

## Categorize findings

For each issue:

- **Critical** — doc is wrong in a way that will actively mislead (broken example, deleted symbol referenced as current, install step that fails).
- **Suggestion** — doc is incomplete or out of date but not actively wrong (new feature undocumented, new config flag missing from reference, version range slightly behind).
- **Nit** — formatting, tone, dead-link-without-replacement, ordering.

If nothing is wrong, say so. Don't manufacture findings.

## Findings report

Present findings before editing. Use this format (write to `.agentic/<slug>/docs-audit.md` if a slug workspace exists, otherwise inline in the response):

```markdown
# Docs audit

**Scope**: <full | diff <ref> | path <glob>>
**Docs scanned**: <count>
**Missing docs**: <count>

## Missing
- <path that should exist> — <why it should exist>

## Critical
- <doc:line> — <what's wrong> → <proposed fix>

## Suggestions
- <doc:line> — <what's incomplete> → <proposed fix>

## Nits
- <doc:line> — <minor issue> → <proposed fix>

## Out of scope
- <link checking, screenshot regen, etc.>
```

## Apply edits

After the user reviews findings:

1. Ask which categories to apply: `critical only`, `critical + suggestions`, `all`, or `let me pick`.
2. For each accepted finding, make the edit. Prefer `Edit` over `Write` so changes are minimal and reviewable.
3. For *missing* docs, draft the new file from current code (read the actual source — don't hallucinate API shape) and show the user the draft before writing it.
4. For generated docs, run the generator command rather than hand-editing the output. Show the command first.
5. Do not commit. Leave staging to the user or `/create-commit`.

## Guidelines

- **Read the code, don't guess.** Before claiming a symbol is renamed or a flag is gone, grep for it. Memory of "what the code looked like" is unreliable.
- **Prefer small, surgical edits.** A stale paragraph gets rewritten; the surrounding doc stays. Don't rewrite a whole README because three sentences drifted.
- **Match the doc's voice.** Look at how the file is currently written (tense, person, formality) and stay consistent. Don't introduce a new style mid-document.
- **Don't add docs the project doesn't want.** If `CLAUDE.md` or `CONTRIBUTING.md` says "no inline JSDoc" or "READMEs only at package root", respect it.
- **No AI attribution** in any doc, generated comment, or commit. Never add "generated by Claude" / "AI-assisted" footers unless the user explicitly asks.
- **Plain text only.** No emojis in any doc this skill writes, even if the surrounding doc has them — flag the existing emoji as a separate nit if relevant.
- **Stop on ambiguity.** If a doc and the code disagree and it's not obvious which is correct (the code might be the bug, not the doc), ask the user before editing either.
