---
name: fetch-context
description: >-
  Pull external context into the current repo via the `fetch-context` CLI:
  shallow-clone an upstream repo (or whole GitHub org / GitLab group) into
  `.agentic/sources/repos/<host>/<owner>/<repo>/` so Read/Grep can use it
  directly, or fetch an arbitrary web page as clean markdown into
  `.agentic/sources/urls/<host>/<path>.md`. Use when the user wants to read,
  grep, or reference an upstream project's source locally, or when they hand
  you a URL (blog post, RFC, changelog, GitHub issue, vendor page) to read.

  Triggers include: "go read the source of X", "clone X so we can look at it",
  "what does X do under the hood", "read/summarize/extract from this URL".
---

# fetch-context

Two ways to bring external context into the working directory, both driven by the `fetch-context` CLI:

1. **Source** — clone an upstream git repo (or every repo in an org/group) into `.agentic/sources/repos/<host>/<owner>/<repo>/`.
2. **URL** — fetch a specific web page as clean markdown into `.agentic/sources/urls/<host>/<path>.md`.

Reach for source when the user wants to read implementation details, grep across an upstream codebase, or trace behavior. Reach for URL when the user gives you (or points you at) a specific page — blog post, RFC, changelog, GitHub issue, vendor docs page — that doesn't warrant a full clone.

---

## Preflight: is `fetch-context` installed?

Assume the CLI is installed and call it directly. Only check if a call fails with "command not found":

```bash
command -v fetch-context >/dev/null
```

If the binary is missing:

1. Tell the user `fetch-context` isn't installed and point them at the install instructions in the upstream README: <https://github.com/mattjmcnaughton/fetch-context#install>.
2. Then fall back to the raw commands documented in the **Fallback** subsection of each path so the immediate task isn't blocked. Be explicit when you do this — the fallback layout differs from the CLI layout, and the user should know they're on a degraded path.

---

## Source: `fetch-context repo`

Shallow-clone an upstream source into `.agentic/sources/repos/<host>/<owner>/<repo>/`.

```bash
fetch-context repo github.com/redis/redis
fetch-context repo github.com/foo/bar gitlab.com/acme/lib
```

- Accepts a host-qualified path (`github.com/foo/bar`) or a full clone URL.
- Shallow by default (`--depth=1`). `--depth N` controls history depth; `--depth 0` fetches full history. `--branch <name>` clones and tracks the named branch.
- Re-running the command **fetches and hard-resets the clone to the remote's latest** — any local edits inside the clone are wiped. Don't edit, don't commit from it, and don't `cd` into it (separate git repo; would shadow the host repo's git state).
- The tree is gitignored automatically by the CLI.

After cloning, report both paths so Read/Grep is easy:

```
Cloned: .agentic/sources/repos/github.com/redis/redis/
        (absolute: <repo-root>/.agentic/sources/repos/github.com/redis/redis/)
```

### Whole orgs / groups: `fetch-context group`

```bash
fetch-context group github.com/my-org
fetch-context group gitlab.com/acme/platform
```

- GitHub orgs are flat: every repo in the org is cloned.
- GitLab groups are recursive: subgroups are walked and their path is preserved (`gitlab.com/acme/platform/team/utils` → `sources/repos/gitlab.com/acme/platform/team/utils/`).
- Enumeration hits the host's REST API and almost always needs a token: `GITHUB_TOKEN` or `GITLAB_TOKEN` in the environment. Public single-repo clones via `repo` need no token.
- Clones run concurrently (default 4). Use sparingly — orgs can be large.

### Fallback (no `fetch-context` binary)

Flat layout, no host/owner prefix:

```bash
mkdir -p .agentic/sources
if [ -d .agentic/sources/<repo>/.git ]; then
  git -C .agentic/sources/<repo> fetch --depth=1 origin
else
  git clone --depth=1 <url> .agentic/sources/<repo>
fi
```

- Destination is `.agentic/sources/<repo>/` (just the basename) — **different from the CLI's `repos/<host>/<owner>/<repo>/` layout**. Call this out when you report the path.
- Pin a ref with `--branch <ref>` on the initial clone. Deepen later with `git -C .agentic/sources/<repo> fetch --unshallow` if blame/log is needed.
- Ensure `.agentic/` is gitignored in the host repo (the CLI does this for you; here you don't get it for free).

---

## URL: `fetch-context url`

Fetch a page (through `https://r.jina.ai/` under the hood, which strips boilerplate and returns clean markdown) and write it to `.agentic/sources/urls/<host>/<path>.md`.

```bash
fetch-context url https://example.com/blog/some-post
```

- The URL is wrapped literally; the page is sent to a third-party proxy. **Never pass a URL containing secrets** (tokens, signed URLs, session IDs). Strip or refuse.
- Re-fetching overwrites the existing markdown.
- A root URL with no path is written to `<host>/index.md`.
- Only fetch URLs the user provided or that you obtained from a trusted source (their repo, an upstream clone). Don't fetch URLs you fabricated.

After fetching, point Read at the resulting markdown file.

### Fallback (no `fetch-context` binary)

Use `WebFetch` against the same proxy and pass the user's question as the prompt so the response is filtered to what they actually want:

```
WebFetch(url="https://r.jina.ai/https://example.com/some/page", prompt="<user's question>")
```

If `WebFetch` isn't a fit (you need the raw body), `curl -sSL https://r.jina.ai/<URL>` works. Same secrets rule applies. The result is not written to disk in this path — quote or summarize inline.

---

## Profiles (saved bundles)

For repeat context sets, `fetch-context` supports named profiles defined in `~/.config/fetch-context/config.yaml`:

```bash
fetch-context load <profile>    # materialize a named bundle of repos/groups/urls
fetch-context list              # show defined profiles and what's on disk
fetch-context clean             # remove materialized content under the resolved target
fetch-context edit              # open the config in $VISUAL/$EDITOR/vi
```

Use `load` when the user references a saved bundle by name. Config-file schema lives in the upstream README — point the user at `fetch-context edit` rather than hand-authoring YAML for them.

---

## Guidelines

- **Don't rely on training data for API details** — signatures, options, and version-specific behavior drift. Clone the source if the user needs to verify behavior.
- **Never put secrets in URLs** — `r.jina.ai`-wrapped URLs are sent to a third-party proxy.
- **`.agentic/sources/` is gitignored automatically by the CLI.** On the fallback path, make sure `.agentic/` is in the host repo's `.gitignore` so clones don't leak into history.
- **Don't `cd` into a clone** — it's a separate git repo and would shadow the host repo's git state. Operate via absolute or repo-root-relative paths.
- **Don't edit or commit from a clone.** The CLI's refresh hard-resets to remote latest and will wipe local edits by design.
