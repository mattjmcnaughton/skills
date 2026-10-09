# skills

Hand-authored skills for Claude Code and Codex, plus pinned upstream skills in `skills/vendor/`. Symlink individual skill directories into `~/.claude/skills` and `~/.codex/skills` to install.

Vendored skills include their resources, upstream license, and an `UPSTREAM.md` recording the source revision. They need no separate fetch at installation time.

## Install

### With skillvendor

Use [skillvendor](https://github.com/mattjmcnaughton/skillvendor) with two source entries in `~/.config/skillvendor/skills.yaml`. Discovery checks immediate child directories, so `path: skills` does not discover the nested vendored skills:

```yaml
skills:
  - repo: github.com/mattjmcnaughton/skills
    ref: main
    path: skills
  - repo: github.com/mattjmcnaughton/skills
    ref: main
    path: skills/vendor
```

Merge these entries into your existing manifest, preserving any `targets` and other sources, then run `skillvendor sync`. Add an `include` list to the vendor entry to select individual skills; include the dependencies listed below too. Avoid installing the same skill name from both this repo and its original upstream.

The two entries have independent lock records. `skillvendor` symlinks whole skill directories from its cached checkout, so licenses, provenance, and resources remain accessible. It does not apply frontmatter overrides or patches. Make durable customizations in this repository, not its cache, and record them in the skill's `UPSTREAM.md`. Remote installation sees only revisions published to the selected ref, not local uncommitted changes.

### Direct links from a local checkout

Run from this repository's root. These Bash commands install first-party and vendored skills as direct children of each client's skill directory; they do not rely on recursive discovery. Existing installations are preserved, not overwritten.

If you used the old whole-directory symlink installation, first inspect `readlink ~/.claude/skills` and `readlink ~/.codex/skills`. For each link that points to this repository's `skills/`, remove **only that symlink** with `unlink ~/.claude/skills` or `unlink ~/.codex/skills`. Do not remove a real directory. The commands below will create replacement directories.

```bash
(
  set -eu
  root="$(pwd)/skills"
  for target in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
    if [ -L "$target" ]; then
      printf 'Migrate the whole-directory symlink first: %s\n' "$target" >&2
      exit 1
    fi
  done
  for target in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
    mkdir -p "$target"
    for source in "$root"/* "$root"/vendor/*; do
      [ -f "$source/SKILL.md" ] || continue
      destination="$target/$(basename "$source")"
      if [ -e "$destination" ] || [ -L "$destination" ]; then
        printf 'Keeping existing installation: %s\n' "$destination"
      else
        ln -s "$source" "$destination"
      fi
    done
  done
)
```

To install just one vendored skill, link its directory directly (the destination skill directory must be a real directory, not the old whole-directory symlink):

```bash
mkdir -p ~/.claude/skills
ln -sT "$(pwd)/skills/vendor/ponytail-review" ~/.claude/skills/ponytail-review
```

This single-skill example requires GNU `ln -T` to fail rather than write inside an existing destination directory. On macOS, use the portable bulk installer above, limiting its `for source` list to the desired skill directories if needed. Substitute `~/.codex/skills` for Codex. Keep the checkout at the same path while using these links. To replace an existing installation, inspect and remove its old link yourself first; the bulk installer deliberately skips conflicts.

### Vendored skills

| Skill | Upstream | Also install |
|---|---|---|
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | — |
| `ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | — |
| `thermo-nuclear-code-quality-review` | [cursor/plugins](https://github.com/cursor/plugins) | — |
| `grill-me` | [mattpocock/skills](https://github.com/mattpocock/skills) | `grilling` |
| `grill-with-docs` | [mattpocock/skills](https://github.com/mattpocock/skills) | `grilling`, `domain-modeling` |
| `grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | — |
| `domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | — |
| `handoff` | [mattpocock/skills](https://github.com/mattpocock/skills) | — |
| `wait-what` | [mattpocock/skills](https://github.com/mattpocock/skills) | — |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills) | — |

`handoff` writes a temporary context-transfer document; it complements the plan/diary-based `/rehydrate`. Its overlays enable model invocation in response to a user command, while its description prohibits unsolicited execution. `wait-what` asks for a clearer explanation and retains upstream's explicit-only invocation policy. `ponytail` enables a persistent minimal-implementation mode; `ponytail-review` is a standalone review and does not call or require it. These three additions use the revisions already pinned for their respective upstream repositories.

The original six snapshots were selected to match the previously installed skills, not necessarily the latest upstream releases. Local customizations now enable model invocation for thermonuclear review and the grilling wrappers, keep thermonuclear review advisory, and require consent before starting a grilling interview. Each affected `UPSTREAM.md` records the changes. `frontend-design` is an additional Apache-2.0 snapshot from Anthropic's skills repository; its instructions match the requested Claude Code plugin revision, but this source also supplies the referenced license. See its `UPSTREAM.md` for both revisions.

To update one, fetch the chosen revision from its `UPSTREAM.md` repository, review the complete skill directory and license, replace the snapshot including resources, and update `UPSTREAM.md`. Record any local modifications there and reapply them deliberately when updating upstream. Do not silently refresh to upstream HEAD or drop copyright notices. Direct local symlinks see changes to this checkout; reload skills or restart the client as needed. Separate Amp global skills are not updated by this process.

## Skills

### Coding loop

The skills below compose into one flow: scope a task, build it, review it, ship it, clean up.

| Skill | Role |
|---|---|
| `/create-worktree` | Initialize an isolated git worktree, branch, and `.agentic/<slug>/` workspace |
| `/prep` | Interview the user; produce a single `plan.md` (goal, optimization target, acceptance criteria, verification plan, research, environment readiness, steps) |
| `/build` | Execute or resume `plan.md`; preserve progress in `diary.md`; ask about checkpoint commits and TDD only when not recorded |
| `/review-suite` | Run the installed code-quality review lenses in parallel, dedupe their findings, and always save the report to `.agentic/review.md` |
| `/resolve-review` | Plan and execute review fixes using the existing task plan; address clear issues, ask about ambiguous decisions, and record every finding's disposition |
| `/prove` | Produce falsifiable evidence that the change does what it claims; falsify each artifact against the base tree; report PROVEN / VACUOUS / UNPROVEN per claim |
| `/rehydrate` | Reload context from `plan.md` + `diary.md` after a `/clear` or interruption |
| `/create-commit` | Conventional Commits message for staged changes (or a specified scope) |
| `/create-pr` | Push the branch and open a GitHub PR with title/body derived from `plan.md` + `diary.md` |
| `/sync-remote` | Amend the current commit with pertinent follow-up edits, force-push safely, and refresh its GitHub PR or GitLab MR description |
| `/review-pr` | Review an open GitHub PR (yours or others'); adapts depth via mode (iteration/standard/critical/security) |
| `/merge-pr` | Merge an approved PR via rebase, request remote branch deletion where supported, and leave local cleanup to `/delete-worktree` |
| `/delete-worktree` | Tear down the local worktree and branch created by `/create-worktree` |

Typical sequence: `/create-worktree` → `/prep` → `/build` → `/review-suite` → `/resolve-review` → `/prove` → `/create-commit` → `/create-pr` → (optional `/sync-remote` after follow-up edits) → (optional `/review-pr` from a teammate) → `/merge-pr` → `/delete-worktree`. `/rehydrate` slots in anywhere after `/prep`. `/build` establishes that the implementation works, `/review-suite` judges how it is written, `/resolve-review` addresses its findings without committing or publishing, and `/prove` packages falsifiable evidence from the final reviewed diff. You can prepare `/prove`'s capture plan while review runs, but capture after resolving review findings so the evidence still describes the code being shipped. `/ship-gate` (see below) is an optional manual checkpoint before `/create-pr` and again before `/merge-pr`.

### Other skills

Standalone helpers, not part of the coding loop.

| Skill | Role |
|---|---|
| `/static-html` | Create a polished, self-contained HTML page with embedded React, compiled Tailwind CSS, and assets; works offline when opened directly in a browser. |
| `/kaizen` | Confirm accessible project chat sessions over a time range, then recommend evidence-backed repo and agentic coding skill improvements. Prefers `agent-logs-extractor` with native-source fallbacks. |
| `/update-docs` | Audit the repo's docs against current code; propose edits and apply them after approval. Optional step after `/review-suite`. |
| `/correctness-review` | Adversarial diff review for logic bugs and weak tests, supplemented by relevant correctness cheat sheets |
| `/security-review` | Reachability-first review for exploitable vulnerabilities, supplemented by relevant OWASP cheat sheets |
| `/pressure-testing-scope` | Pressure-test a PRD, technical design document, or implementation plan; classify commitments to keep, cut, defer, or justify, then propose the minimum coherent scope. |
| `/fetch-context` | Use the `fetch-context` CLI to clone upstream repositories or fetch web pages as Markdown, with raw-command fallbacks when the CLI is unavailable. |
| `/audit-third-party` | Audit a third-party codebase (cloned via `/fetch-context`) for data-exfiltration channels, persistence, auth/config defaults, and dependency risk. Produces a finding list and a maximum-security configuration baseline. |
| `/audit-skill` | Read-only audit of skills in `~/.claude/skills`, `~/.codex/skills`, and `~/.agents/skills` (or supplied paths). Treats all target files as untrusted; inventories all external interactions and reports malicious behavior, risky capabilities, and coverage gaps without activating skills. |
| `/parquet-duckdb` | Explore and query Parquet files (local or S3-compatible) via the DuckDB CLI. |
| `/create-diagram` | Author and render diagrams in Mermaid, Graphviz, Excalidraw, or TikZ. Writes source plus a rendered SVG via an external Kroki (`KROKI_HOST_URL`) or the bundled docker-compose stack. |
| `/upload-files` | Explicitly launch a Python drag-and-drop upload server via uv (or Python fallback) on `0.0.0.0` with a random port; receive files in gitignored `.agentic/uploads` under the current directory. |
| `/ship-gate` | Fast pre-ship checklist on the branch diff: secrets, garbage files, machine-specific paths, debug residue, dead/duplicated code, commit hygiene, local gate. Optional manual checkpoint before `/create-pr` and `/merge-pr`. |
| `/workflow-catalog` | Probe a codebase for user-facing workflows (routes, pages, CLI subcommands, service endpoints), interview to confirm, and write `docs/workflows.md` with stable `WF-<DOMAIN>-NNN` IDs. Pairs with `/workflow-audit`. |
| `/workflow-audit` | Read `docs/workflows.md` and report unit/integration/e2e test coverage per workflow by linking tests via explicit pins, ID references, name matches, page URLs, or import heuristics. Writes `docs/workflow-coverage.md`. |

## Conventions

- **One artifact directory per task**: `.agentic/<slug>/`, created by `/create-worktree`. The coding-loop skills read/write `plan.md` and `diary.md` inside it. Ticket context is optional: `ticket.json`, free-form `ticket.md`, or no ticket are all supported. If both ticket files exist, read both and resolve material conflicts rather than silently preferring one. `/review-suite` instead always writes the latest report to `.agentic/review.md` at the worktree root.
- **Review resolution**: `/resolve-review` consumes the review report and keeps its fix plan in `.agentic/<slug>/review-resolution.md`, separate from the original `plan.md`.
- **Tracker-agnostic tickets**: GitHub, Linear, Jira, and other trackers are supported as context sources. Preserve their identifiers and URLs; use supplied context when an integration is unavailable. Only use tracker-specific closing syntax when its meaning is known.
- **Plain text only.** No emojis in any skill output, commit message, or document.
- **No AI attribution** in commits, PRs, or generated content unless the user explicitly asks for it.
- **Skills can route to other skills** by invoking the Skill tool with the target skill name. Used sparingly; most v1 skills are standalone.

## Layout

```
skills/
├── audit-third-party/SKILL.md
├── audit-skill/SKILL.md
├── build/SKILL.md
├── create-commit/SKILL.md
├── create-diagram/
│   ├── SKILL.md
│   ├── render.sh
│   ├── docker-compose.yml
│   └── references/excalidraw.md
├── create-pr/SKILL.md
├── create-worktree/SKILL.md
├── correctness-review/SKILL.md
├── delete-worktree/SKILL.md
├── fetch-context/SKILL.md
├── kaizen/SKILL.md
├── merge-pr/SKILL.md
├── parquet-duckdb/
│   ├── SKILL.md
│   └── duckdb-parquet.sh
├── prep/SKILL.md
├── pressure-testing-scope/SKILL.md
├── prove/SKILL.md
├── rehydrate/SKILL.md
├── resolve-review/SKILL.md
├── review-suite/SKILL.md
├── review-pr/SKILL.md
├── security-review/SKILL.md
├── ship-gate/SKILL.md
├── static-html/SKILL.md
├── sync-remote/SKILL.md
├── update-docs/SKILL.md
├── upload-files/
│   ├── SKILL.md
│   └── scripts/server.py
├── vendor/                     # Ten upstream skills with licenses and UPSTREAM.md
├── workflow-audit/SKILL.md
└── workflow-catalog/SKILL.md
README.md
LICENSE
```

## License

First-party content is MIT — see [LICENSE](LICENSE). Under `skills/vendor/`, `frontend-design` retains Apache-2.0 in its `LICENSE.txt`; the other nine skills retain upstream MIT licenses and copyright notices in their own `LICENSE` files. Preserve the applicable licenses and notices when redistributing, and mark modified Apache-2.0 files as changed. See each `UPSTREAM.md` for provenance. Vendoring does not transfer upstream authorship or replace their licenses with this repository's MIT license.
