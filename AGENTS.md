# Skill authoring guidance

## Repository layout

- First-party skills live in `skills/<name>/SKILL.md`. Edit that source, not an installed copy. `.agents/skills` and `.claude/skills` point to `skills/`.
- Keep `AGENTS.md` as the source of repository guidance and `CLAUDE.md` as a relative symlink to it.
- Read `README.md` for installation, the skill catalog, and coding-loop contracts. Update its catalog and layout when adding, renaming, or removing a skill.
- Vendored skills live in `skills/vendor/`. Preserve their licenses, resources, and pinned provenance; record local changes in `UPSTREAM.md`. Do not rename or refresh them just to match first-party conventions.

## Names and discovery

- Prefer imperative, lowercase, hyphen-separated names for new first-party skills: `walk-decisions`, `create-commit`, `review-pr`. This repository's convention takes precedence over generic advice to use gerunds. Do not mass-rename existing skills.
- Keep the directory name and YAML frontmatter `name` identical. When renaming, update invocation examples, cross-skill references, and README entries too.
- Frontmatter must include `name` and `description`. The description should state what the skill does and when to use it, in third person. Quote YAML values when punctuation requires it.

## Write focused instructions

- Give each skill one clear job. State its inputs, workflow, output, and stopping conditions; distinguish discussion, planning, review, and execution.
- Prefer one concise `SKILL.md`. Add scripts or reference files only when they remove real complexity or provide necessary executable behavior. Keep the main instructions under 500 lines.
- Write direct, actionable instructions rather than explaining concepts the agent already knows. Use concrete examples when they resolve ambiguity; avoid repeated rules and speculative options.
- Reuse established task artifacts and handoff contracts instead of inventing parallel state. Keep standalone helpers independent of the coding loop unless they actually need it.
- Keep skills portable across supported clients where practical. Do not require a client-specific tool for an interaction that plain conversation can handle.
- For interactive skills, specify defaults, when to wait for an answer, and how to handle missing inputs, partial answers, deferrals, and completion. Keep AI recommendations distinct from user-approved choices.
- Make side effects and approval boundaries explicit. A request for advice or an accepted recommendation does not itself authorize implementation, publishing, or destructive actions.
- Use plain text without emojis. Do not add AI attribution to generated content, commits, or PRs unless requested.

## Verify changes

- Re-read edited instructions for contradictions, broken references, and unintended changes to adjacent skills. Keep changes scoped to the requested behavior.
- Check frontmatter, directory/name agreement, referenced paths, and symlink targets. For renames, search for stale names.
- Run `git diff --check`. For executable changes, run the relevant scripts or tests against disposable inputs; never use shared data just to validate a skill.
- For behavioral instruction changes, exercise representative conversations when practical, including a non-default or ambiguous case. Structural checks alone do not prove an agent follows the workflow; report what was and was not tested.
- Reload skills when the client supports it. Report separately whether changes are local, committed, pushed, or merged; a local reload does not update remote installations.
