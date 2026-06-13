---
name: enforce-data-contract
description: >-
  Take an Open Data Contract Standard (ODCS) YAML contract and generate
  validation code in the host repo's stack: dbt model contracts plus
  dbt-expectations / dbt-utils tests, Great Expectations expectation
  suites, Soda Core checks, Pandera DataFrameSchema, or Pydantic
  BaseModel. Auto-detects which validators the repo already uses;
  interviews the user about which to emit, where they land, and how they
  wire into the existing test/CI surface. Honors layer-strictness defaults
  (gold contracts emit freshness checks automatically; bronze emits
  schema only). Surfaces ODCS fields the target tool can't express as
  warnings rather than silently dropping them. Use when the user has a
  contract (typically from `/draft-data-contract`) and wants to wire its
  guarantees into the pipeline. Triggers include "enforce this contract",
  "generate dbt tests from this contract", "wire validation for
  <dataset>", "emit Pandera from this contract", "Soda checks for this
  contract". Produces validators only — does not modify the contract.
---

`/enforce-data-contract` is a generator. One conversation, one or more validator artifacts: code or config files that enforce the guarantees of an ODCS contract at the boundary the user picks (dbt model contract + tests, Great Expectations suite, Soda checks, Pandera schema, Pydantic model). The contract is the source of truth; the validators are derived.

The skill does not modify the contract. If the user wants the contract changed, route them back to `/draft-data-contract`. The skill does not generate sample data (that is `/synth-from-contract`).

## When to use

- The user has an ODCS contract (typically produced by `/draft-data-contract`) and wants validators wired into the pipeline.
- The user is adopting a new validation tool (Pandera, Soda, GE) and wants to bootstrap from existing contracts.
- The user added a new dataset to a dbt project and wants the model-contract YAML + tests emitted from the ODCS source.
- The user changed a contract (new field, new enum value, new uniqueness constraint) and wants the validators regenerated.

## When not to use

- The user wants to write or revise the contract itself — go to `/draft-data-contract`. The contract is input, not output.
- The user wants synthetic data for tests — go to `/synth-from-contract`. Validators and fakes are siblings; this skill emits one, that one emits the other.
- The user wants to audit a repo for missing contracts — go to `/audit-data-contracts`.
- The user wants runtime data quality monitoring as a service (a Monte-Carlo-style platform) — out of scope; this skill emits validators that run inside the host project's existing test / CI / scheduler surface.

## Input

The skill takes one positional input: the ODCS contract path.

If the path is not given, ask. Suggested defaults: `.agentic/<slug>/<title>.odcs.yaml`, `contracts/<title>.odcs.yaml`, `models/<layer>/<dataset>.odcs.yaml` (dbt projects). If the user has multiple contracts and wants validators for several, ask them to run the skill once per contract.

Before interviewing, load the contract and verify it satisfies the required-fields bar from the `data-contract-core` skill (`info.title`, `info.version`, `info.owner`, and at least one `schema.fields[]` entry with `name`, `type`, `required`). If required fields are missing, stop and tell the user; do not attempt to emit validators against a malformed contract.

If `info.layer: gold` is set, also verify gold's strictness requirements: at least one `quality.uniqueness` or `quality.references` entry, and `quality.freshness_sla` present. Missing either is an error, not a warning — route the user back to `/draft-data-contract` to fix.

## Host stack detection

Before the interview, scan the repo for existing validators so the questions stay concrete:

- **dbt** — `dbt_project.yml` exists. Note the `models/` layout. Note whether `dbt-expectations` and `dbt-utils` are in `packages.yml`; if both, default to dbt model contracts + `dbt-expectations` for ranges/enums + `dbt-utils` for uniqueness/FK.
- **Great Expectations** — `great_expectations/` directory or `gx/` exists; or `great-expectations` is in `pyproject.toml` / `requirements.txt`. Note the existing expectation-suite layout.
- **Soda Core** — `soda-core` (or `soda-core-*`) in deps; `soda/` or `checks/` directory with `*.yaml` files.
- **Pandera** — `pandera` in `pyproject.toml`. Note whether the project uses class-based `pa.DataFrameModel` or functional `pa.DataFrameSchema`. Mirror what's there.
- **Pydantic** — `pydantic` in `pyproject.toml`. Note the Pydantic version (v1 vs v2 API surface differs).
- **None of the above** — the contract is being used in a project that has no validator yet. Default suggestion: Pandera for in-Python pipelines, dbt contracts for dbt projects, Soda for warehouse-centric pipelines without a dbt layer.

Cite the detection back to the user in one short paragraph before the interview.

## The interview

Cover, in order:

### Enforcement boundaries (write and read)

Before asking which validators to emit, establish *where* the contract is enforced. The default, per the `data-contract-core` profile, is to enforce on both sides of every boundary the contract crosses: the producer validates **on write**, the next consumer validates **on read**.

Ask the user:

- Which job(s) **write** data conforming to this contract? (e.g., the extract job for a bronze contract; the bronze→silver transform for a silver contract.) A validator goes there.
- Which job(s) **read** data conforming to this contract? (e.g., the bronze→silver transform reads the bronze contract; the silver→gold transform reads the silver contract; downstream consumers read the gold contract.) A validator goes there too.

For each boundary the user names, the skill will plan a validator. The user may opt out of a side per boundary (e.g., "the extract job has its own typed schema; skip write-side bronze"), but the skill should warn that single-sided enforcement is fragile and the reason for opting out should be recorded as a comment in the emitted file.

If the user is unsure which jobs touch the contract, ask them to enumerate the boundaries first; the rest of the interview is shaped by the answer.

### Which validator(s) to emit

For each boundary identified above (write side and read side), ask which of {dbt model contract, dbt-expectations/dbt-utils tests, Great Expectations suite, Soda checks, Pandera schema, Pydantic model} should be emitted. The write-side and read-side validators often differ in tool: e.g., the producer is a Python extract job (Pandera on write) and the consumer is a dbt transform (dbt model contract + tests on read). Match the tool to where the job actually runs.

Multi-select per boundary is fine; many projects want both a dbt-layer enforcement and a Python-layer enforcement at the same boundary, because they run at different points in the pipeline.

Default the answer to whatever host-stack detection found for the job at that boundary, but always confirm.

### Where outputs land

Per chosen validator, ask the file path:

- **dbt model contract** — `models/<layer>/<dataset>.yml` (alongside the model SQL). If a `schema.yml` already exists, append to it; if not, create the `.yml` next to the model. Confirm the schema-file pattern the repo uses (`schema.yml` per directory vs `<model>.yml` per model).
- **Great Expectations suite** — `great_expectations/expectations/<title>.json` or `gx/expectations/<title>.yaml` (GE v3+ uses YAML for fluent suites; v2 uses JSON). Confirm GE version.
- **Soda checks** — `soda/checks/<title>.yml` or `checks/<title>.yml`, matching repo convention.
- **Pandera schema** — `<package>/schemas/<title>.py`. Confirm package path.
- **Pydantic model** — `<package>/models/<title>.py`. Confirm package path.

If the path already exists, ask: overwrite, append, or pick a new path? Default: prompt every time before overwriting.

### Wire-up to test / CI / scheduler

Validators that don't run don't enforce. Ask how each emitted validator should be invoked:

- **dbt** — `dbt build` or `dbt test` in CI? Tag the new tests with `data-contract` so they can be filtered? The skill emits the `tags:` attribute by default.
- **Great Expectations** — invoked from a checkpoint? From a pipeline step? From a pytest fixture? The skill emits the suite file; wiring is a one-line snippet shown in the conversation.
- **Soda** — invoked from `soda scan`? From an Airflow operator? Daily cron? The skill emits the checks file and shows the run command.
- **Pandera** — invoked as a decorator on a pipeline function (`@pa.check_input(...)`), as a standalone validation call, or as a Hypothesis strategy in tests? Default: emit a `validate(df: pl.DataFrame | pd.DataFrame) -> ...` function so the caller wires it where they want.
- **Pydantic** — typically used at API or message boundaries, not for full-table validation. Confirm the intended use; if the user wants full-table enforcement, push them toward Pandera or GE instead.

### Layer-strictness defaults

If `info.layer` is set on the contract, apply defaults:

- **bronze** — schema-only validation. The skill skips quality block translation even if the block is present, and warns the user that bronze validators are intentionally minimal.
- **silver** — schema + uniqueness + FK + ranges + enums. If `quality.uniqueness` is absent on the contract, warn: silver datasets should have at least one uniqueness constraint.
- **gold** — schema + uniqueness + FK + ranges + enums + freshness. Freshness emits as a custom check (dbt: a freshness test; GE: a custom expectation referencing the SLA; Soda: a `freshness` block). Already verified at input time that the gold requirements are present in the contract.

Ask the user once to confirm the layer-strictness defaults; do not silently apply them.

### Field-level translation rules

For each ODCS field, translate to the chosen validator(s) using the table below. When a field exists in ODCS that the target tool cannot express, surface as a warning in the conversation (and as a comment in the emitted file) rather than silently dropping it.

| ODCS                                  | dbt contract + tests                          | Great Expectations                                | Soda checks                       | Pandera                           | Pydantic                          |
|---|---|---|---|---|---|
| `schema.fields[].type`                | `data_type` in contract                       | `expect_column_values_to_be_of_type`              | implicit (typed warehouse)        | `pa.Column(<dtype>)`              | `<field>: <type>`                 |
| `schema.fields[].required: true`      | `constraints: [{type: not_null}]`             | `expect_column_values_to_not_be_null`             | `missing_count(col) = 0`          | `nullable=False`                  | non-Optional type                 |
| `quality.uniqueness.fields: [a]`      | `tests: [unique]`                             | `expect_column_values_to_be_unique`               | `duplicate_count(a) = 0`          | `unique=True`                     | (n/a)                             |
| `quality.uniqueness.fields: [a, b]`   | `tests: [dbt_utils.unique_combination_of_columns]` | `expect_compound_columns_to_be_unique`       | `duplicate_count(a, b) = 0`       | `pa.Check(...)` row-wise          | (n/a)                             |
| `quality.ranges`                      | `tests: [dbt_expectations.expect_column_values_to_be_between]` | `expect_column_values_to_be_between`  | `min(col) >= X and max(col) <= Y` | `pa.Check.in_range(...)`          | `Field(ge=X, le=Y)`               |
| `quality.enums`                       | `tests: [accepted_values]`                    | `expect_column_values_to_be_in_set`               | `invalid_count(col) = 0` with values | `pa.Check.isin([...])`         | `Literal[...]`                    |
| `quality.references`                  | `tests: [relationships]`                      | (custom) — load referenced data, check membership | `failed rows for ... reference`   | (cross-frame; usually skip)       | (n/a)                             |
| `quality.freshness_sla.max_lag`       | `dbt source freshness` or custom test         | custom expectation                                | `freshness(col) < duration`       | (n/a — runtime check)             | (n/a)                             |
| `schema.fields[].semantics`           | passes through as `description`               | passes through as expectation `meta`              | passes through as `meta`          | passes through as docstring       | passes through as `Field(description=...)` |
| `schema.fields[].pii: true`           | `meta: {pii: true}`                           | passes through as expectation `meta`              | passes through as `meta`          | passes through as field metadata  | passes through as `Field(...)` json_schema_extra |
| `info.x-breaking-change-policy`       | passes through as `meta:` on the model        | (no native home — emit comment)                   | (no native home — emit comment)   | (no native home — emit comment)   | (no native home — emit comment)   |

Whenever the table says "no native home", the emitted file should include a comment block citing the dropped field and pointing back to the `data-contract-core` skill so a future reader knows the contract is the source of truth.

## Output: render then write

For each chosen validator:

1. **Render** the emitted file content in the conversation. Show the full file, not a diff.
2. **Show the wire-up snippet** (CI command, decorator usage, checkpoint config).
3. **Show the warnings list** — ODCS fields that couldn't translate cleanly, plus layer-strictness warnings (e.g., "silver contract has no uniqueness constraints").
4. **Ask for the path** (use detection defaults as the suggested answer).
5. **Write** only after confirmation. If multiple validators were chosen, batch the path confirmations into one round.

After writing, print a one-paragraph summary: which files landed, which test commands the user should run next, and any open warnings the user should acknowledge.

## Per-stack output specs

### dbt model contract + tests

Emit a YAML block under `models[]`:

```yaml
models:
  - name: <title>
    config:
      contract:
        enforced: true
      tags: [data-contract]
    description: <from info.description>
    meta:
      odcs_version: <info.version>
      odcs_owner: <info.owner>
      odcs_layer: <info.layer>
      odcs_path: <path to source contract>
    columns:
      - name: <field>
        data_type: <field.type>
        constraints:
          - type: not_null              # if required: true
        tests:
          - unique                       # if uniqueness on this field
          - accepted_values:             # if enums
              values: [...]
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: <quality.ranges.min>
              max_value: <quality.ranges.max>
          - relationships:               # if FK
              to: ref('<referenced.title>')
              field: <referenced.contract_field>
```

For multi-column uniqueness, emit `tests:` at the model level using `dbt_utils.unique_combination_of_columns`. For freshness, emit a `sources:` block or a custom `tests/freshness.sql` test referencing the contract's `freshness_sla.max_lag`.

### Great Expectations expectation suite

Emit a fluent suite. Default to GE v3 YAML format; ask if the project is on v2.

```yaml
name: <title>
expectations:
  - expectation_type: expect_column_to_exist
    kwargs:
      column: <field>
  - expectation_type: expect_column_values_to_be_of_type
    kwargs:
      column: <field>
      type_: <ODCS type mapped to GE type>
  # ... one per field per applicable rule
meta:
  odcs:
    title: <info.title>
    version: <info.version>
    owner: <info.owner>
    layer: <info.layer>
    path: <path to source contract>
```

### Soda Core checks

Emit a Soda checks file:

```yaml
checks for <warehouse_table>:
  - schema:
      fail:
        when required column missing: [<field>, ...]
        when wrong column type:
          <field>: <type>
  - missing_count(<field>) = 0   # for each required field
  - duplicate_count(<field>) = 0  # for each uniqueness constraint
  - invalid_count(<field>) = 0:
      valid values: [...]         # for each enum
  - min(<field>) >= <min>          # for each range
  - max(<field>) <= <max>
  - freshness(<col>) < <duration>  # for freshness SLA
```

`<warehouse_table>` resolves from the contract's `servers[].location` when possible; if multiple servers, ask.

### Pandera schema

Emit a Python module:

```python
"""Pandera schema generated from <info.title> ODCS contract.

Contract: <path to source contract>
Version:  <info.version>
Owner:    <info.owner>
Layer:    <info.layer or 'unset'>
"""

import pandera as pa
from pandera.typing import Series


class <PascalCaseTitle>(pa.DataFrameModel):
    <field>: Series[<pandera type>] = pa.Field(
        nullable=<not required>,
        unique=<true if single-column uniqueness>,
        in_range={"min_value": <min>, "max_value": <max>},  # if range
        isin=[...],                                          # if enum
        description="<semantics>; <description>",
    )
    # ... one Series per field

    class Config:
        strict = True
        coerce = False
```

For multi-column uniqueness, emit a `@pa.dataframe_check` decorator on a class method. Mirror the project's existing Pandera style if `pa.DataFrameSchema` (functional) is used instead.

### Pydantic model

Emit a Python module:

```python
"""Pydantic model generated from <info.title> ODCS contract.

Contract: <path to source contract>
Version:  <info.version>
Owner:    <info.owner>
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class <PascalCaseTitle>(BaseModel):
    <field>: <type or Optional[type]> = Field(
        description="<semantics>; <description>",
        ge=<min>,                 # if range
        le=<max>,
    )
    # enum-typed fields use Literal[...]

    model_config = {"extra": "forbid"}
```

Emit Pydantic v2 syntax by default. Switch to v1 (`Config` inner class, `Field(...,)` without `model_config`) if detection finds Pydantic <2.

## Composition with other skills

- **Upstream**: `/draft-data-contract` produces the contract this skill consumes.
- **Sibling**: `/synth-from-contract` consumes the same contract and emits fake data for tests; the validators emitted here and the fakes emitted there are designed to round-trip cleanly. A fake passed through the validator should always pass.
- **Reference**: the `data-contract-core` skill documents the ODCS profile this skill reads. Link to it in every emitted file's header comment.

## Guidelines

- **The contract is the source of truth.** Never edit it from this skill, and never silently drop ODCS fields the target tool can't express — surface them as warnings and as comments in the emitted file. The next reader needs to know the validator is incomplete relative to the contract.
- **Enforce on both write and read.** Default to wiring a validator on both sides of every boundary the contract crosses: the producer validates on write, the next consumer validates on read. Single-sided enforcement is the default failure mode for data contracts in the wild — writers trust their own code, readers trust the upstream, and bad rows land silently in between. The user may opt out per boundary, but warn and require a reason recorded as a comment in the emitted file. See the "Enforcement boundaries" section of `data-contract-core` for the medallion-flow picture.
- **Emit only what the user asked for.** If the user picked Pandera, don't also write a Soda file. Multi-validator emission is opt-in.
- **Layer strictness is non-negotiable for gold.** If a gold contract is missing freshness or FK / uniqueness, refuse to emit and route back to `/draft-data-contract`. The whole point of the layer is the strictness contract.
- **Test the validators, don't just emit them.** Show the run command in the conversation and recommend the user run it before committing. A validator file the user can't invoke is no enforcement at all.
- **Mirror the host project's existing style.** dbt projects have a `schema.yml` pattern; Pandera projects use class-based or functional schemas; Pydantic projects pin a major version. Detect first, ask second, emit third.
- **Don't fabricate library APIs.** If the user asks for a tool the skill doesn't know (e.g., a newer GE-fluent version, an alternate dbt-test library), pause and ask the user for a syntax sample instead of guessing.
- **Plain text only. No emojis.** Match the rest of the skills.
