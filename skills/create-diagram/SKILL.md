---
name: create-diagram
description: Author and render diagrams in Mermaid, Graphviz, Excalidraw, or TikZ. Picks a format based on intent, writes source plus a rendered SVG, and either uses an externally managed Kroki (via KROKI_HOST_URL) or the bundled docker-compose stack.
---

# create-diagram

Create and render diagrams as code. Source plus rendered SVG are written side by side so diagrams stay editable. All rendering goes through Kroki — either an externally managed instance you point at via `KROKI_HOST_URL`, or the bundled docker-compose stack you start on demand.

## Formats

Pick the format that matches the user's intent, not the format they named (unless they were explicit).

| Format | When to pick | File extension |
|---|---|---|
| `mermaid` | Default. Sequence, flowchart, state, class, ER, gantt. Renders inline on GitHub/GitLab. Best when the diagram lives next to docs. | `.mmd` |
| `graphviz` | Dependency graphs, call graphs, large node-edge graphs. Also the right choice when another tool emits DOT (e.g. `terraform graph`, `go mod graph`). | `.dot` |
| `excalidraw` | Sketchy, whiteboard aesthetic. Architecture brainstorms, informal docs, anything where "rough" is part of the point. | `.excalidraw` |
| `tikz` | Publication-quality figures, precise positioning, math/CS papers, anything where the user mentions LaTeX. | `.tex` |

If the user names a format explicitly, honor it. If they don't, infer from the request and state your choice in one sentence before generating.

## CLI

Use the bundled `render.sh` wrapper. It resolves which Kroki to talk to, health-checks it, and POSTs the diagram source to the right endpoint.

```bash
./skills/create-diagram/render.sh <command> [args...]
```

| Command | Purpose |
|---|---|
| `render <type> <source-file> <output-svg>` | Render a diagram to SVG. Fails fast if Kroki is not healthy. |
| `start` | Start the bundled Kroki containers. Disabled when `KROKI_HOST_URL` is set. |
| `stop` | Stop the bundled Kroki containers (`docker compose down`). Disabled when `KROKI_HOST_URL` is set. |
| `status` | Print whether Kroki is healthy; exit 1 if not. |

`render` never auto-starts the stack. If Kroki is not healthy, it prints how to start it and exits non-zero.

## Choosing a Kroki

Before the first render, decide which Kroki to use:

1. **External Kroki** — if `KROKI_HOST_URL` is set in the environment (a self-hosted instance, a CI sidecar, a team-shared deployment), the script uses it directly and refuses to manage docker compose. Run `status` to confirm it is reachable.
2. **Bundled docker-compose stack** — if `KROKI_HOST_URL` is unset, the script targets `http://localhost:18473` and manages the bundled stack via `start`/`stop`.

When `KROKI_HOST_URL` is unset and Kroki is not healthy, **ask the user before running `start`**. Bringing the stack up pulls ~1 GB on first run and leaves long-running containers on their machine. One sentence is enough: "Kroki is not running. OK to bring up the bundled docker-compose stack?"

Once running, leave it running across sessions. Only run `stop` if the user asks for cleanup.

## Output layout

Write source and SVG side by side under `diagrams/` at the repo root:

```
diagrams/
├── auth-flow.mmd
├── auth-flow.svg
├── service-deps.dot
├── service-deps.svg
├── architecture-sketch.excalidraw
└── architecture-sketch.svg
```

Override the location only when the user names a specific path. Keeping source next to SVG means future edits read the source, modify it, and re-render — no round-tripping from rendered output.

## Patterns

### Mermaid — sequence diagram

```bash
cat > diagrams/auth-flow.mmd <<'EOF'
sequenceDiagram
  participant U as User
  participant A as API
  participant DB as Database
  U->>A: POST /login
  A->>DB: SELECT user
  DB-->>A: row
  A-->>U: JWT
EOF

./skills/create-diagram/render.sh render mermaid diagrams/auth-flow.mmd diagrams/auth-flow.svg
```

### Graphviz — dependency graph

```bash
cat > diagrams/service-deps.dot <<'EOF'
digraph services {
  rankdir=LR;
  api -> auth;
  api -> billing;
  billing -> stripe;
  auth -> db;
  billing -> db;
}
EOF

./skills/create-diagram/render.sh render graphviz diagrams/service-deps.dot diagrams/service-deps.svg
```

### Excalidraw — sketch

Excalidraw source is JSON. Authoring by hand is verbose; for deep authoring, see `references/excalidraw.md` for the JSON wrapper, element templates, and a section-by-section build strategy for large diagrams. Alternatively, have the user draw at excalidraw.com and export `.excalidraw` JSON.

```bash
./skills/create-diagram/render.sh render excalidraw diagrams/architecture-sketch.excalidraw diagrams/architecture-sketch.svg
```

**Authoring defaults for modern (non-sketchy) output:**

- `fontFamily: 3` (Excalidraw's sans), `fontSize: 16` for body, larger for titles.
- `roughness: 0` for clean edges. Use `1` only when the user explicitly wants a hand-drawn feel.
- `opacity: 100` for every element. Use color, size, and stroke width for hierarchy — not transparency.
- `strokeWidth: 2` is the default; `1` for thin connectors, `3` only for emphasis.

**Default to free-floating text.** Not every label needs a box. Add a container only when the shape carries meaning, arrows bind to it, or it groups other elements. The test: "would this work as text with no box?" If yes, drop the box.

**Pattern → shape mapping** (pick from intent):

| Concept | Shape |
|---|---|
| Start, entry, input | `ellipse` |
| End, exit, output | `ellipse` |
| Process, action, step | `rectangle` |
| Decision, conditional | `diamond` |
| Abstract state, context | overlapping `ellipse` |
| Timeline marker, bullet | small `ellipse` (10-20px) |
| Hierarchy node | `line` + free-floating text (no box) |
| Section title, label | free-floating `text` (no box) |

### TikZ — publication figure

Source must be a complete LaTeX document (preamble plus `\begin{document}`...`\end{document}`), not just a `tikzpicture` block.

```bash
cat > diagrams/state-machine.tex <<'EOF'
\documentclass[tikz,border=5pt]{standalone}
\usetikzlibrary{automata,positioning}
\begin{document}
\begin{tikzpicture}[->,auto,node distance=2cm]
  \node[state,initial] (q0) {$q_0$};
  \node[state,right=of q0] (q1) {$q_1$};
  \node[state,accepting,right=of q1] (q2) {$q_2$};
  \path (q0) edge node {a} (q1)
        (q1) edge node {b} (q2);
\end{tikzpicture}
\end{document}
EOF

./skills/create-diagram/render.sh render tikz diagrams/state-machine.tex diagrams/state-machine.svg
```

### Editing an existing diagram

Read the source file next to the SVG, modify it, then re-render to the same SVG path. Do not edit the SVG directly — it gets overwritten on next render.

### Render-view-fix loop

You cannot judge a diagram from source alone — layout, overlap, arrow routing, and text clipping only show up in the rendered output. After rendering, **Read the SVG file** and check for:

- Text clipped by or overflowing its container.
- Shapes or text overlapping unintentionally.
- Arrows crossing through elements or landing on the wrong target.
- Lopsided composition (one section cramped while another is empty).
- Labels floating ambiguously, not clearly anchored to what they describe.

Fix the source, re-render, re-read. Typical comprehensive diagrams take 2-4 iterations. This loop matters most for Excalidraw (positional, easy to misalign) and TikZ (compile errors and overflow are silent in source), less for Mermaid and Graphviz where the layout engine handles spacing.

## Kroki lifecycle (bundled stack only)

The skill ships a `docker-compose.yml` with four services on two Docker networks:

- `proxy` — Caddy reverse proxy. The only container with host port exposure (`127.0.0.1:18473 → :8080`). Lives on both networks.
- `core` — Kroki gateway (handles Graphviz and TikZ natively). Internal network only.
- `mermaid` — companion container, headless browser-based renderer. Internal network only.
- `excalidraw` — companion container, headless browser-based renderer. Internal network only.

The `internal` network has `internal: true`, meaning containers on it cannot reach the internet. Renderers cannot phone home, fetch external fonts, or load remote images. The `proxy` straddles `internal` and a normal bridge network so it can both forward requests to `core` and publish a host port.

`core` runs with `KROKI_SAFE_MODE=secure`, which disables risky features like remote `!include` directives in PlantUML.

First `start` pulls images (~1 GB total, one-time) and brings everything up. Subsequent renders hit running containers and are fast. Containers keep running across sessions until `./skills/create-diagram/render.sh stop`.

If port `18473` is already in use, point at a different port via `KROKI_HOST_URL=http://localhost:<port>` (and edit the compose file's port mapping if you still want the bundled stack on that port).

When `KROKI_HOST_URL` is set, `start`/`stop` are disabled — the script assumes the user owns the Kroki lifecycle.

### Trust boundary

`proxy` is the sole ingress point and the only container with internet egress. Hardening lives here naturally — when you need auth, mTLS, rate limiting, or request logging, replace the inline `caddy reverse-proxy` command with a mounted Caddyfile and add the directives there without touching the renderer containers.

## Guidelines

- **Always write source plus SVG.** Source so the diagram is editable; SVG so it is viewable in a browser or embedded in markdown.
- **Pick the format from intent.** If unsure, default to Mermaid — it renders inline on GitHub and covers the most common diagram types.
- **State your choice before generating.** One sentence: "Going with Graphviz since this is a dependency graph." Lets the user redirect cheaply.
- **Check `KROKI_HOST_URL` first.** Run `render.sh status` before any render. If unhealthy and `KROKI_HOST_URL` is unset, ask the user before running `start` — do not silently bring up containers.
- **TikZ source must be a full document**, not a bare `tikzpicture`. Kroki's TikZ backend compiles the document with `latex`.
- **Do not edit SVGs directly** — they are derived artifacts. Edit the source and re-render.
- **Read the rendered SVG to validate.** Source alone can't reveal overlap, clipping, or bad arrow routing. After every render, Read the SVG and iterate.
- **For Mermaid in READMEs**, consider skipping the SVG and embedding the fenced ```mermaid block directly — GitHub renders it natively. The skill still helps you draft the source.
- **Do not commit `.agentic/sources/`** — Kroki upstream lives there only during `/fetch-context` lookups and is gitignored.
