---
name: audit-data-contracts
description: >-
  Audit a host repo (dbt project, Python pipeline, Spark jobs, ad-hoc SQL,
  warehouse views) for implicit data contracts that should be made explicit
  as Open Data Contract Standard (ODCS) YAML. Interviews the user about
  which paths to scan, which stacks are in play, and whether medallion
  layering is used; then surfaces datasets without owners, schemas without
  documented nullability, columns that look like enums but aren't pinned,
  pipelines without freshness SLAs, and dataframes whose schemas live only
  in code. Produces a terminal report with finding-driven recommendations
  and a per-finding next-step `/draft-data-contract` invocation. Use
  before adopting contracts in a project that doesn't have them, before a
  medallion-architecture migration, or when a downstream consumer keeps
  getting surprised by upstream changes. Triggers include "audit data
  contracts", "find unwritten contracts", "where are the implicit
  contracts in this repo", "scan for missing data contracts", "data
  contract gap analysis".
---

`/audit-data-contracts` answers three questions about a data project that doesn't yet have explicit contracts:

1. **Which datasets in this project should have a contract?** Bronze-shaped raw ingests, silver-shaped conformed tables, gold-shaped serving tables — and the dataframes between them.
2. **For each, what's missing relative to the ODCS profile?** Ownership, schema-with-nullability, semantic tags, enums, ranges, FK references, freshness SLA, layer designation.
3. **What's the highest-leverage next step?** A prioritized list of `/draft-data-contract <dataset>` invocations the user can run to close the most-painful gaps first.

The audit is intent-calibrated: a missing freshness SLA on a bronze raw-ingest table is a low finding; the same gap on a gold serving table is critical. The skill interviews the user up front to calibrate before any scanning.

## When to use

- Before a team adopts data contracts as a practice and wants to know which datasets to start with.
- Before a medallion-architecture migration, to see which existing tables already act like bronze / silver / gold without saying so.
- When a downstream consumer reports surprises — a column changed type, an enum gained a value, a freshness regression — and the team suspects more such gaps exist.
- After a refactor that moved a pipeline boundary; the new boundary likely needs a contract.

## When not to use

- The user wants the contract written, not the audit — go to `/draft-data-contract`.
- The user wants the contract enforced — go to `/enforce-data-contract`.
- The user wants to audit a third-party codebase for security risk — different skill, `/audit-third-party`.
- The user wants to audit data *quality* (anomaly detection, drift) — out of scope; this skill audits the *agreement layer*, not the data values themselves.
- The user wants a formal data-governance review covering retention, access control, lineage — bigger than this skill; the audit is a first-pass technical finding list, not a governance deliverable.

## Process

### Step 1 — Interview the user about intent

Ask the user the following, batched. The answers calibrate every finding's severity in Step 3.

1. **Paths to scan** — which directories should the audit cover? Defaults: `models/` (dbt), `src/`, `pipelines/`, `dags/`, `notebooks/`, anywhere else the user names. Exclude `tests/`, `.venv/`, `node_modules/`, build directories.
2. **Stacks in play** — which of {dbt, Polars, Pandas, PySpark, plain SQL via a warehouse, dlt, Dagster, Airflow, Prefect, Kafka producers/consumers} are used? Multi-select.
3. **Medallion architecture** — yes / no / partial. If yes or partial, ask how layers are distinguished (directory names, dbt model prefixes, schema names, naming conventions).
4. **Downstream consumers** — internal teams, external customers, ML training pipelines, BI dashboards? The consumer list disciplines what counts as a serving / gold boundary.
5. **Existing contracts** — does the repo already have any ODCS contracts? Path to them if yes. The skill won't re-audit datasets that already have a contract; it focuses on the gaps.
6. **Tolerance** — does the user want everything flagged (including INFO), or only HIGH / CRITICAL? Default: everything; surface even small gaps so the user can choose.

Persist nothing. Interview answers stay in conversation context and inform Step 3 severity assignment. If the user wants the audit captured for later, Step 5 offers to write the report to a file.

### Step 2 — Map the codebase

Before scanning, get the lay of the land:

- `README.md`, `docs/` — what does the project say it does?
- `dbt_project.yml`, `pyproject.toml`, `requirements.txt`, `package.json` — language(s) and dependency manifest.
- `models/` layout — for dbt projects, note directory structure (e.g., `staging/`, `intermediate/`, `marts/`) and whether `schema.yml` files exist alongside models.
- `migrations/` or `sql/` — raw SQL DDL.
- Any existing contracts directory the interview surfaced.

Note the latest commit SHA (`git rev-parse HEAD`) so the report is reproducible.

### Step 3 — Run the four scans

Each finding gets: **category**, **severity** (CRITICAL / HIGH / MEDIUM / LOW / INFO), **evidence** (`file:line` citations), **inferred layer** (bronze / silver / gold / unknown), and **recommendation** with a suggested `/draft-data-contract <dataset>` invocation.

Severity is calibrated against the Step 1 intent:

- A missing owner on a gold (serving) table is CRITICAL; on a bronze raw-ingest is MEDIUM.
- A missing freshness SLA on a gold table is HIGH; on bronze is LOW.
- An implicit enum (a string column with a closed value set in practice) is MEDIUM regardless; consumers depend on it.
- A dataframe with no schema at all in code is HIGH at any layer; the pipeline can break silently.

#### Scan A — dbt models without contracts

For each `models/**/*.sql`:

- Is there a sibling `schema.yml` (or `<model>.yml`) entry? Cite the path.
- Does the model have `config.contract.enforced: true`? Cite the line or note absent.
- Are columns documented with `data_type` and constraints? Cite gaps.
- Is `meta.owner` (or equivalent) set? Cite absent.
- For models in a directory that looks like a serving layer (`marts/`, `gold/`, `fct_`, `dim_` prefixes), are tests defined? Cite gaps.

Output one finding per missing dimension per model. Group by model in the report.

#### Scan B — Dataframes and code-defined schemas

For Polars, Pandas, PySpark code:

- `pl.DataFrame(...)` / `pd.DataFrame(...)` / `spark.createDataFrame(...)` constructed without an explicit schema. Cite.
- `pd.read_csv` / `pl.read_csv` / `spark.read.csv` without a `dtype` / `schema` argument — type inference is convenient and a liability.
- Functions that return a dataframe but have no type hint / docstring describing the columns. Cite.
- Pandera / Pydantic / `dataclass` schemas that *are* defined but live far from the boundary where they're used. Cite as INFO — the schema exists but isn't pinned at the producer/consumer boundary.

For each: name the pipeline boundary the dataframe represents (function name + caller) and suggest the dataset name a contract would use.

#### Scan C — SQL views and warehouse tables

For each `.sql` file with `CREATE VIEW`, `CREATE TABLE`, or `CREATE OR REPLACE`:

- Are column comments present?
- Are types explicit or inferred (`CREATE TABLE x AS SELECT ...` is a finding)?
- Is the table named in a way that suggests serving (`fct_`, `dim_`, `agg_`, `mart_`)? If yes, severity bumps.
- For warehouse `INFORMATION_SCHEMA` exports the user provides, flag tables with no `OBJECT_OWNER` set.

#### Scan D — Implicit contracts in semantics

The hardest scan and the highest-value. Walk the data layer for:

- **Implicit enums** — a string column whose values come from a closed set in code (e.g., `CASE WHEN status IN ('pending', 'settled', 'refunded') THEN ...`). The enum is real; it just isn't written. Cite the use-site, name the column, list the values.
- **Implicit FKs** — a column that looks like `*_id` and is joined to another table's `id` column anywhere in the codebase. Cite both sides.
- **Implicit ranges** — numeric columns checked against literal bounds (e.g., `WHERE amount > 0 AND amount < 1000000`). The range is real; it just isn't pinned.
- **Implicit freshness** — pipeline code that filters on a recency window (`WHERE updated_at > now() - interval '1 hour'`). That's an SLA expressed as code; pin it as a contract.
- **Implicit semantics** — column names containing `amount`, `cents`, `minor_units`, `pct`, `usd`, `ms`, `epoch`, `email`, `phone` with no `semantics` tag in any docs. Cite each.

Each implicit-contract finding gets a one-line suggested resolution: "field <name> is used as an enum at <file:line>; pin in the contract as `quality.enums.field=<name>, values=[...]`."

### Step 4 — Rank the findings

Group by inferred layer, then by severity. Within severity, prefer findings that:

1. Block a downstream consumer the user named in Step 1.
2. Sit at a pipeline boundary multiple consumers depend on (high-leverage to fix once).
3. Have an implicit enum or FK present in code — these are the cheapest contracts to draft because the values are already discoverable from the codebase.

The report's top section is the ranked next-step list: 5–10 datasets ordered by which `/draft-data-contract` invocation would close the most pain.

### Step 5 — Report

Print the report to the terminal in the format below. The report has three sections:

1. **Headline** — count of datasets-with-gaps by inferred layer, plus the top-priority next steps.
2. **Findings** — grouped by dataset, ordered by inferred layer (gold first, then silver, then bronze, then unknown).
3. **Suggested next steps** — the prioritized list of `/draft-data-contract <dataset>` invocations.

Then ask once: "Save this report to a file?" If yes, default to `./contracts-audit-<shortsha>.md` in the current working directory; offer `.agentic/audits/contracts-<shortsha>.md` if the user is in a workspace with `.agentic/`.

## Report format

```
Data contract audit: <repo>
Source: <repo path>  (commit <shortsha>)

Intent calibration
  Paths scanned:        <list>
  Stacks in play:       <list>
  Medallion:            <yes | no | partial — how distinguished>
  Downstream consumers: <list>
  Existing contracts:   <count, with path>
  Tolerance:            <all | high-only>

============================================================
HEADLINE: Contract gaps by layer
============================================================
  Gold-shaped datasets without contracts:    <N>
  Silver-shaped datasets without contracts:  <N>
  Bronze-shaped datasets without contracts:  <N>
  Unknown-layer datasets without contracts:  <N>

Top priorities (highest leverage to draft first):
  1. <dataset>  (<inferred layer>)  — closes <N> findings, blocks <consumer>
     Next:  /draft-data-contract <dataset>
  2. ...

============================================================
Findings
============================================================

[Gold] <dataset>
  CRITICAL  missing-owner             <file:line>
    What: no owner set anywhere
    Recommend: pin `info.owner` in the contract
    Next:      /draft-data-contract <dataset>

  HIGH      missing-freshness-sla     <file:line>
    What: pipeline filters on `updated_at > now() - 1h` but the SLA is uncoded
    Recommend: pin `quality.freshness_sla.max_lag: 1h`
    Next:      /draft-data-contract <dataset>

  MEDIUM    implicit-enum             <file:line>
    What: column `status` is filtered to {pending, settled, refunded, disputed}
          at <file:line> but has no enum constraint
    Recommend: pin `quality.enums.field=status` with the discovered values
    Next:      /draft-data-contract <dataset>

[Silver] <dataset>
  ...

[Bronze] <dataset>
  ...

[Unknown] <dataset>
  ...

============================================================
Suggested next steps (ordered)
============================================================
  1. /draft-data-contract <dataset-1>     # gold, closes 5 findings
  2. /draft-data-contract <dataset-2>     # silver, closes 3 findings
  ...

After each `/draft-data-contract`, the natural follow-on is:
  /enforce-data-contract <contract-path>   # to emit validators
  /synth-from-contract <contract-path>     # to emit fixtures

Summary: <X CRITICAL> <Y HIGH> <Z MEDIUM> <W LOW> across <N> datasets
```

When the audit is clean (no findings above INFO), collapse to:

```
Data contract audit: <repo>  (commit <shortsha>)

Headline: every detected dataset has an ODCS contract.

  [A] dbt models     CLEAN
  [B] Dataframes     CLEAN
  [C] SQL views      CLEAN
  [D] Implicit       CLEAN

Suggested next: nothing pending. Re-audit after the next pipeline boundary lands.
```

## Calibrating severity

Use the Step 1 answers as the lens. A rough table:

| Finding                                | Gold layer  | Silver layer | Bronze layer | Unknown layer |
|---|---|---|---|---|
| Missing owner                          | CRITICAL    | HIGH         | MEDIUM       | MEDIUM        |
| Missing schema with nullability        | HIGH        | HIGH         | MEDIUM       | HIGH          |
| Missing freshness SLA                  | HIGH        | MEDIUM       | LOW          | MEDIUM        |
| Implicit enum (closed set in code)     | MEDIUM      | MEDIUM       | LOW          | MEDIUM        |
| Implicit FK (join pattern present)     | MEDIUM      | MEDIUM       | LOW          | MEDIUM        |
| Dataframe with no code-defined schema  | HIGH        | HIGH         | MEDIUM       | HIGH          |
| Column name suggesting money/PII, no semantics | HIGH | MEDIUM      | LOW          | MEDIUM        |

When in doubt, err toward the higher severity and explain the calibration in one line under the finding. Users can downgrade.

## Composition with other skills

- **Downstream**: every finding's "Next" line is a `/draft-data-contract <dataset>` invocation. The audit's job is to surface the work; `/draft-data-contract` does the work.
- **Downstream of downstream**: once a contract exists, `/enforce-data-contract` emits validators and `/synth-from-contract` emits fixtures. The audit report includes a footer pointing at both as natural follow-ons.
- **Reference**: the `data-contract-core` skill documents the ODCS profile the audit measures against. Findings reference profile fields by name (e.g., "missing `info.owner`", "missing `quality.freshness_sla`") so the user can trace each gap back to the profile.

## Guidelines

- **Cite, don't assert.** Every finding needs `file:line` against the host repo. "This pipeline has no freshness SLA" without a citation is unactionable.
- **Be specific about the gap.** Don't say "needs a contract" — say "missing `info.owner` and `quality.uniqueness`; sibling `schema.yml` at `models/marts/transactions.yml` documents 6 of 8 columns but lacks `data_type`."
- **Implicit contracts are the gold of this audit.** When you find a closed enum, an FK pattern, a freshness filter in code — that's the highest-leverage finding because the contract values are *already in the codebase*. Draft is cheap; finding is the hard part.
- **Don't audit datasets the user already has contracts for.** Read the existing-contracts directory in Step 2 and exclude those datasets from the scans. The audit's job is the gap, not the inventory.
- **Don't recommend contracts the user can't act on.** If a dataset is upstream of the team (provided by another team or vendor), flag the gap but route the recommendation to "request a contract from <owner>" rather than `/draft-data-contract`. Drafting other teams' contracts unilaterally is rude and produces fiction.
- **The headline is the headline.** Lead with the layer-by-layer gap count and the top priorities. Don't bury them under finding tables.
- **Heuristics, not guarantees.** Static analysis misses dynamically-constructed schemas, schemas loaded from JSON at runtime, etc. The report should recommend a follow-up pass that runs the pipeline in a dry-run mode and dumps observed schemas for any code path the scan couldn't reach.
- **Plain text only. No emojis. No AI attribution.** Match the rest of the skills.
