# Browser access via agent-browser

We use [agent-browser](https://github.com/vercel-labs/agent-browser) for controlled browser automation from Claude Code. This doc covers the local security posture and the encryption-key story. Full CLI reference lives upstream.

## Why agent-browser

Single Rust binary, no Playwright/Puppeteer at runtime. Built-in security primitives we'd otherwise have to assemble by hand: domain allowlist, action-policy gating, content-boundary markers for prompt-injection defense, output-length limits, encrypted auth vault.

## Install

```bash
npm i -g agent-browser  # or brew install agent-browser
agent-browser install --with-deps   # one-time: Chrome for Testing + Linux system libs
agent-browser doctor                # verify install + active security posture
```

`--with-deps` installs the apt packages Chromium needs (libnss, libatk, libxkbcommon, etc.) alongside the browser. Drop it on macOS or if the system libs are already present.

Node is only used for delivery; the daemon itself is pure Rust.

## Sandbox on Ubuntu 23.10+ VMs

Ubuntu 23.10+ restricts unprivileged user namespaces via AppArmor, which breaks Chrome's sandbox initialization. Symptom on first `agent-browser open`:

> No usable sandbox! ... see `kernel.apparmor_restrict_unprivileged_userns`

Most often hit on fresh Ubuntu VMs and cloud images. Desktop installs running Snap Chromium typically don't see it — Snap ships an AppArmor profile that grants the capability, but the bare Chrome-for-Testing binary `agent-browser install` downloads has no such profile. Not needed on macOS.

Re-enable userns so Chrome's own sandbox can initialize. Preferred over `--no-sandbox`, which disables the renderer boundary entirely:

```bash
echo 'kernel.apparmor_restrict_unprivileged_userns = 0' | sudo tee /etc/sysctl.d/60-chrome-userns.conf
sudo sysctl --system
```

Tradeoff: this weakens AppArmor's policy for *all* unprivileged binaries, not just Chrome. A narrower alternative is a per-binary AppArmor profile scoped to `~/.agent-browser/browsers/chrome-*/chrome`, but it has to be redone whenever agent-browser pulls a new Chrome.

## Security config

Locked-down defaults at `~/.agent-browser/config.json`. The CLI reads this on every invocation; flags and env vars override.

```json
{
  "$schema": "https://agent-browser.dev/schema.json",
  "contentBoundaries": true,
  "maxOutput": 50000,
  "allowedDomains": ["localhost", "127.0.0.1", "[::1]"],
  "confirmActions": "eval,download,upload,network,state",
  "confirmInteractive": true,
  "ignoreHttpsErrors": false,
  "allowFileAccess": false,
  "noAutoDialog": true
}
```

### What each setting does

- **`allowedDomains`** — only localhost. Blocks top-level navigation, sub-resource fetches, WebSockets, and EventSources to anything else. Matches hostnames exactly (no port consideration) and does not special-case localhost — `localhost`, `127.0.0.1`, and `::1` are listed separately because they are distinct hostnames to the matcher.
- **`confirmActions` + `confirmInteractive: true`** — `eval, download, upload, network, state` require approval. With `confirmInteractive: true`, the upstream docs guarantee actions auto-deny when stdin is not a TTY. In agent context (no TTY) that means a hard fail; in an interactive terminal you get a `[y/N]` prompt. This closes a subtle loophole where the agent could self-approve by calling `agent-browser confirm <id>` in a follow-up bash call.
- **`contentBoundaries`** — wraps page-sourced output in nonce'd structural markers so an orchestrator can distinguish trusted tool output from untrusted page content. Defense-in-depth against prompt injection.
- **`maxOutput`** — 50k char cap on page-sourced output (`snapshot`, `get text/html`, `eval`, `console`). Prevents context flooding.
- **`noAutoDialog`** — alert/beforeunload dialogs are not silently dismissed. The agent must call `dialog accept/dismiss` explicitly.
- **`ignoreHttpsErrors`, `allowFileAccess`** — explicitly false. Self-signed certs and `file://` URLs require ad-hoc flag overrides.

### Gating rationale

Mental model: gate anything that **escapes the page sandbox** (filesystem, persistent state, network mocking) or **breaks the sandbox** (`eval`, which injects arbitrary JS and — per upstream security docs — can bypass the WebSocket/EventSource domain filter). Let normal page interaction (`navigate`, `click`, `fill`, `scroll`, `snapshot`, `get`, `wait`, `interact`) through, since the domain allowlist already constrains *where*.

| Category | Covers | Why gated |
|---|---|---|
| `eval` | `eval`, `addinitscript`, `setcontent`, ... | Arbitrary JS; can restore WebSocket/EventSource constructors and bypass the domain filter |
| `download` | `download`, `waitfordownload` | Writes fetched bytes to disk |
| `upload` | `upload` | Sends local files to the page (exfiltration vector) |
| `network` | `network route`, `har start/stop` | Traffic tampering; HAR files leak request headers, cookies, response bodies |
| `state` | `cookies set`, `storage set`, `state load` | Auth-takeover vector via cookie/storage writes |

Note: `network` lumps the read-only `network requests` in with `network route`. If a debugging session keeps tripping confirmations just from listing requests, that's why.

### Loosening per-invocation

Allowing extra domains for a single command (the flag *replaces* the config list, so always re-list localhost):

```bash
agent-browser --allowed-domains "localhost,127.0.0.1,docs.python.org" open https://docs.python.org
```

For a project that consistently needs broader scope, drop an `agent-browser.json` in the working directory. Project configs replace, not merge — list everything the project needs including localhost.

## Encryption key

`AGENT_BROWSER_ENCRYPTION_KEY` encrypts two opt-in features:

- **Auth vault** (`~/.agent-browser/auth/`) — `agent-browser auth save <name> --username ... --password-stdin` writes credentials encrypted at rest. `auth login <name>` navigates and fills the form without the LLM ever seeing the password.
- **Session state** (`~/.agent-browser/sessions/`) — when using `--session-name <name>`, cookies and localStorage persist encrypted across runs.

If you never use either feature, the key is never read.

### Skip-for-now is fine

If `AGENT_BROWSER_ENCRYPTION_KEY` is unset, the CLI auto-generates `~/.agent-browser/.encryption-key` (chmod 600) on first use. Real encryption; you just don't pick the key. Tradeoff: lose that file (accidental delete, `~/.agent-browser/` wipe) and the vault is permanently unreadable.

### Setting it explicitly

Do this **before** your first `agent-browser auth save`. If you save credentials first and add the env var later, the existing vault becomes unreadable from key mismatch — you have to delete and re-enter everything.

Generate:

```bash
openssl rand -hex 32
```

64 hex chars = 32 bytes for AES-256-GCM. Stash the output in a password manager *before closing the terminal*, then add to `~/.bashrc`:

```bash
export AGENT_BROWSER_ENCRYPTION_KEY=<paste-here>
```

Benefits over the auto-generated key:
- Backup-able from the password manager.
- Portable across machines (sync `~/.agent-browser/auth/` between hosts using the same key).
- Survives wipes of `~/.agent-browser/`.

## References

- [agent-browser README](https://github.com/vercel-labs/agent-browser) — full CLI reference
- [Security docs](https://agent-browser.dev/security) — threat model and primitive details
- Config schema: `https://agent-browser.dev/schema.json`
