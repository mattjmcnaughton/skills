# skills

Hand-authored skills for Claude Code and Codex. Symlink into `~/.claude/skills` and `~/.codex/skills` to install.

Remote skills from other git repos are managed separately by [`skillvendor`](../skillvendor/).

## Install

```bash
ln -sfn "$(pwd)/skills" ~/.claude/skills
ln -sfn "$(pwd)/skills" ~/.codex/skills
```

Both clients discover any subdirectory containing a `SKILL.md`.

## Skills

### Coding loop

The skills below compose into one flow: scope a task, build it, review it, ship it, clean up.

| Skill | Role |
|---|---|
| `/create-worktree` | Initialize an isolated git worktree, branch, and `.agentic/<slug>/` workspace |
| `/prep` | Interview the user; produce a single `plan.md` (goal, optimization target, acceptance criteria, verification plan, research, environment readiness, steps) |
| `/build` | Execute `plan.md` step by step; always write `diary.md`; ask up front about checkpoint commits and TDD |
| `/review` | Pre-commit self-review of local changes against `plan.md`; output `review.md` |
| `/rehydrate` | Reload context from `plan.md` + `diary.md` after a `/clear` or interruption |
| `/create-commit` | Conventional Commits message for staged changes (or a specified scope) |
| `/create-pr` | Push the branch and open a GitHub PR with title/body derived from `plan.md` + `diary.md` |
| `/review-pr` | Review an open GitHub PR (yours or others'); adapts depth via mode (iteration/standard/critical/security) |
| `/merge-pr` | Merge an approved PR via rebase and delete the remote branch |
| `/delete-worktree` | Tear down the local worktree and branch created by `/create-worktree` |

Typical sequence: `/create-worktree` → `/prep` → `/build` → `/review` → `/create-commit` → `/create-pr` → (optional `/review-pr` from a teammate) → `/merge-pr` → `/delete-worktree`. `/rehydrate` slots in anywhere after `/prep`. `/ship-gate` (see below) is an optional manual checkpoint before `/create-pr` and again before `/merge-pr`.

### Other skills

Standalone helpers, not part of the coding loop.

| Skill | Role |
|---|---|
| `/update-docs` | Audit the repo's docs against current code; propose and apply edits. Optional step after `/review`. |
| `/draft-api-client` | Interview the user about an API client and draft a plan covering a clean client, contract tests, a fake client, and an opt-in integration test. Hand off to `/build`. |
| `/draft-job-map` | Interview the user about a broad space and produce a concise, precise Jobs-to-Be-Done map: actors, jobs, circumstances, competing alternatives, success criteria. Pairs with `/hire-job-map`. |
| `/hire-job-map` | Take a job map and stack-rank candidate solutions per job. Biased toward existing OSS / self-hostable options; includes "keep the current hire" and "build from scratch" as honest baselines. Hands off to `/fetch-context` and `/audit-third-party` for verification. |
| `/fetch-context` | Pull external context into the repo: library docs via `context7-cli`, upstream source via shallow `git clone`, or web pages via `r.jina.ai`. |
| `/audit-third-party` | Audit a third-party codebase (cloned via `/fetch-context`) for data-exfiltration channels, persistence, auth/config defaults, and dependency risk. Produces a finding list and a maximum-security configuration baseline. |
| `/parquet-duckdb` | Explore and query Parquet files (local or S3-compatible) via the DuckDB CLI. |
| `/create-diagram` | Author and render diagrams in Mermaid, Graphviz, Excalidraw, or TikZ. Writes source plus a rendered SVG via an external Kroki (`KROKI_HOST_URL`) or the bundled docker-compose stack. |
| `/setup-permissions` | Configure `.claude/settings.local.json`, `.codex/config.toml`, `.codex/rules/default.rules`, and AGENTS.md so an agent can run lint/fmt/test/gate without prompts. Run on a new repo. |
| `/add-permissions` | Add a single focused permission grant to the repo's agent allowlist, written symmetrically for Claude and Codex. Use after a one-off prompt instead of rerunning `/setup-permissions`. |
| `/ship-gate` | Fast pre-ship checklist on the branch diff: secrets, garbage files, machine-specific paths, debug residue, dead/duplicated code, commit hygiene, local gate. Optional manual checkpoint before `/create-pr` and `/merge-pr`. |
| `/workflow-catalog` | Probe a codebase for user-facing workflows (routes, pages, CLI subcommands, service endpoints), interview to confirm, and write `docs/workflows.md` with stable `WF-<DOMAIN>-NNN` IDs. Pairs with `/workflow-audit`. |
| `/workflow-audit` | Read `docs/workflows.md` and report unit/integration/e2e test coverage per workflow by linking tests via explicit pins, ID references, name matches, page URLs, or import heuristics. Writes `docs/workflow-coverage.md`. |

## Conventions

- **One artifact directory per task**: `.agentic/<slug>/`, created by `/create-worktree`. The coding-loop skills read/write `plan.md`, `diary.md`, `review.md`, and `ticket.json` inside it.
- **Plain text only.** No emojis in any skill output, commit message, or document.
- **No AI attribution** in commits, PRs, or generated content unless the user explicitly asks for it.
- **Skills can route to other skills** by invoking the Skill tool with the target skill name. Used sparingly; most v1 skills are standalone.

## Layout

```
skills/
├── add-permissions/SKILL.md
├── audit-third-party/SKILL.md
├── build/SKILL.md
├── create-commit/SKILL.md
├── create-diagram/SKILL.md
├── create-pr/SKILL.md
├── create-worktree/SKILL.md
├── delete-worktree/SKILL.md
├── draft-api-client/SKILL.md
├── draft-job-map/SKILL.md
├── fetch-context/SKILL.md
├── hire-job-map/SKILL.md
├── merge-pr/SKILL.md
├── parquet-duckdb/
│   ├── SKILL.md
│   └── duckdb-parquet.sh
├── prep/SKILL.md
├── rehydrate/SKILL.md
├── review/SKILL.md
├── review-pr/SKILL.md
├── setup-permissions/SKILL.md
├── ship-gate/SKILL.md
├── update-docs/SKILL.md
├── workflow-audit/SKILL.md
└── workflow-catalog/SKILL.md
README.md
LICENSE
```

## License

MIT — see [LICENSE](LICENSE).
