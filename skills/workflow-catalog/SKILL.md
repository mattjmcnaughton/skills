---
name: workflow-catalog
description: >-
  Probe a target codebase (or a monorepo of codebases) for user-facing
  workflows, propose candidates grouped by domain, interview the user to
  confirm/reject/edit, and write the result to a markdown file (default
  `docs/workflows.md`). Each workflow gets a stable ID of the form
  `WF-<DOMAIN>-NNN`. Re-runs preserve existing IDs and propose deltas
  interactively. Use when the user asks to "list the workflows in this app",
  "catalog the user flows", "what workflows do we have", "build a workflow
  inventory", or as the input step before `/workflow-audit` checks test
  coverage per workflow. Triggers include "catalog workflows", "map user
  flows", "what end-to-end flows exist", "inventory the workflows".
---

`/workflow-catalog` builds a stable, human-curated list of the user-facing workflows a codebase supports. A workflow is a unit of progress the user is trying to make end-to-end — "log in", "checkout cart", "reset password", "deploy a build" — not an internal code path. The skill probes the code for candidates, surfaces what the probe will miss, runs an interview to accept/reject/edit, and writes a markdown file that downstream skills (notably `/workflow-audit`) can read.

The output file is the contract. Every workflow has an ID like `WF-CHECKOUT-001`. IDs are stable across re-runs.

## When to use

- The user wants a written inventory of what their app actually does for users.
- The user is about to run `/workflow-audit` and there's no `docs/workflows.md` yet.
- A new module/area shipped and the catalog needs a top-up — re-run preserves IDs and proposes additions.
- A teammate asks "what flows do we have here" while onboarding.

## When not to use

- To document internal architecture, modules, or code paths — that's `/update-docs`, or an architecture doc.
- To produce test cases or scenario specs — out of scope for v1 (deferred future skills `workflow-test`, `workflow-instrument`).
- To drive the application via a browser to discover flows at runtime — explicitly deferred for v1. This skill is codebase-probe only; it asks the user to fill probe gaps.
- To enforce a formal schema (YAML / Gherkin) — deferred. v1 output is flat markdown with stable IDs.

## Prerequisites

- A target repo to scan. Default is the current working directory; if the user is in a monorepo with separate frontend/backend trees, ask which paths to include (multiple is fine — workflows can span both).
- If `docs/workflows.md` (or the user-chosen path) already exists, treat this as a re-run. See "Re-run behavior" below.

## Process

### Step 1 — Confirm scope and output path

Ask, in one batched prompt, before any probing:

1. **Scope paths** — which directories to probe? Defaults: the repo root. For monorepos, ask for explicit roots (e.g. `apps/web`, `apps/api`, `packages/cli`).
2. **Output path** — default `docs/workflows.md`. The user can pick a different path (e.g. `docs/user-workflows.md`, `WORKFLOWS.md`).
3. **Re-run mode?** — if the output file exists, default to re-run (preserve IDs, propose deltas). Confirm before overwriting.

Read `.agentic/<slug>/plan.md` if a slug workspace exists — the optimization target there may say what to bias toward.

### Step 2 — Probe the codebase

Walk the target paths and enumerate candidate workflows per stack. The goal is to surface things the user might miss, not to be exhaustive — false positives are cheap, and the interview filters them.

For each candidate, capture: a short title, the file path(s) that suggested it, and a proposed domain (cluster key).

#### Web routes — server-side frameworks

Look for route definitions. Each route is a workflow candidate; group by route prefix or controller name.

| Stack | Where to look | Pattern |
|---|---|---|
| Next.js (App Router) | `app/**/page.tsx`, `app/**/route.ts` | One route per `page.tsx` or `route.ts`; folder name is the path segment |
| Next.js (Pages Router) | `pages/**/*.tsx`, `pages/api/**/*.ts` | One route per file |
| React Router | `routes.tsx`, `App.tsx`, `<Route path=...>` JSX | Grep `<Route\b.*path=` |
| Rails | `config/routes.rb` | Grep `resources :`, `get '/...'`, `post '/...'` |
| Django | `urls.py` files | Grep `path(`, `re_path(`, `url(` |
| FastAPI | router files | Grep `@router\.(get|post|put|patch|delete)`, `@app\.` |
| Express / Fastify | `app.ts`, route modules | Grep `app\.(get|post|put|patch|delete)\(`, `router\.(get|post|...)` |
| Phoenix (Elixir) | `lib/**/router.ex` | Grep `scope`, `get "/...`, `post "/..."` |

For each route, the workflow title is usually a verb-phrase derived from the path (`/checkout/confirm` → "Confirm checkout"). Don't blindly include every CRUD endpoint — group e.g. `GET /orders`, `POST /orders`, `PUT /orders/:id` under one workflow "Manage orders" unless they clearly correspond to distinct user-visible flows.

#### Frontend views — page components with route bindings

For SPAs without a server router (or in addition to one):

| Stack | Where to look | Pattern |
|---|---|---|
| React + React Router | `routes.tsx`, `router.tsx`, component tree | Grep `<Route\b`, `createBrowserRouter` |
| Vue Router | `router/index.ts`, `routes.ts` | Grep `path:` inside route arrays |
| SvelteKit | `src/routes/**/+page.svelte` | One route per `+page.svelte` |
| Nuxt | `pages/**/*.vue` | One route per file |
| Angular | `app-routing.module.ts` | Grep `path:` in `Routes` array |

Frontend pages often map 1:1 with server-side workflows. Don't double-count — note the frontend file as additional evidence for the same workflow rather than a separate one.

#### CLI subcommands

For CLI apps, each subcommand is a workflow candidate.

| Stack | Where to look | Pattern |
|---|---|---|
| Click (Python) | entry point file | Grep `@click\.command`, `@cli\.command`, `@<group>\.command` |
| argparse (Python) | parser setup | Grep `add_subparsers`, `add_parser(` |
| Typer (Python) | app file | Grep `@app\.command` |
| Cobra (Go) | `cmd/**/*.go` | Grep `&cobra\.Command{`, `Use:\s*"..."` |
| oclif (Node) | `src/commands/**` | One subcommand per file |
| Commander.js | entry file | Grep `\.command\(` |
| Rust clap | derive `#[command(...)]`, builder `.subcommand(` |
| Bash CLIs | `case "$1" in` blocks | Manual read |

Also grep entry-point `--help` strings if a binary is runnable in this repo; if a CI fixture runs the CLI, scan that for invoked subcommands.

#### Service endpoints — HTTP / RPC / GraphQL

| Stack | Where to look |
|---|---|
| OpenAPI / Swagger | `openapi.yaml`, `swagger.json`, `**/openapi/*.yaml` |
| gRPC | `**/*.proto` — each `rpc` line is a workflow candidate |
| GraphQL | `schema.graphql`, `**/*.gql`, resolver files | Group by mutation/query, not by field |
| AsyncAPI | `asyncapi.yaml` |
| tRPC | router files; grep `\.mutation\(`, `\.query\(` |

Schema-first sources (OpenAPI, proto, GraphQL SDL) are the cheapest probe — one file lists everything.

#### Background jobs and scheduled tasks

User-triggered jobs (a workflow ends in "this gets queued") count. Pure infrastructure cron (rotate logs, vacuum DB) does not.

- `Sidekiq`, `Resque`, `Celery`, `BullMQ`, `RQ`, `Inngest`, `Trigger.dev` — grep for worker / task / job definitions.
- Cron / scheduled functions — only if user-visible (e.g. "send weekly digest").

#### Webhooks and event handlers

Inbound webhook handlers (`POST /webhooks/stripe`) are workflows if the user-facing outcome differs from a plain API call ("Stripe charge succeeded → upgrade plan"). Otherwise group under the affected domain.

### Step 3 — Workflows the probe will miss

After the mechanical probe, ask the user about the categories the probe routinely misses. Present this as a short prompt:

> The probe scanned routes, pages, CLI commands, and service endpoints. It will typically miss workflows that don't have a dedicated URL or command. Are any of these in scope here?

- **Auth / session flows** — login, logout, refresh, MFA challenge, password reset (the route exists but the flow spans more than one route).
- **Onboarding** — signup → email verify → first-run wizard → activated.
- **Account lifecycle** — email change, password change, account deletion, data export.
- **Billing flows** — start subscription, upgrade, downgrade, cancel, dunning, refund.
- **Payment failures** — 3DS challenge, declined card retry, webhook-driven status update.
- **Multi-step wizards** — anything that pages across multiple URLs.
- **In-app side effects** — "invite teammate sends email", "publish post triggers webhook".
- **Background-triggered user-visible events** — "weekly digest sent", "trial expired email".
- **Error / recovery paths** — "session expired → re-auth", "rate limited → retry".

Don't enumerate all of these every time — pick the ones most plausible for this stack and ask. Record any the user adds as workflow candidates with file references where possible (or `(no single file)` when the flow spans many).

### Step 4 — Cluster into domains

Group candidates into domains. Domain inference, in priority order:

1. Top-level route prefix (`/checkout/*` → `CHECKOUT`, `/auth/*` → `AUTH`).
2. Directory / module name (`app/billing/` → `BILLING`, `cmd/deploy/` → `DEPLOY`).
3. Controller / router file name (`OrdersController` → `ORDERS`).
4. Ask the user.

Domain names are upper-snake-case (`USER_SETTINGS`, not `UserSettings` or `user-settings`). Keep them short — one or two words.

For an existing file (re-run), reuse the domains already there; only propose new ones for candidates that don't fit.

### Step 5 — Present candidates and run the interview

Show the user the candidate list, grouped by proposed domain. Format:

```
Proposed domains and candidates:

AUTH
  - Log in — app/auth/login/page.tsx, POST /api/auth/session
  - Log out — POST /api/auth/session DELETE
  - Reset password — app/auth/reset/page.tsx, POST /api/auth/reset

CHECKOUT
  - Add to cart — POST /api/cart
  - Confirm order — app/checkout/confirm/page.tsx, POST /api/orders
  - View order history — app/orders/page.tsx, GET /api/orders

...
```

Then offer the user these actions, one round at a time:

- **accept** — keep the candidate as proposed.
- **reject** — drop the candidate (e.g. it's not user-facing, or it's covered by another).
- **rename** — change the title.
- **edit description** — fill in or fix the one-line description.
- **merge** — fold two candidates into one (common: `POST /thing` and `GET /thing` describe the same workflow).
- **split** — break one candidate into two (e.g. "Manage orders" → "Place order" + "View orders").
- **move** — reassign to a different domain.
- **add** — add a workflow the probe missed (one-shot prompt for probe-misses; see Step 3).

Iterate until the user says "done". Then ask once more: "Anything missing?" — that's the final probe-misses sweep.

### Step 6 — Assign IDs and write the file

ID format: `WF-<DOMAIN>-NNN`.

- `<DOMAIN>` matches the domain heading exactly.
- `NNN` is zero-padded three digits.
- Next ID per domain is `max(existing IDs in this domain) + 1`. Start at `001`.
- **Never silently renumber.** On re-run, deleted IDs leave a gap; the gap stays.

Write the file in this format:

```markdown
# Workflows

<!-- Generated by /workflow-catalog. Re-runs preserve IDs and propose deltas. -->
<!-- Format: WF-<DOMAIN>-NNN — <title> — <one-line description> -->

## AUTH

WF-AUTH-001 — Log in — User authenticates with email and password and receives a session.
WF-AUTH-002 — Log out — User ends their session and is redirected to the public landing page.
WF-AUTH-003 — Reset password — User requests a reset email, clicks the link, and sets a new password.

## CHECKOUT

WF-CHECKOUT-001 — Add to cart — User adds an item to the cart from a product page.
WF-CHECKOUT-002 — Confirm order — User reviews cart contents and submits payment.
WF-CHECKOUT-003 — View order history — User views their past orders with status.
```

Rules for the line shape — `workflow-audit` parses this exact form:

- One workflow per line.
- Three em-dash-separated fields: ID, title, description.
- ID matches `^WF-[A-Z0-9_]+-\d{3}$`.
- Title is human, single sentence-case phrase.
- Description is one line. No trailing period required.
- Blank line between domains; no blank lines inside a domain block.
- Domain heading is `## <DOMAIN>`.

### Step 7 — Optional: pin test mappings

Below each workflow line, the user can optionally pin specific test files so `workflow-audit` skips its heuristic linking. Annotation form:

```markdown
WF-AUTH-001 — Log in — User authenticates with email and password and receives a session.
<!-- tests: tests/auth/login.spec.ts, e2e/auth.e2e.ts:"login with valid credentials" -->
```

The annotation lives on the line immediately after the workflow. Comma-separated entries; each entry is `<file>` or `<file>:<test-name>`. `workflow-catalog` does not generate these on first pass — it only documents the format so users can add them. If the format feels overengineered when authoring, skip it and let `workflow-audit` rely on heuristics.

## Re-run behavior

When the output file already exists:

1. **Read and parse it.** Build a map of `<DOMAIN> → [WF-IDs]`.
2. **Preserve every existing ID.** Even if the user wants to delete a workflow, the ID is not reused. Removed workflows are simply taken out of the file; the next addition in that domain gets `max(existing) + 1`, leaving a numeric gap.
3. **Probe fresh.** Run the codebase probe again from scratch.
4. **Diff against existing.** Classify each existing entry as:
   - **matched** — probe found supporting evidence, no change needed.
   - **stale** — probe found no supporting evidence; ask the user whether to keep, edit, or remove.
   - **edit candidate** — probe found different evidence (title drift, file moved); propose an edit.
5. **Propose additions.** Probe candidates that don't match any existing ID are presented as additions. Run the same interview as a fresh catalog.
6. **Confirm before writing.** Show the user the full delta — added, edited, removed — and write only after approval.

## Worked example

A user runs `/workflow-catalog` in a small monorepo with `apps/web` (Next.js) and `apps/api` (FastAPI).

**Probe surfaces:**

```
Routes found:
  apps/web/app/login/page.tsx
  apps/web/app/signup/page.tsx
  apps/web/app/dashboard/page.tsx
  apps/web/app/cart/page.tsx
  apps/web/app/checkout/page.tsx
  apps/api/routers/auth.py — POST /auth/login, POST /auth/signup, POST /auth/logout
  apps/api/routers/cart.py — GET /cart, POST /cart, DELETE /cart/{id}
  apps/api/routers/orders.py — POST /orders, GET /orders, GET /orders/{id}
```

**Proposed grouping:**

```
AUTH
  - Log in — apps/web/app/login/page.tsx, POST /auth/login
  - Sign up — apps/web/app/signup/page.tsx, POST /auth/signup
  - Log out — POST /auth/logout

CART
  - Add to cart — POST /cart
  - View cart — apps/web/app/cart/page.tsx, GET /cart
  - Remove from cart — DELETE /cart/{id}

CHECKOUT
  - Confirm order — apps/web/app/checkout/page.tsx, POST /orders
  - View orders — GET /orders
  - View order detail — GET /orders/{id}
```

**Probe-misses prompt:** "Looks like auth, cart, and checkout are covered. Are password reset, email verification, or account deletion in scope?" — user answers: "Password reset yes, others no."

**Interview moves:** user accepts AUTH and CHECKOUT as-is, merges "Add to cart" and "Remove from cart" under "Manage cart" in CART, renames "Confirm order" to "Place order", adds `WF-AUTH-004 — Reset password` from the probe-misses sweep.

**Final file at `docs/workflows.md`:**

```markdown
# Workflows

<!-- Generated by /workflow-catalog. Re-runs preserve IDs and propose deltas. -->
<!-- Format: WF-<DOMAIN>-NNN — <title> — <one-line description> -->

## AUTH

WF-AUTH-001 — Log in — User authenticates with email and password and receives a session.
WF-AUTH-002 — Sign up — New user creates an account with email and password.
WF-AUTH-003 — Log out — User ends their session and is redirected to the public landing page.
WF-AUTH-004 — Reset password — User requests a reset email and sets a new password via tokenized link.

## CART

WF-CART-001 — View cart — User views the items currently in their cart.
WF-CART-002 — Manage cart — User adds items to and removes items from their cart.

## CHECKOUT

WF-CHECKOUT-001 — Place order — User reviews cart contents and submits payment to create an order.
WF-CHECKOUT-002 — View orders — User views their past orders with status.
WF-CHECKOUT-003 — View order detail — User views a single order with line items and shipment status.
```

## Guidelines

- **Probe is a starting point, not the answer.** A clean probe with no interview turn produces a list of routes, not a list of workflows. The interview is where the value gets created — slow down for it.
- **One workflow per unit of user progress.** "Log in" is a workflow. "POST /auth/login" is a route. Group routes that compose into a single user-visible flow under one workflow.
- **Don't invent workflows.** If the probe found nothing and the user can't name it, it's not a workflow. Missing coverage is fine; fabricated coverage is harmful.
- **IDs are forever.** Once written, never reuse a number, never silently renumber. Downstream tools and docs may reference IDs.
- **Domains are clustering, not taxonomy.** Don't agonize over the perfect grouping. Good enough is good enough; the user can re-group on a future run.
- **Stay codebase-only.** v1 explicitly does not run the app, drive a browser, or query an external service. If the user wants those, capture as a follow-up for the deferred `workflow-explore` skill.
- **Plain text only.** No emojis in the output file or in interview prompts.
- **No AI attribution** in the generated file. The header comment is the only generator marker.
- **Stop on ambiguity.** If the user can't decide between two phrasings or two domains, present the trade-off and let them pick; don't auto-choose.
