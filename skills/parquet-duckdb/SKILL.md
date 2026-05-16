---
name: parquet-duckdb
description: Explore and query Parquet files on S3-compatible storage or local filesystem using DuckDB. Supports schema inspection, row sampling, column statistics, arbitrary SQL, and file listing.
---

# parquet-duckdb

Use DuckDB to investigate and query Parquet files — either on the local filesystem or S3-compatible block storage (AWS S3, MinIO, R2, etc.). Auth is handled entirely via environment variables; no credential configuration is needed at invocation time.

## Script

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py <command> <uri> [options]
```

The script uses `uv` inline script dependencies — `duckdb` and `typer` are installed automatically on first run into a cached environment. No virtualenv setup required.

---

## URI formats

| Format | Description |
|---|---|
| `s3://bucket/prefix/` | S3-compatible prefix (glob applied automatically) |
| `s3://bucket/path/file.parquet` | Single S3 file |
| `/local/path/to/dir/` | Local directory (glob applied recursively) |
| `/local/path/file.parquet` | Single local file |

When a URI does not end in `.parquet`, the script appends `/**/*.parquet` to match all Parquet files under that prefix/directory.

---

## Auth

### AWS S3

Set standard AWS environment variables:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION       (defaults to us-east-1)
AWS_SESSION_TOKEN        (optional, for temporary credentials)
```

### S3-compatible (MinIO, R2, etc.)

In addition to the key/secret above, set:

```
AWS_ENDPOINT_URL         (e.g. http://localhost:9000 or https://s3.example.com)
```

`S3_ENDPOINT_URL` is also accepted as a fallback. Path-style URL addressing is enabled automatically when an endpoint override is present.

---

## Commands

### schema

Show column names and types.

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py schema s3://my-bucket/events/
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py schema /data/local/events/
```

Output: markdown table of `column_name`, `column_type`, nullability.

---

### sample

Show the first N rows (default: 20).

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py sample s3://my-bucket/events/
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py sample s3://my-bucket/events/ --limit 50
```

Output: markdown table of rows.

---

### stats

Show per-column statistics: count, null percentage, min, max, mean, standard deviation, quartiles.

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py stats s3://my-bucket/events/
```

Uses DuckDB's `SUMMARIZE` under the hood. Works on all column types; numeric columns get full statistics, others get count/null/distinct.

---

### query

Run arbitrary SQL against the dataset. The Parquet source is registered as a view named `data`.

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py query s3://my-bucket/events/ \
  --sql "SELECT event_type, count(*) AS n FROM data GROUP BY 1 ORDER BY 2 DESC"

uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py query s3://my-bucket/events/ \
  --sql "SELECT * FROM data WHERE user_id = 'abc123'" \
  --limit 10
```

Use `data` as the table name in all queries. `--limit N` appends `LIMIT N` to the query (useful for exploration without modifying the SQL).

Output: markdown table of results. Truncated to 100 rows by default; use `--limit` or a `WHERE` clause to narrow.

---

### ls

List Parquet files found at a URI prefix.

```bash
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py ls s3://my-bucket/events/
uv run ~/code/skills/skills/parquet-duckdb/parquet_duckdb.py ls /data/local/
```

Output: plain list of file paths.

---

## Guidelines for agents

- Always run `schema` first when encountering an unfamiliar dataset — don't guess column names.
- Use `stats` to understand data distributions before writing queries.
- Use `union_by_name=true` behavior (built in) — safe to query prefix paths with mixed schemas as long as columns share names and compatible types.
- Output goes directly to chat. For large result sets, apply `--limit` or filter with `WHERE` rather than dumping everything.
- When querying partitioned datasets (e.g. `s3://bucket/events/year=2025/month=04/`), pass the most specific prefix available to reduce scan cost.
- Cell values are truncated to 200 characters in output. If you suspect truncation is hiding important data, use a targeted `query` to SELECT the specific column.
