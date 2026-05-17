---
name: fetch-context
description: >-
  Pull external context into the current repo: up-to-date library documentation
  via `context7-cli`, and full upstream source code via shallow `git clone` into
  `.agentic/sources/<repo>/`. Use whenever the user asks about a specific
  library, framework, SDK, or CLI tool — even well-known ones — since training
  data may not reflect recent API changes. Also use when the user wants to read,
  grep, or reference an upstream project's source locally.

  Always use for: API syntax questions, configuration options, version migration
  issues, "how do I" questions mentioning a library name, debugging
  library-specific behavior, and any request to "go read the source of X" or
  "clone X so we can look at it".
---

# fetch-context

Two ways to bring external context into the working directory:

1. **Docs** — query Context7 via `context7-cli` for current documentation and code snippets.
2. **Source** — shallow-clone an upstream git repo into `.agentic/sources/<repo>/` so Read/Grep can use it directly.

Use docs first for API questions. Reach for a source clone when docs aren't enough — when the user wants to read implementation details, grep across the codebase, or trace behavior the docs don't cover.

---

## Docs: `context7-cli`

Two-step workflow: search for a library ID, then fetch docs by ID. Always do both steps — never skip the search.

```bash
context7-cli search <query>          # list matching libraries
context7-cli get-docs <id>           # fetch docs for a known ID (e.g. /fastapi/fastapi)
```

The CLI also has a `lucky` subcommand that auto-picks the top search hit. **Do not use it.** Always inspect search results and pick deliberately — `lucky` hides the candidates, so you can't tell when the top hit is wrong.

IMPORTANT: Do not run these commands more than 3 times per question. If you cannot find what you need after 3 attempts, use the best result you have.

### Step 1: search

```bash
context7-cli search "fastapi dependency injection"
context7-cli search "nextjs app router middleware" --limit 5
context7-cli search "react" --id-only --limit 3
```

Options:

| Flag | Purpose |
|---|---|
| `--sort-by <field>` | Sort results (default: `stars`) |
| `--limit <n>` | Cap result count |
| `--id-only` | Print only library IDs, one per line — useful for piping |

Use a descriptive query that reflects the user's intent, not just the library name. Better disambiguation when multiple libraries share a name. Never include secrets (API keys, credentials, proprietary code) in the query.

### Selecting a result

Each result lists name, description, code-snippet count, source reputation (High/Medium/Low/Unknown), benchmark score (max 100), and any indexed versions.

Pick by:
1. Name match to what the user named.
2. Description relevance to the user's question.
3. Higher code-snippet count and benchmark score.
4. Higher source reputation.

If multiple matches look equally plausible, acknowledge and proceed with the best; don't silently guess. If nothing fits, say so and suggest a refined query rather than forcing a bad ID.

### Step 2: get-docs

```bash
context7-cli get-docs /fastapi/fastapi
context7-cli get-docs /vercel/next.js
```

Library IDs are `/<org>/<project>` and require the leading slash. If the user pins a version and the search output exposed it, use `/<org>/<project>/<version>`.

### Writing good queries

The query directly affects result quality.

| Quality | Example |
|---|---|
| Good | `"How to set up JWT authentication in Express.js"` |
| Good | `"React useEffect cleanup with async operations"` |
| Bad | `"auth"` |
| Bad | `"hooks"` |

Use the user's full question as the query when possible. Vague one-word queries return generic results.

### When docs aren't enough

If the docs don't answer the question (missing detail, behavior not documented, you need to read the implementation), fall through to a source clone — see below.

---

## Source: shallow clone into `.agentic/sources/`

When the user wants to read or grep upstream code locally, clone it into `.agentic/sources/<repo>/` at the repo root. `.agentic/` is already gitignored across this workflow, and `sources/` is repo-scoped so the same clone is reusable across tasks rather than re-cloned per `.agentic/<slug>/`.

### Process

1. **Resolve the repo URL.** If the user gave a URL, use it. If they gave a name, ask which upstream they mean before cloning — don't guess. For Context7 results, the library ID often maps to `https://github.com/<org>/<project>` but confirm if it's not obvious.

2. **Derive the destination.** `.agentic/sources/<repo>/` where `<repo>` is the repo's basename (e.g. `fastapi`, `next.js`). Use the repo root of the current working directory — `git rev-parse --show-toplevel`.

3. **Check for an existing clone.**
   ```bash
   if [ -d .agentic/sources/<repo>/.git ]; then
     # Already cloned — fetch latest instead of re-cloning.
     git -C .agentic/sources/<repo> fetch --depth=1 origin
   fi
   ```
   If it exists, offer to `git fetch` rather than re-cloning. Only delete and re-clone with explicit user confirmation.

4. **Clone shallow by default.**
   ```bash
   mkdir -p .agentic/sources
   git clone --depth=1 <url> .agentic/sources/<repo>
   ```
   Shallow keeps disk and network cheap. If the user needs blame/log/history, deepen on request:
   ```bash
   git -C .agentic/sources/<repo> fetch --unshallow
   ```

5. **Report the path.** Tell the user the absolute and relative path so Read/Grep calls are easy:
   ```
   Cloned: .agentic/sources/fastapi/
   ```

### Refs, branches, tags

Default to the repo's default branch. If the user names a ref, pass it:

```bash
git clone --depth=1 --branch <ref> <url> .agentic/sources/<repo>
```

`<ref>` can be a branch or a tag. For arbitrary SHAs, clone then `git -C ... fetch --depth=1 origin <sha> && git -C ... checkout <sha>`.

### Reading the clone

After cloning, use Read/Grep/Glob directly on `.agentic/sources/<repo>/`. Treat it like any other code under the repo root — but never edit or commit from it, and don't `cd` into it (it's a separate git repo and would shadow the host repo's git state).

---

## Guidelines

- **Prefer docs over source for API questions** — docs are curated and faster to scan. Clone only when you need implementation detail.
- **Don't rely on training data for API details** — signatures, options, and version-specific behavior drift. Run `context7-cli` even for libraries you "know".
- **Surface quota errors honestly.** If `context7-cli` fails with a quota or auth error, tell the user, then answer from training knowledge with an explicit caveat that it may be outdated. Never silently fall back.
- **Library IDs need the leading slash** — `/facebook/react`, not `facebook/react`.
- **Never put secrets in queries** — `context7-cli` queries are sent to a third-party API.
- **`.agentic/sources/` is gitignored** — clones won't pollute the host repo. Don't `git add` anything inside it.
- **Don't `cd` into a clone** — operate on it via absolute or repo-root-relative paths so your shell stays in the host repo.
