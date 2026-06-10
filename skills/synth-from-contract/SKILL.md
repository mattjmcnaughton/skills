---
name: synth-from-contract
description: >-
  Take an Open Data Contract Standard (ODCS) YAML contract and generate
  realistic, constraint-respecting synthetic data for tests, demos, and
  local development. Honors enums, ranges, regex formats, nullability,
  uniqueness, and cross-contract foreign-key references resolved via
  topological order across multiple contracts. Output formats are picked
  at runtime: Parquet, CSV, JSON Lines, a DuckDB table, or a Python
  Faker factory class downstream callers can subclass. Deterministic by
  default (seeded RNG) so tests don't flake. Tier-2 generation only:
  constraint-respecting but not distribution-learning — SDV /
  distribution-fit is documented as an out-of-scope follow-up. Use when
  the user has a contract (typically from `/draft-data-contract`) and
  needs realistic fixtures for unit tests, integration tests, local
  demos, or seeding a dev warehouse. Triggers include "fake data for
  this contract", "synth from this contract", "generate fixtures for
  <dataset>", "seed dev data from <contract>", "Faker factory for this
  contract". Produces data only — does not modify the contract.
---

`/synth-from-contract` is a generator. One conversation, one or more synthetic-data artifacts: rows that satisfy the schema, semantics, and quality constraints of an ODCS contract, materialized in the format the user picks (Parquet file, CSV, JSON Lines, DuckDB table, or a Faker factory class).

The skill does not modify the contract. It does not emit validators (that is `/enforce-data-contract`). It generates data that, when fed through the validators emitted by `/enforce-data-contract` from the same contract, passes — that round-trip guarantee is the whole point.

## When to use

- The user has an ODCS contract and needs realistic fixtures for unit or integration tests.
- The user wants to seed a local dev warehouse / DuckDB / dbt project with conformant rows for a dataset that doesn't have production data yet (or whose production data is too sensitive to use locally).
- The user is wiring `/enforce-data-contract` validators and wants test inputs that exercise both the happy path and the edges.
- The user is building a demo and needs the dataset to look plausible without leaking real data.

## When not to use

- The user wants synthetic data that statistically mimics a real source distribution — out of scope for v1. The skill respects constraints but does not learn distributions. Route to SDV (`https://sdv.dev`), Gretel, or a similar tier-3 tool. This is a deliberate scope cut to keep the skill self-contained and reproducible.
- The user wants the contract written or revised — go to `/draft-data-contract`.
- The user wants validators for the contract — go to `/enforce-data-contract`.
- The user wants production data to pass through a redaction pipeline — different problem (anonymization, not synthesis). Out of scope.
- The dataset is too narrow to fake usefully (e.g., a contract describing a single global config row) — flag it and ask the user to confirm before emitting.

## Input

One positional input: the ODCS contract path (or paths, plural — see FK resolution below).

If no path is given, ask. Suggested defaults match `/enforce-data-contract`: `.agentic/<slug>/<title>.odcs.yaml`, `contracts/<title>.odcs.yaml`, `models/<layer>/<dataset>.odcs.yaml`.

Before interviewing, load the contract and verify it satisfies the required-fields bar from the `data-contract-core` skill. If required fields are missing, stop and route back to `/draft-data-contract`.

## The interview

Cover, in order:

### Output format(s)

Ask explicitly which format(s) to emit. Multi-select is fine; common combinations are "Parquet for the test fixture + Faker factory class for downstream unit tests."

- **Parquet** — single `.parquet` file per contract. Best for warehouse-shaped fixtures and PyArrow / Polars / Pandas consumption.
- **CSV** — single `.csv` file. Best for human inspection or where Parquet is overkill. Loses type fidelity (everything round-trips as string); the skill warns when emitting CSV for a contract with non-string types.
- **JSON Lines** — one JSON object per line. Best for stream- or message-shaped fixtures and for contracts with nested `object` / `array` fields.
- **DuckDB table** — write directly into a DuckDB database file at a user-supplied path. Best for local-warehouse dev setups; the skill emits a `CREATE TABLE` matching the contract types and inserts the generated rows.
- **Python Faker factory class** — emit a `<Title>Factory` class that callers can instantiate, override per field, and `.build()` / `.build_batch(n)` against. Best for unit tests where each test wants slight variations. Uses `factory-boy` style by default; ask if the project uses an alternative.

### Row count and shape

- **Row count** — how many rows? Default: 1000. For Faker factory output, "row count" means default `build_batch(n)` size.
- **Edge-case coverage** — should the output include a row per enum value (so every branch is exercised), boundary rows (min/max for each range), null rows for every nullable field, and rows where every optional field is present and absent? The skill calls this the "coverage gallery"; default to yes. The gallery rows come *in addition* to the requested row count, with a small marker column or as a separate output (user picks).
- **Skew** — should certain enum values be more frequent than others? Default no (uniform). If the contract has a `quality.distribution` block with `expected_proportions`, default to using it but confirm.

### Determinism

- **Seed** — what RNG seed? Default: `42`. Always seed; non-deterministic synthetic data makes tests flaky.
- **Salt** — for FK and uniqueness, the skill derives values from the seed plus a per-field salt. Surface this once so the user knows tests stay stable across runs.

### FK strategy (when multiple contracts are passed)

If the user passes more than one contract, scan their `quality.references` blocks to build a dependency graph. Then:

- **Topological order** — generate referenced contracts first, then dependents. The skill records the order in the run summary so the user can reproduce.
- **FK pool size** — when generating a dependent, sample FK values from the referenced contract's generated rows. Ask: should every referenced row appear at least once (full coverage), or just be sampled with replacement (default)?
- **Cycle in the FK graph** — refuse to generate. Cycles in references almost always mean a contract authoring error; surface as an error and route back to `/draft-data-contract`.
- **Reference target not in the input set** — warn. The skill generates FK values from the contract's `semantics` tag (e.g., `uuid_v4`) but cannot guarantee membership in the referenced dataset. Recommend running the skill on both contracts together.

If only one contract is passed and it has `quality.references` to a contract not in the input set, the warning above applies.

### Output destination

Per chosen format, ask the file/table path:

- **Parquet** — default `.agentic/<slug>/fixtures/<title>.parquet` if in a workspace, else `tests/fixtures/<title>.parquet`.
- **CSV** — same defaults as Parquet, swapping the extension.
- **JSON Lines** — same, with `.jsonl`.
- **DuckDB** — default `.agentic/<slug>/fixtures/synth.duckdb` (single DB, table named `<title>`); else `tests/fixtures/synth.duckdb`.
- **Faker factory** — default `<package>/factories/<title>.py`. Confirm package path from host-repo detection.

If the path already exists, ask: overwrite, version-bump suffix, or pick a new path? Default: prompt every time.

## Generation strategy (tier 2)

The skill walks the contract's schema and quality blocks deterministically. Per-field rules:

### Type-driven primitives

- **string** — `mimesis.Generic` or `faker.Faker` instance, seeded. Default value depends on the `semantics` tag; without a tag, generate a short ASCII slug.
- **integer / number** — uniform within `quality.ranges.min/max` if present; else `[-2^31, 2^31)` for integer, `[-1e6, 1e6)` for number. Skip `NaN` / `inf` unless the user explicitly asks for them as edge cases.
- **boolean** — uniform 50/50 unless skewed.
- **timestamp / date** — within the last 90 days by default; if the contract has a freshness SLA, anchor the most recent row at `now() - random(0, SLA/2)` so the data looks fresh. Confirm with the user if the use case wants a different window.
- **object / array** — recurse on the nested schema if present; if not (raw `object`), emit `{}` and warn.

### Semantics-driven realism

If `schema.fields[].semantics` is set, override the primitive generation:

| Semantics tag                  | Generator                                                   |
|---|---|
| `uuid_v4`                      | `uuid.uuid4()` (seeded via RNG)                             |
| `iso_country_alpha2`           | sample from ISO 3166-1 alpha-2 list                         |
| `iso_currency_alpha3`          | sample from ISO 4217 alpha-3 list                           |
| `email`                        | `<slug>@example.<tld>` (RFC 2606 reserved domain)           |
| `e164_phone`                   | `+1` + 10-digit number; pin country if context allows       |
| `currency_usd_minor_units`     | integer in [0, 1_000_000_000], gated by `quality.ranges`    |
| `epoch_ms` / `epoch_s`         | integer derived from timestamp window                       |
| `iban`                         | mimesis IBAN generator (if available)                       |
| Unknown semantics              | fall back to type-driven primitive, warn once               |

Add semantics tags incrementally; the table above is the v1 surface, not a closed set.

### Constraint-driven assertions

- **enum** — sample from `quality.enums.values`. If the user opted into the coverage gallery, guarantee at least one row per enum value.
- **range** — integer/number generators clamp to `[min, max]`.
- **uniqueness** — for single-column uniqueness, use a stateful generator (per-row counter or RNG-without-replacement) and assert no collisions in a post-generation pass. For multi-column uniqueness, the post-pass tuple-checks.
- **references** — sample from the FK pool built during topological generation (see above).
- **freshness_sla** — affects timestamp anchoring (see above). No separate generator.
- **distribution** — used as the skew distribution if the user opted in during interview.
- **row_count** — informational; the requested row count must satisfy the contract's `row_count.min`, else warn.

### Coverage gallery

When the gallery is on (default), append rows that exercise:

- One row per enum value, for every enum-typed field.
- A row with the minimum value for each range, and one with the maximum.
- A row with each nullable field null (one row per such field; rest of the row is typical).
- A row with each optional field absent (for JSONL / Faker factory; n/a for Parquet/CSV where every column is present).
- A `pii: true` field gets generated with explicitly fake-marked values (`first.last+fake@example.com`) so accidental leakage of synthetic data is obviously synthetic.

The gallery is a small fixed cost (~10-30 rows depending on the contract) added on top of the requested row count.

## Output: render then write

For each chosen format:

1. **Show a preview** in the conversation: the first 5 generated rows (Parquet/CSV/JSONL) or the Faker class definition (Faker factory). Don't render the full N rows.
2. **Show the warnings list** — unknown semantics tags, missing reference targets, unsupported nested types.
3. **Show the run summary** — row count requested, gallery rows added, seed, FK pool sizes, topological order if multi-contract.
4. **Ask for the path** (defaults above).
5. **Write** only after confirmation.

After writing, print the obvious next steps:

- Run the validators emitted by `/enforce-data-contract` against this fixture; everything should pass. If anything fails, that's a bug in either the synth or the contract.

## Per-format output specs

### Parquet

Use PyArrow or Polars (mirror host project). Type mapping from ODCS to Arrow:

| ODCS         | Arrow                |
|---|---|
| `string`     | `string`             |
| `integer`    | `int64`              |
| `number`     | `float64`            |
| `boolean`    | `bool`               |
| `timestamp`  | `timestamp[us, UTC]` |
| `date`       | `date32`             |
| `object`     | `struct<...>` (recursive) or `string` (JSON-encoded) — ask |
| `array`      | `list<...>` (recursive) or `string` (JSON-encoded) — ask  |

Emit a `_meta` Parquet key referencing the source contract path and version so downstream readers can trace provenance.

### CSV

Use stdlib `csv` or Polars. Warn that non-string types round-trip as string; offer to emit a sibling `<title>.csv.schema.json` describing types for re-import.

### JSON Lines

One JSON object per line. Strict UTF-8. Encode timestamps as ISO 8601 with timezone offset; encode dates as `YYYY-MM-DD`. Encode `null` for absent nullable fields; omit absent optional fields (this difference matters for downstream consumers).

### DuckDB table

Emit a Python snippet:

```python
import duckdb

con = duckdb.connect("<db path>")
con.execute("""
    CREATE OR REPLACE TABLE <title> (
      <field> <duckdb type> [NOT NULL],
      ...
    )
""")
con.execute("INSERT INTO <title> VALUES ...")
```

Type mapping: same as Parquet, with DuckDB names (`BIGINT`, `DOUBLE`, `BOOLEAN`, `TIMESTAMP`, `DATE`).

### Faker factory class

```python
"""Faker factory generated from <info.title> ODCS contract.

Contract: <path to source contract>
Version:  <info.version>
Owner:    <info.owner>

Build single row: <Title>Factory.build()
Build N rows:    <Title>Factory.build_batch(n)
Override field:  <Title>Factory.build(status='settled')
"""

import factory
from factory import Faker
from <package>.schemas.<title> import <PascalCaseTitle>   # if Pandera schema exists

SEED = 42


class <PascalCaseTitle>Factory(factory.Factory):
    class Meta:
        model = dict   # or <PascalCaseTitle> if a Pandera/Pydantic class is wired in

    <field> = Faker("<faker provider>", **{...})
    # ... one assignment per field, with constraints encoded

    @classmethod
    def _setup_next_sequence(cls):
        return 0
```

For fields with enums/ranges/semantics that Faker doesn't natively express, emit a `LazyFunction` referencing a small inline helper. Keep the file self-contained.

## Composition with other skills

- **Upstream**: `/draft-data-contract` produces the contract this skill consumes.
- **Sibling**: `/enforce-data-contract` consumes the same contract and emits validators. The fakes this skill emits round-trip cleanly through those validators by construction.
- **Reference**: the `data-contract-core` skill documents the ODCS profile this skill reads. Link in every emitted file's header comment.

## Out of scope (deliberate)

- **Tier-3 distribution-learning synthesis** — SDV-style generators that learn marginal and joint distributions from a real source. Powerful but heavy: brings in PyTorch / SDV / etc., requires a real source dataset, and is non-deterministic without significant work. Out of v1 by design. Users who need it should reach for SDV directly; this skill's job is to be a no-real-data, deterministic, constraint-respecting fixture generator that test suites can rely on.
- **Anonymization pipelines** — separate problem class; needs real data as input and a redaction policy. Out of scope.
- **Streaming generators** — this skill emits batches. For continuous synthetic event streams (Kafka producers, etc.), the Faker factory output is the closest fit; wrap it in a producer loop.

## Guidelines

- **Deterministic by default.** Always seed. Document the seed in the run summary so reproducing a failed test is one re-run away.
- **Respect every constraint in the contract.** If the contract has a uniqueness constraint and the requested row count exceeds the achievable uniqueness, refuse to generate and warn — don't silently emit duplicates.
- **Round-trip with `/enforce-data-contract`.** The most useful invariant in this skill family: data emitted from contract C, fed through the validators emitted from contract C, passes. Test this in your head before writing; if you can't, the generation strategy has a bug.
- **Coverage gallery is high-leverage.** Default it on. The marginal cost is small; the value of "every enum branch is exercised in every test fixture" is huge.
- **Don't fabricate semantics.** If the contract's `semantics` tag is unknown to the skill, fall back to type-driven generation and warn — don't make up a generator. The user will refine the semantics tag set over time; the skill should be honest about what it doesn't recognize.
- **Don't lie about determinism with concurrency.** If the user wires the generator into a parallel pipeline, document that per-row determinism requires the user to seed per-task, not just globally.
- **PII fields produce obviously-fake values.** Even though the data is synthetic, generated PII that looks real (a plausible email at a real domain) is dangerous if a fixture leaks into a non-test environment. Use RFC 2606 reserved domains, `555-` phone prefixes, `0000-` SSN patterns, etc.
- **Plain text only. No emojis.** Match the rest of the skills.
