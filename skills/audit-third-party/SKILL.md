---
name: audit-third-party
description: >-
  Audit a third-party codebase (cloned locally via `/fetch-context`) for
  data-privacy and security risk before adopting or deploying it. Interviews
  the user about intended use and deployment context, then scans the source
  for outbound network calls, telemetry, data persistence, auth/secrets
  defaults, and dependency-supply-chain risk. Produces a terminal report with
  a headline verdict on data-exfiltration mechanisms, finding-driven
  recommendations, and a maximum-security configuration baseline for
  deployment. Use before adopting a self-hosted service, OSS framework, or
  vendor SDK — examples like `coder/coder`, `mastra-ai/mastra`, or any new
  tool the team plans to deploy. Triggers include "audit this repo", "audit
  this third-party", "is this safe to self-host", "what does this thing send
  out", "audit before we adopt X".
---

`/audit-third-party` answers three questions about a third-party codebase you're considering adopting:

1. **What can this software do with our data?** Specifically: when deployed as we intend to deploy it, can it leak, share, or exfiltrate data to third parties — and which of those channels are configurable vs. baked in?
2. **How should we configure it to close the gaps we found?** Finding-driven recommendations: specific env vars, config keys, CLI flags, and deployment choices that mitigate each finding.
3. **What's the maximum-security baseline?** A standalone deployment configuration — independent of the findings — that turns every available security and privacy knob to the most-locked-down setting the software supports. The user can apply this baseline first and then relax individual knobs where their threat model allows, rather than building security up from defaults.

The audit is intent-calibrated: a telemetry endpoint that's a non-issue in a managed SaaS deployment is a CRITICAL finding in an air-gapped one. The skill interviews the user up front to set that calibration before any scanning.

## When to use

- Before adopting a new self-hosted service or framework (e.g., `coder/coder`, `mastra-ai/mastra`).
- Before deploying an OSS tool into a regulated / air-gapped / data-sensitive environment.
- Before embedding a third-party SDK or library that will process production data.
- The user says: "audit this repo", "is this safe to deploy", "what does this thing phone home", "audit before we adopt X".

## When not to use

- To audit code in the current working repo — that's `/review`, `/review-pr`, or `/ship-gate`.
- As a substitute for a formal security review or pentest — this is a structured first-pass, not a deliverable for a compliance auditor.
- For runtime / dynamic analysis — this skill reads source only. If the user needs traffic capture, recommend running the service in a sandboxed VM with egress logging after this audit narrows the surface.
- When the target repo isn't cloned locally yet — route the user to `/fetch-context` first.

## Prerequisites

The target codebase must be cloned locally before this skill runs. Expected path: `.agentic/sources/<repo>/`, as produced by `/fetch-context`. If not present, stop and tell the user:

> The target repo isn't cloned locally. Run `/fetch-context` first with the GitHub URL, then re-run this skill.

Do not clone the repo yourself — that's `/fetch-context`'s job and keeps the source-management surface in one place.

## Process

### Step 1 — Interview the user about intent

Ask the user the following, in one batched question set. The answers calibrate every finding's severity in Step 3.

1. **Deployment model** — managed SaaS / self-hosted in our cloud / self-hosted on-prem / air-gapped (no internet egress).
2. **Data classes** — what data will flow through this software? (public / internal / customer PII / regulated — PHI/PCI/etc. / model inputs and outputs / source code).
3. **Egress policy** — is outbound internet from the deployment environment allowed at all? If yes, to which destinations (allow-list, broad)?
4. **Telemetry tolerance** — is vendor analytics / crash reporting / update-check pings acceptable, configurable-off-required, or forbidden?
5. **Features in scope** — which subset of this software's features will we actually use? (Many repos ship optional integrations that are off by default and can be ignored if the user won't enable them.)
6. **Auth model** — how will users authenticate? (SSO, local accounts, anonymous, machine-to-machine.)

Persist nothing. The interview answers stay in conversation context and inform Step 3 severity assignment. If the user wants the audit captured for later, Step 4 offers to write the report to a file.

### Step 2 — Map the codebase

Before scanning, get a quick lay of the land so you scan the right files.

- `README.md`, `CONTRIBUTING.md`, `docs/` — what does the project say it is?
- `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `Gemfile` — language(s), dependency manifests.
- `Dockerfile`, `docker-compose.yml`, `helm/`, `charts/`, `k8s/`, `deploy/` — deployment surface.
- `.env.example`, `config/`, `settings.*`, `*.config.*` — configuration knobs (this is where most recommendations will land).
- `CHANGELOG.md` or release notes — recent changes to telemetry/auth/data handling.

Note the latest commit SHA you're auditing (`git -C .agentic/sources/<repo> rev-parse HEAD`) so the report is reproducible.

### Step 3 — Run the four scans

Each finding gets: **category**, **severity** (CRITICAL / HIGH / MEDIUM / LOW / INFO), **evidence** (`file:line` citations from the cloned source), **configurable?** (yes/no + how), and **recommendation**.

Severity is calibrated against the Step 1 intent. Examples:

- A telemetry POST to `vendor.example.com` is **CRITICAL** if the user said "air-gapped" or "telemetry forbidden", **MEDIUM** if "configurable-off-required", **INFO** if "telemetry acceptable".
- A default admin password is **CRITICAL** regardless of deployment model.
- An optional Slack integration is **INFO** if the user said they won't use Slack integrations, even if the code is sloppy.

#### Scan A — Outbound network and telemetry (the headline)

This is the primary question. Be thorough. Bucket each finding by destination type.

- **Hardcoded URLs and hostnames** — grep for `https?://`, domain literals. Cite each unique destination.
  ```bash
  grep -rEn "https?://[a-zA-Z0-9.-]+" .agentic/sources/<repo> --include="*.{go,ts,js,py,rs,rb,java,kt}"
  ```
- **Analytics / product telemetry SDKs** — known names: Segment, PostHog, Mixpanel, Amplitude, Heap, Rudderstack, Snowplow, Google Analytics, Plausible. Check both source imports and config keys.
- **Crash reporting / observability** — Sentry, Bugsnag, Rollbar, Honeycomb, Datadog, New Relic, Dynatrace, OpenTelemetry exporters (note the configured endpoint).
- **Update-check / version pings** — code that fetches a remote manifest of "latest version" on startup or on a timer.
- **Model / AI API calls** — OpenAI, Anthropic, Cohere, Mistral, Bedrock, Vertex AI SDKs. Note what data is sent in prompts. **High-stakes for the data-exfiltration question** — model providers see every prompt.
- **Webhooks / outbound integrations** — Slack, Discord, PagerDuty, GitHub, custom webhook URLs.
- **Package / dependency fetches at runtime** — does the software download plugins, models, containers, or extensions from the internet at runtime? (vs. only at build time.)
- **License / activation pings** — phone-home for license validation.

For each finding, answer the four questions explicitly:

1. **What data is sent?** (User identifiers, IPs, hostnames, command-line args, prompt content, full request bodies, anonymized counters.)
2. **When is it sent?** (Startup, on every request, on a timer, on errors only.)
3. **Can it be disabled?** (Env var like `TELEMETRY_DISABLED=1`, config key, CLI flag, build flag, or no — recompile required.)
4. **Is the destination configurable?** (Can we point it at a self-hosted relay instead?)

Conclude this scan with an explicit one-paragraph **Exfiltration verdict**:

- **No outbound channels** — software is silent unless we configure it to talk.
- **Disable-able telemetry only** — channels exist but every one has an off switch documented and verified.
- **Required outbound channels** — at least one channel is not disable-able without source modification. List them.
- **Indeterminate** — code is large enough that this pass can't rule out hidden channels. Recommend a runtime egress-capture pass.

#### Scan B — Data persistence and storage

What does the software write, where, and is sensitive data handled correctly?

- **Database schemas / migrations** — what tables exist? Is PII or auth material stored? Is anything stored that the user didn't expect (audit logs of full request bodies, prompt history)?
- **Disk writes** — `open(..., 'w')`, `fs.writeFile`, log directories, cache directories, temp files. Note what's written.
- **Object storage** — `s3://`, `gs://`, `azure://` SDK calls or config keys.
- **Logging of sensitive data** — grep for `log.*password`, `log.*token`, `log.*secret`, `log.*auth`, full-request-body logging. Often the biggest accidental-exfil vector.
- **Encryption at rest defaults** — does the software encrypt data it persists, or does it rely on the storage layer? Are there config flags for KMS/customer-managed keys?
- **Backup / export functionality** — does it ship data out for backup, and to where by default?
- **Data retention defaults** — are there retention/TTL settings? What's the default?

#### Scan C — Auth, secrets, and config defaults

The "shipped insecure out of the box" category.

- **Default credentials** — search for `admin`/`admin`, `root`/`password`, hardcoded API keys in default configs, `.env.example` values that look real.
- **Disabled auth in default config** — `auth.enabled = false`, `--no-auth` flags, dev modes enabled by default.
- **Weak default ports / protocols** — HTTP (vs HTTPS) by default, plaintext database connections, no TLS verification.
- **Permissive CORS / CSRF defaults** — `Access-Control-Allow-Origin: *`, CSRF off.
- **Secret handling** — secrets in env vars (acceptable), secrets in config files committed to disk (warn), secrets logged (critical).
- **RBAC / authorization model** — is there one? Default role? Public-by-default endpoints?
- **Session / token defaults** — long-lived tokens, no rotation, JWTs with no expiry.
- **CSP / security headers** — if there's a web UI, what does it ship by default?

#### Scan D — Dependencies and supply chain

The transitive-trust surface.

- **Direct dependency count and roster** — list direct deps from each manifest. Flag any with names that look typosquatted, abandoned (last release > 2 years), or that are themselves the kind of "analytics SDK" Scan A would flag if used.
- **Install-time scripts** — `package.json` `scripts.postinstall`, `setup.py` custom commands, Cargo `build.rs`, Go `go:generate` — anything that runs arbitrary code at install/build time. Note where it phones home if it does.
- **Pinning posture** — are direct deps pinned, ranged, or floating? Floating direct deps in a deploy-time-resolved manifest is a supply-chain risk worth flagging.
- **License flags** — anything GPL/AGPL/SSPL when the user is embedding into a closed-source product; anything with no LICENSE file at all.
- **Known-vulnerable versions** — best-effort. If the user has `osv-scanner` or `npm audit` / `pip-audit` / `cargo audit` available, run it against the cloned source and surface output. Don't fabricate CVE IDs.
- **Vendored / bundled binaries** — pre-built binaries committed to the repo (note path and what they claim to be).

### Step 4 — Catalog the security and privacy knobs

Independent of findings, enumerate every configuration option the software exposes that affects security or data privacy. Sources to read:

- `.env.example`, `config/`, `defaults.yaml`, `settings.py`, `application.yml`, embedded default configs in code.
- CLI flag definitions (`flag.Bool`, `argparse`, `clap`, `cobra` definitions).
- Helm `values.yaml`, Docker Compose env blocks, k8s manifests.
- `docs/configuration.md`, `docs/security.md`, or equivalent.

Bucket each knob by category and note the default vs. the most-locked-down value:

- **Telemetry / analytics off-switches** — every flag found in Scan A that disables a channel, plus any not exercised by Scan A.
- **Auth enforcement** — required-auth flags, MFA settings, SSO-only flags, session timeouts, token TTLs.
- **Network / TLS** — TLS-required flags, cipher suites, HSTS, listener bind addresses (`127.0.0.1` vs `0.0.0.0`).
- **Data handling** — retention TTLs, log levels (avoid `debug` in prod), redaction flags, encryption-at-rest knobs.
- **Outbound destination overrides** — knobs that let you point telemetry/webhooks at a self-hosted relay instead of the vendor.
- **Update / plugin behavior** — auto-update off, plugin allow-listing, signature verification on plugins/extensions.
- **Multi-tenancy / RBAC** — default role, public-by-default endpoints, admin-API expose flags.

For each knob, record: name, file/source where defined, default, recommended-for-max-security value, and a one-line rationale. This catalog feeds the "Maximum-security baseline" section of the report.

If a knob the user would expect doesn't exist (e.g., no flag to disable telemetry, no flag to require TLS), record that absence — it's both a finding for Scan A/C and a gap in the baseline.

### Step 5 — Report

Print the report to the terminal in the format below. The report has three actionable sections in priority order:

1. **Headline** — the data-exfiltration verdict.
2. **Guided configuration recommendations** — finding-driven; closes the specific gaps surfaced in Scans A–D.
3. **Maximum-security baseline** — knob-driven; built from the Step 4 catalog. Independent of findings; turns every relevant lever to the most-locked-down setting. The user can apply this baseline wholesale and then back off individual knobs where their threat model allows.

Then ask once: "Save this report to a file?" If yes, default to `./audit-<repo>-<shortsha>.md` in the current working directory; offer `.agentic/audits/<repo>-<shortsha>.md` if the user is in a workspace that has `.agentic/`.

## Report format

```
Third-party audit: <repo>
Source: .agentic/sources/<repo>/  (commit <shortsha>)

Intent calibration
  Deployment:        <self-hosted on-prem | SaaS | air-gapped | ...>
  Data classes:      <PII, regulated, ...>
  Egress policy:     <allow-list | broad | none>
  Telemetry policy:  <forbidden | configurable-off | acceptable>
  Features in use:   <list>
  Auth model:        <SSO | local | ...>

============================================================
HEADLINE: Data-exfiltration verdict
============================================================
<one paragraph from Scan A's verdict — the answer to the core question>

Required outbound channels (cannot be disabled via config):
  - <destination>  <file:line>  <what data, when sent>
  - ...

Disable-able outbound channels (off-switch verified):
  - <destination>  <file:line>  <config to disable>
  - ...

============================================================
Findings
============================================================

[A] Outbound network / telemetry      <N findings>
  CRITICAL  <category>   <file:line>
    What: <one line>
    Data: <what gets sent>
    Trigger: <when>
    Configurable: yes — set <ENV_VAR>=... in config/values.yaml
    Recommend: <action>

  HIGH      <category>   <file:line>
    ...

[B] Data persistence & storage        <N findings>
  ...

[C] Auth, secrets, config defaults    <N findings>
  ...

[D] Dependencies & supply chain       <N findings>
  ...

============================================================
Guided configuration recommendations
============================================================
Apply these together when deploying. Each is keyed to a finding above.

  1. Set TELEMETRY_DISABLED=1                       (closes A-1, A-3)
  2. Override default admin password before first start (closes C-1)
  3. Set AUTH_REQUIRED=true in config/server.yaml   (closes C-2)
  4. Pin dependency `foo` to ==1.2.3 in requirements.txt (closes D-4)
  5. Run behind TLS-terminating proxy; the default HTTP listener is plaintext (closes C-3)
  ...

============================================================
Maximum-security baseline (apply wholesale, then relax as needed)
============================================================
This is every security/privacy knob this software exposes, set to the most-locked-down value. Apply all of them, then back off individual knobs only where your threat model explicitly allows.

Telemetry / analytics
  TELEMETRY_DISABLED=1                              (default: off — telemetry on)
  CRASH_REPORTING_ENABLED=false                     (default: true)
  UPDATE_CHECK_INTERVAL=0                           (default: 24h ping to vendor.example.com)

Auth and session
  AUTH_REQUIRED=true                                (default: false in dev mode — verify dev mode is off)
  SESSION_TTL=15m                                   (default: 30d)
  REQUIRE_MFA=true                                  (default: false; supported since v2.3)
  ADMIN_API_BIND=127.0.0.1                          (default: 0.0.0.0 — admin API on public iface)

Network / TLS
  TLS_REQUIRED=true                                 (default: false; HTTP listener on by default)
  TLS_MIN_VERSION=1.3                               (default: 1.2)
  HSTS_ENABLED=true                                 (default: false)

Data handling
  LOG_LEVEL=info                                    (default: debug — leaks request bodies)
  AUDIT_LOG_REDACT_PII=true                         (default: false)
  RETENTION_DAYS=30                                 (default: unlimited)
  ENCRYPT_AT_REST=true + KMS_KEY_ID=<your-key>      (default: rely on storage layer)

Outbound destination overrides (use these if egress is allowed but vendor-bound is not)
  TELEMETRY_ENDPOINT=https://relay.internal/        (default: vendor.example.com — relay if you must collect)
  WEBHOOK_ALLOWLIST=slack.internal.example.com      (default: empty = any host)

Updates and plugins
  AUTO_UPDATE=false                                 (default: true)
  PLUGIN_SIGNATURE_REQUIRED=true                    (default: false)
  PLUGIN_ALLOWLIST=<explicit list>                  (default: any)

Gaps (knobs the user would expect that this software does NOT expose):
  - No flag to disable the model-API call in src/agent.py:88 — see finding A-3. Mitigate at network layer.
  - No way to require auth for /healthz endpoint — see finding C-4. Mitigate at proxy.

Suggested follow-ups (out of scope for this static pass):
  - Run the service in a sandboxed VM with egress logging to confirm Scan A coverage.
  - Pen-test the auth boundary if exposing the UI publicly.
  - Subscribe to <repo>'s security advisories.

Summary: <X CRITICAL> <Y HIGH> <Z MEDIUM> <W LOW>
```

When the audit is clean (no findings above INFO), collapse:

```
Third-party audit: <repo>  (commit <shortsha>)

Headline: no outbound channels detected, defaults are reasonable.

  [A] Outbound        CLEAN
  [B] Persistence     CLEAN
  [C] Auth/config     CLEAN
  [D] Dependencies    CLEAN (<N> direct deps, all pinned)

Recommended config: none beyond upstream README. Suggest one runtime egress-capture pass to confirm.
```

## Calibrating severity

Use the Step 1 answers as the lens. A rough table:

| Finding                                       | Air-gapped intent | Egress-allowed intent |
|---|---|---|
| Hardcoded telemetry POST, no off switch       | CRITICAL          | MEDIUM                |
| Hardcoded telemetry POST, off switch exists   | HIGH              | LOW (recommend off)   |
| Optional integration to a SaaS the user won't enable | INFO       | INFO                  |
| Default admin password                        | CRITICAL          | CRITICAL              |
| HTTP-by-default with TLS opt-in               | HIGH              | HIGH (still bad)      |
| Floating direct dependency                    | MEDIUM            | MEDIUM                |
| Unmaintained dependency (>2y, low-traffic)    | HIGH              | MEDIUM                |
| Model-API call sending prompt content out     | CRITICAL          | HIGH (data class matters) |

When in doubt, err toward the higher severity and explain the calibration in one line under the finding. Users can downgrade; they can't act on findings they never saw.

## Guidelines

- **Cite, don't assert.** Every finding needs `file:line` against the cloned source. "The code phones home" without a citation is unactionable.
- **Be specific about configurability.** Don't say "telemetry can be disabled" — say "set `TELEMETRY_DISABLED=1` (see `config/defaults.yaml:42`)". If you can't find the off switch, say so explicitly; that itself is a finding.
- **Read what you cite.** When you cite `file:line` for a network call, read the surrounding context first. False positives on this skill are expensive — users will deploy or not based on the report.
- **Don't audit features the user said they won't use.** If they said "no Slack integration", note the Slack code exists and move on. Don't bury the headline.
- **The headline is the headline.** The data-exfiltration verdict is what the user came for. Lead with it; don't bury it under finding tables.
- **Heuristics, not guarantees.** Static analysis can miss obfuscated or dynamically-loaded channels. The report should always recommend a runtime egress-capture pass as a follow-up, especially for large codebases.
- **Don't fabricate.** No invented CVE IDs, no invented config keys. If a setting "should exist" but you can't find it in the source, say so.
- **Build the baseline from the source, not from memory.** Every knob in the maximum-security baseline must trace back to a config key, env var, or flag that exists in the cloned source. If you can't find a knob that the user would reasonably expect (e.g., "disable telemetry"), list it under the baseline's **Gaps** subsection rather than inventing one. The point of the baseline is to be applicable verbatim by the user — invented keys make it dangerous.
- **Distinguish the two recommendation sections.** Finding-driven recommendations are minimum fixes for problems found. The maximum-security baseline is the most-locked-down deployment posture the software supports, independent of findings. Both belong in the report; don't collapse them.
- **No emojis. No AI attribution in any written artifact.** Plain text.
- **Don't auto-route into other skills.** The user runs `/fetch-context` themselves before, and acts on the recommendations themselves after.
