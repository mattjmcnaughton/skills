---
name: data-contract-core
description: >-
  Reference doc for the data-contract skill family. Defines the Open Data
  Contract Standard (ODCS) profile that `/draft-data-contract`,
  `/enforce-data-contract`, `/synth-from-contract`, and
  `/audit-data-contracts` all assume: required fields, the optional
  medallion `info.layer: bronze|silver|gold` field with strictness
  defaults, the `quality` block shape (uniqueness, ranges, enums,
  foreign-key references, freshness SLA, row count, distribution), and a
  worked `silver.transactions` example contract used as the canonical
  reference shape across the family. Not an action skill — there is
  nothing to "run". Read this when authoring or modifying a data-contract
  skill, when answering questions about the ODCS profile, or when a
  contract that round-trips through one of the four skills fails and the
  cause might be a profile mismatch. Pairs with the four data-contract
  skills as their shared format spec.
---

# Data contract format (core reference)

The four data-contract skills (`/audit-data-contracts`, `/draft-data-contract`, `/enforce-data-contract`, `/synth-from-contract`) share one contract format: **Open Data Contract Standard (ODCS)**, see `https://datacontract.com`. ODCS is a YAML-based, vendor-neutral spec maintained under the Bitol project. It covers schema, semantics, quality, SLAs, and ownership in one document — which is exactly the surface our skills need to author, validate against, generate from, and audit toward.

This skill pins the **profile** the others use: a minimum subset of ODCS that every skill assumes, plus a small set of conventional extensions (most notably the optional `info.layer` field for medallion architectures). A contract that passes this profile will round-trip cleanly through all four skills. A contract that uses ODCS fields outside this profile is still valid ODCS; the skills will warn rather than reject.

This is a **reference skill**, not an action skill. There is nothing to run. The four downstream skills consume the profile defined here; when a question about contract shape comes up — what counts as required, what the `layer` field means, what the `quality` block looks like — answer from here.

## Why ODCS

The data-contract space has three real options (ODCS, the dbt-flavored model-contract YAML, and various in-house JSON Schema variants). ODCS wins for this skill family because:

1. It is the only option whose surface covers schema *and* quality *and* SLA *and* ownership in one artifact. The skills need all four.
2. It is YAML-native, which keeps it human-editable in PRs alongside dbt models and pipeline code.
3. It is independent of any single execution engine, which keeps `/enforce-data-contract` honest about emitting validators for dbt, Great Expectations, Soda, Pandera, and Pydantic from the same source.

## Required fields

A contract that satisfies the profile MUST set:

- `info.title` — human-readable name, typically `<layer>.<dataset>` (e.g., `silver.transactions`).
- `info.version` — semver string. Bumped on every breaking change.
- `info.owner` — team or person accountable. Free-form string; a Slack handle or team name is fine.
- `schema.fields[].name` — column name.
- `schema.fields[].type` — one of `string`, `integer`, `number`, `boolean`, `timestamp`, `date`, `object`, `array`. Mirrors JSON Schema primitives.
- `schema.fields[].required` — `true` or `false`. The skill enforces this as the canonical non-nullability signal; if ODCS `nullable` is present, treat `required: true` as `nullable: false`.

Everything else is optional. The skills degrade gracefully when optional fields are absent (e.g., `/enforce-data-contract` emits a schema-only validator if there is no `quality` block).

## Optional profile extensions

### `info.layer` (medallion architecture)

If the host uses medallion architecture, set `info.layer: bronze | silver | gold`. The four skills apply layer-strictness defaults:

- **bronze** — raw, append-only. Defaults: no FK assertions, no uniqueness, no freshness SLA required. `/enforce-data-contract` emits schema-only validation. `/audit-data-contracts` flags missing owner only.
- **silver** — conformed, deduplicated. Defaults: at least one uniqueness assertion expected; FK references allowed; freshness SLA recommended. `/enforce-data-contract` emits schema + uniqueness checks; warns if no `quality.uniqueness` is present.
- **gold** — business-ready, served to downstream consumers. Defaults: at least one uniqueness assertion and at least one FK or referential-integrity assertion required; `quality.freshness_sla` required. `/enforce-data-contract` refuses to emit and surfaces the missing fields as errors rather than warnings.

`info.layer` is optional. Contracts without it behave like silver for default purposes but skip the layer-strictness errors.

### `info.pii` and `schema.fields[].pii`

`true` / `false` flags. Drive PII-aware redaction in `/enforce-data-contract` outputs and PII-aware fake values in `/synth-from-contract`.

### `schema.fields[].semantics`

Free-form short string: `currency_usd_minor_units`, `iso_country_alpha2`, `email`, `e164_phone`, etc. Drives realistic value choice in `/synth-from-contract` and informs `/audit-data-contracts` finding messages.

## Quality block shape

The `quality` block is optional but is what makes a contract enforceable beyond schema.

```yaml
quality:
  uniqueness:
    - fields: [id]
    - fields: [user_id, occurred_at]
  ranges:
    - field: amount_minor_units
      min: 0
      max: 1000000000
  enums:
    - field: status
      values: [pending, settled, refunded, disputed]
  references:
    - field: user_id
      contract: silver.users
      contract_field: id
  freshness_sla:
    max_lag: 1h
    measured_as: max(occurred_at) vs now()
  row_count:
    min: 1
    max_daily_change_pct: 50
  distribution:
    - field: status
      expected_proportions:
        settled: 0.85
        pending: 0.10
        refunded: 0.04
        disputed: 0.01
      tolerance_pct: 5
```

Notes on shape:

- `uniqueness.fields` is a list-of-lists so multi-column uniqueness constraints are first-class.
- `references` is the FK shape. Both `contract` and `contract_field` are required; `/enforce-data-contract` looks up the referenced contract to validate types match.
- `freshness_sla.max_lag` accepts Go-style duration strings (`30m`, `1h`, `24h`) for portability.
- `distribution` is informational at bronze/silver; `/enforce-data-contract` only emits distribution checks if the user asks for them explicitly, because they are flaky by nature.

## Worked example: `silver.transactions`

This contract is cited verbatim by each of the four data-contract skills. Treat it as the canonical reference shape.

```yaml
# silver.transactions ODCS contract
info:
  title: silver.transactions
  version: 1.2.0
  owner: data-platform
  layer: silver
  pii: false
  description: >-
    Conformed, deduplicated payment transaction events. Source of truth for
    downstream gold marts.

schema:
  fields:
    - name: id
      type: string
      required: true
      semantics: uuid_v4
      description: Stable transaction identifier.
    - name: user_id
      type: string
      required: true
      semantics: uuid_v4
    - name: amount_minor_units
      type: integer
      required: true
      semantics: currency_usd_minor_units
      description: Amount in USD cents. Always non-negative.
    - name: currency
      type: string
      required: true
      semantics: iso_currency_alpha3
    - name: status
      type: string
      required: true
    - name: occurred_at
      type: timestamp
      required: true
      description: Event time in UTC. Source clock, not ingestion clock.
    - name: ingested_at
      type: timestamp
      required: true
    - name: metadata
      type: object
      required: false

quality:
  uniqueness:
    - fields: [id]
  ranges:
    - field: amount_minor_units
      min: 0
      max: 1000000000
  enums:
    - field: status
      values: [pending, settled, refunded, disputed]
    - field: currency
      values: [USD, EUR, GBP, JPY]
  references:
    - field: user_id
      contract: silver.users
      contract_field: id
  freshness_sla:
    max_lag: 1h
    measured_as: max(ingested_at) vs now()
  row_count:
    min: 1
    max_daily_change_pct: 50

servers:
  - type: warehouse
    location: snowflake://prod/ANALYTICS/SILVER/TRANSACTIONS
```

The example deliberately uses every field shape the skills care about: required + optional, primitive + object types, semantics tags, enum + range + uniqueness + FK + freshness in the quality block, and a `servers` entry pointing at the physical materialization.

## Round-trip guarantees

- `/draft-data-contract` writes contracts that conform to this profile.
- `/audit-data-contracts` reports against this profile (e.g., "field `status` has no enum but is used as a categorical downstream").
- `/enforce-data-contract` accepts any contract that meets the required-fields bar; warns when optional-but-recommended fields are absent for the contract's layer.
- `/synth-from-contract` accepts any contract that meets the required-fields bar; falls back to type-only generation when semantics/enums/ranges are absent.

A contract is "round-trip clean" when all four skills run on it without warnings. Gold contracts must be round-trip clean before serving; silver contracts should be; bronze contracts often aren't, by design.

## What this profile deliberately excludes

- **ODCS `team` and `support` blocks** — useful for handoff to a steward, but the skills don't consume them. Authors may include them; the skills pass them through untouched.
- **ODCS `tags`** — kept as free-form pass-through metadata; no skill behavior keys off them.
- **Multiple servers per contract** — the profile supports it (ODCS does), but `/enforce-data-contract` and `/synth-from-contract` operate on one materialization at a time. If a contract has multiple `servers`, the skills will ask the user which to target.
- **ODCS `slo` extensions for availability/latency** — these are service-level, not data-level; out of scope for this skill family.

## References

- Open Data Contract Standard (ODCS): `https://datacontract.com`
- dbt model contracts: `https://docs.getdbt.com/docs/collaborate/govern/model-contracts`
- Great Expectations: `https://greatexpectations.io`
- Soda Core: `https://www.soda.io/soda-core`
- Pandera: `https://pandera.readthedocs.io`
- Pydantic: `https://docs.pydantic.dev`
