---
name: draft-data-contract
description: >-
  Interview the user about a dataset or pipeline boundary and produce an Open
  Data Contract Standard (ODCS) YAML contract covering schema, semantics,
  quality, freshness SLA, and ownership — with an optional medallion `layer:
  bronze|silver|gold` field. Accepts existing sample data, a SQL/DDL schema,
  an inferred dataframe schema, or a blank slate as input. Auto-detects the
  host repo stack (dbt, pandera/pydantic, Great Expectations, Soda, Polars
  /Pandas/Spark) so the contract matches conventions already in use. Use
  when the user wants to make an implicit dataset contract explicit, define
  a new dataset at a pipeline boundary, or formalize an agreement between a
  producer and a downstream consumer. Triggers include "draft a data
  contract", "ODCS this dataset", "contract for <table>", "pin the schema
  for <dataset>", "make this dataset's contract explicit". Pairs upstream
  with `/audit-data-contracts` (finds gaps) and downstream with
  `/enforce-data-contract` (emits validators) and `/synth-from-contract`
  (emits realistic fakes). Produces a contract only — hand off to the
  downstream skills to act on it.
---

`/draft-data-contract` is an authoring skill. One conversation, one artifact: an ODCS YAML contract for a dataset or pipeline boundary the user names. The contract conforms to the profile in the `data-contract-core` skill, which `/enforce-data-contract` and `/synth-from-contract` both consume verbatim.

The skill does not generate validation code (that is `/enforce-data-contract`). It does not generate fake data (that is `/synth-from-contract`). It does not scan the repo for unwritten contracts (that is `/audit-data-contracts`). It produces one well-formed contract for one boundary.

## When to use

- The user has a dataset whose schema is "known" but unwritten — a Parquet table, a Kafka topic, a dbt model, a Polars dataframe at a pipeline edge — and wants to make the agreement between producer and consumer explicit.
- The user is defining a new dataset and wants the contract before the implementation, so downstream consumers can code against it.
- The user is formalizing a medallion boundary (bronze → silver, or silver → gold) and needs a contract that matches the layer's strictness expectations.
- `/audit-data-contracts` found a gap and recommended drafting a contract for a specific dataset.

## When not to use

- The user wants validation code, not a contract — go to `/enforce-data-contract`. (It will ask for the contract path; this skill produces that path.)
- The user wants synthetic / fake data for tests — go to `/synth-from-contract`.
- The user wants a survey of all unwritten contracts in the repo — go to `/audit-data-contracts`.
- The user wants to draft *many* contracts in one session — run this skill multiple times, once per boundary. A single contract per conversation keeps the interview tight.
- The dataset has no stable shape yet (e.g., a Kafka topic with arbitrary JSON payloads) — flag it; pinning a contract on shifting data does more harm than no contract.

## Inputs the skill accepts

Ask the user which form the dataset description is in. Support any of:

1. **Sample data file** — local path to a Parquet, CSV, JSONL, or Arrow file. Use the file headers / column types as the starting schema, but treat them as a draft only; do not auto-emit nullability or enums without confirming with the user.
2. **DDL / SQL schema** — `CREATE TABLE` text, a `schema.yml` from dbt, or an information-schema dump. Parse out columns and types; ask about everything else.
3. **Inferred dataframe schema** — output of `df.schema` (Polars), `df.dtypes` (Pandas), `df.printSchema()` (Spark). Same caveat as sample files: types only, semantics by interview.
4. **Existing ODCS contract to extend or revise** — local path. Load it, show the user what's there, and interview the deltas.
5. **Blank slate** — no inputs. Conduct the full interview from scratch.

If the user has more than one source (a sample file *and* a DDL), use both — they cross-check each other.

### Input triage

Before interviewing, surface what the input source tells you:

- Column names and types in the input.
- Anything that looks like an ID, a foreign key, a timestamp, an enum (low-cardinality string columns in sample data), or a monetary value (column names containing `amount`, `price`, `cents`, `minor_units`).
- Anything that looks like PII (column names matching `email`, `phone`, `ssn`, `dob`, `address`).
- Obvious gaps the contract must fill — e.g., the input lists `status` but doesn't say which values are legal.

Use this triage to make interview questions concrete: "the sample has a `status` column with values `pending`, `settled`, `refunded` — is `disputed` also legal?" beats "are there any enums?".

### Host repo detection

Before interviewing, also detect what the host repo already uses, because the contract should fit local conventions:

- **dbt project** — `dbt_project.yml` exists. The contract will likely live next to a model and be enforced via dbt model contracts. Note the `models/` layout.
- **Python data stack** — `pyproject.toml` lists any of `pandera`, `pydantic`, `great_expectations`, `soda-core`, `polars`, `pandas`, `pyspark`. Note which.
- **Spark / Databricks** — `pyspark`, `delta-spark`, or `databricks-sdk` in deps; `spark-defaults.conf` or `databricks.yml`.
- **Medallion architecture in use** — directory names like `bronze/`, `silver/`, `gold/`; dbt model prefixes like `stg_`, `int_`, `fct_`, `dim_`; or explicit references in README. If detected, default the contract's `info.layer` field to a best guess and confirm in the interview.
- **Existing contracts in the repo** — `grep -l "open-data-contract\|datacontract.com" .` or files named `*.contract.yaml`, `*.odcs.yaml`, `contracts/`. If others exist, mirror their conventions (file location, naming, version-bumping pattern).

Cite what you found back to the user in one short paragraph before the interview. This avoids dumb questions and signals you've read the project.

## The interview

Conversational, not a flat script. Build on answers; push back when an answer is vague. Cover the following dimensions in roughly this order, but follow the user's lead.

### Identity and ownership

- **Title** — what is this dataset called? Convention: `<layer>.<name>` if medallion (e.g., `silver.transactions`). Otherwise a stable, lowercase, dotted or snake_case name.
- **Owner** — which team or person is accountable for the contract? Free-form (Slack handle, team name, GitHub team). The contract is an agreement; an agreement needs a counterparty.
- **Consumers** — who reads this dataset? List by name if known. The consumer list disciplines what counts as a breaking change.
- **Version** — starting version. Default `0.1.0` if this is a new dataset; `1.0.0` if it's already being consumed. Ask only if the user has a strong opinion.

### Layer (medallion, optional)

- **Layer** — bronze (raw, append-only), silver (conformed, deduped), gold (business-ready, served). Skip if the user doesn't use medallion. If set, the layer drives default strictness for the quality block (see the `data-contract-core` skill).
- If silver or gold: confirm the user understands the implied defaults (silver expects uniqueness; gold requires FK + freshness SLA). Don't quietly emit a gold contract that lacks the required quality fields — surface the gap.

### Schema (fields)

For each field, settle: `name`, `type`, `required` (nullability), `semantics` tag (optional), and a one-line description (optional but encouraged).

- Use input triage to seed the field list; confirm rather than discover.
- Types: `string`, `integer`, `number`, `boolean`, `timestamp`, `date`, `object`, `array`. If the input uses a type the profile doesn't list (e.g., `decimal(18,2)`, `geography`), ask how the user wants to model it — usually as `string` with a `semantics` tag, or as `number` with a `ranges` quality assertion.
- Required: ask per field. "Required" means non-null in the contract; default to required for IDs and timestamps, ask about everything else.
- Semantics: short free-form string. Examples: `uuid_v4`, `iso_country_alpha2`, `iso_currency_alpha3`, `e164_phone`, `email`, `currency_usd_minor_units`, `epoch_ms`. The semantics tag drives `/synth-from-contract` realism and `/audit-data-contracts` finding messages. Push the user to set semantics on every ID, timestamp, money, and code-table column.
- PII tag: ask once per field for any column that looks like PII (or set `info.pii: true` for the whole dataset and skip per-field unless one column is non-PII).

### Semantics and value domains

- **Enums** — for any low-cardinality string column, surface the candidate values from sample data (if available) and ask the user to confirm the full set. An enum is a contract; missing values from the enum are bugs to find.
- **Ranges** — for any numeric column, ask about `min`/`max`. Common: `amount >= 0`, `pct between 0 and 100`. Skip if the user genuinely doesn't know.
- **Formats** — for strings with a defined format (regex, ISO 8601 date, UUID), capture as a `semantics` tag and, where the format is regex-like, also as a `quality.ranges` entry with `format`.

### Quality and constraints

- **Uniqueness** — ask which fields uniquely identify a row, and which combinations (e.g., `(user_id, occurred_at)`). At silver+, expect at least one. At gold, require one.
- **Foreign-key references** — ask which fields reference another dataset's contract. Capture as `quality.references` with `contract` and `contract_field`. If the referenced contract doesn't exist yet, note it as an open question rather than fabricating the reference.
- **Freshness SLA** — what is the maximum acceptable lag between source-event time and dataset availability? Capture as `quality.freshness_sla.max_lag` (Go-style duration: `30m`, `1h`, `24h`) and `measured_as` (free-form: `max(ingested_at) vs now()`).
- **Row count expectations** — daily floor, ceiling, max acceptable day-over-day change. Skip if the user doesn't know; row-count checks are easy to add later.
- **Distribution checks** — flag as optional and skip by default; they are flaky and rarely worth defaulting on. Mention they exist.

### Physical materialization

- **Server / location** — where does this dataset physically live? `snowflake://...`, `s3://bucket/prefix`, `bigquery://project.dataset.table`, `kafka://cluster/topic`. Captured as a `servers` entry. If multiple, list them; the downstream skills will ask which to target.
- **File format** — if object storage: Parquet, Delta, Iceberg, CSV, JSONL. Affects how `/enforce-data-contract` wires up validators.

### Versioning and breaking-change policy

- **Breaking-change policy** — additive-only (every new version bump must be additive: new optional fields, new enum values), or open (anything goes with a major version bump). Default: additive-only on silver/gold.
- **Deprecation window** — how long does a removed field stay around as deprecated before it can be dropped? Free-form (e.g., "two quarters").

Capture as `info.x-breaking-change-policy` (ODCS allows `x-` extensions).

## Output: render then write

When the contract is ready, **render it in the conversation first**. Don't write to disk yet. The user reviews; iteration is expected.

Then ask where to save. Suggestions, in order:

1. If `.agentic/<slug>/` exists for the current branch, suggest `.agentic/<slug>/<title>.odcs.yaml`.
2. If the repo has an existing `contracts/` directory or other contracts at a stable path, suggest matching that path.
3. If the host is a dbt project, suggest `models/<layer>/<dataset>.odcs.yaml` next to the model.
4. Else suggest `<repo-root>/contracts/<title>.odcs.yaml`.
5. Accept any user-supplied path.

Only write after the user confirms a path. If they want to iterate on the contract in chat first, do that — the file write is the last step, not the first.

After writing, suggest the obvious next steps:

- `/enforce-data-contract <path>` — emit validators for the chosen stack.
- `/synth-from-contract <path>` — generate realistic fakes for tests / dev.

Do not auto-invoke either. The user decides.

## Contract template

The skill emits ODCS YAML conforming to the profile in the `data-contract-core` skill. Use the worked `silver.transactions` example there as the canonical reference shape. The template below names every field the skill should populate during the interview; omit optional fields the interview didn't surface rather than emitting empty placeholders.

```yaml
# <title> ODCS contract
info:
  title: <title>                           # required
  version: <semver>                        # required
  owner: <team or handle>                  # required
  layer: <bronze|silver|gold>              # optional, medallion
  pii: <true|false>                        # optional, dataset-level PII flag
  description: >-                          # optional but encouraged
    <one or two sentences>
  x-breaking-change-policy: <additive-only|open>   # optional
  x-consumers: [<list>]                    # optional; informs breaking-change reviews

schema:
  fields:
    - name: <field>
      type: <string|integer|number|boolean|timestamp|date|object|array>
      required: <true|false>
      semantics: <free-form short tag>     # optional
      pii: <true|false>                    # optional, per-field PII flag
      description: <one line>              # optional
    # ... one entry per field

quality:                                   # optional block
  uniqueness:
    - fields: [<field>, ...]
  ranges:
    - field: <field>
      min: <value>
      max: <value>
  enums:
    - field: <field>
      values: [<v1>, <v2>, ...]
  references:
    - field: <field>
      contract: <other.title>
      contract_field: <other-field>
  freshness_sla:
    max_lag: <duration>
    measured_as: <free-form expression>
  row_count:
    min: <int>
    max_daily_change_pct: <int>

servers:                                   # optional, but recommended
  - type: <warehouse|object_store|stream|database>
    location: <URI>
```

After the contract block, append an `## Open questions` section in the conversation (not in the YAML) listing anything the interview did not resolve. The user should answer these before handing the contract to `/enforce-data-contract` or `/synth-from-contract`.

## Composition with other skills

- **Upstream**: `/audit-data-contracts` finds datasets without contracts and routes each one to a `/draft-data-contract` invocation.
- **Downstream**: `/enforce-data-contract <path>` reads the contract and emits validators (dbt, Great Expectations, Soda, Pandera, or Pydantic).
- **Downstream**: `/synth-from-contract <path>` reads the contract and emits realistic fake data (Parquet, CSV, JSONL, DuckDB, or a Faker factory class).
- **Reference**: the `data-contract-core` skill documents the ODCS profile shared across all four skills. Link to it in the rendered contract's preamble comment.

## Guidelines

- **Interview before drafting.** Even with a sample file or DDL, do not silently autofill nullability, enums, ranges, or FK references. Type is the only thing the input can authoritatively give you; everything else is an agreement, not an observation.
- **Push back on missing semantics on IDs, timestamps, money, and codes.** A contract with bare `string` columns and no semantics is barely better than no contract. Names lie; semantics don't.
- **Match the layer's strictness.** If the user labels a contract `gold`, the freshness SLA and at least one FK or uniqueness assertion must be present before write — surface the gap rather than emitting an under-spec gold contract. See the `data-contract-core` skill for the layer-strictness defaults.
- **Don't invent FKs.** If the user names a foreign key but the referenced contract doesn't exist yet, capture the FK as an open question, not as a `quality.references` entry. Phantom FKs that point at non-existent contracts break `/enforce-data-contract`.
- **One contract per conversation.** If the user wants three contracts, run the skill three times. The interview is too detailed to multiplex.
- **Use ODCS, not a homegrown shape.** This skill family commits to ODCS by design; see the `data-contract-core` skill for the rationale. Don't drift into a custom YAML even if the user proposes one — propose ODCS plus the `x-` extension surface instead.
- **Plain text only. No emojis.** Match the rest of the skills.
