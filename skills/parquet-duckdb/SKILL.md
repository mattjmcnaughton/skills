---
name: parquet-duckdb
description: Explore and query Parquet files on S3-compatible storage or local filesystem using the DuckDB CLI. Supports schema inspection, row sampling, column statistics, arbitrary SQL, and file listing.
---

# parquet-duckdb

Use the DuckDB CLI to investigate and query Parquet files — either on the local filesystem or S3-compatible block storage (AWS S3, MinIO, R2, etc.).

## CLI

Use the `duckdb-parquet` wrapper script. It handles httpfs installation, secret creation, and credential management so that credentials never appear in SQL strings.

```bash
./skills/parquet-duckdb/duckdb-parquet.sh <backend> "<sql>"
```

| Backend | Description | Required env vars |
|---|---|---|
| `local` | Local filesystem — no auth needed | — |
| `s3` | AWS S3 — uses credential chain (env vars, config files, SSO, instance metadata) | Standard AWS credentials |
| `minio` | MinIO or S3-compatible storage | `MINIO_ACCESS_KEY_ID`, `MINIO_SECRET_ACCESS_KEY`, `MINIO_ENDPOINT` |

---

## URI formats

| Format | Description |
|---|---|
| `s3://bucket/prefix/**/*.parquet` | S3 prefix glob |
| `s3://bucket/path/file.parquet` | Single S3 file |
| `/local/path/to/dir/**/*.parquet` | Local directory glob |
| `/local/path/file.parquet` | Single local file |

---

## Auth

### Local filesystem

No setup needed — use the `local` backend.

### AWS S3

Uses DuckDB's `credential_chain` provider, which automatically resolves credentials from environment variables, `~/.aws/credentials`, SSO, STS, or EC2 instance metadata. No secrets appear in the SQL.

```bash
./skills/parquet-duckdb/duckdb-parquet.sh s3 "SELECT * FROM 's3://bucket/file.parquet'"
```

### MinIO / S3-compatible

Requires `MINIO_ACCESS_KEY_ID`, `MINIO_SECRET_ACCESS_KEY`, and `MINIO_ENDPOINT` (host:port, no scheme). The wrapper maps these to AWS env vars for the process and uses `credential_chain` with `CHAIN 'env'`, so credentials never appear in the SQL string.

```bash
export MINIO_ACCESS_KEY_ID='...'
export MINIO_SECRET_ACCESS_KEY='...'
export MINIO_ENDPOINT='minio.example.com:9000'

./skills/parquet-duckdb/duckdb-parquet.sh minio "SELECT * FROM 's3://bucket/file.parquet'"
```

`MINIO_ENDPOINT` should be host:port without the `http://` or `https://` prefix.

---

## Patterns

### Schema

```bash
./skills/parquet-duckdb/duckdb-parquet.sh local "DESCRIBE SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true)"
```

### Sample

```bash
./skills/parquet-duckdb/duckdb-parquet.sh local "SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true) LIMIT 20"
```

### Stats

```bash
./skills/parquet-duckdb/duckdb-parquet.sh local "SUMMARIZE SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true)"
```

Returns per-column count, null percentage, min, max, mean, std, and quartiles.

### Arbitrary SQL

Register the source as a view named `data` then query freely:

```bash
./skills/parquet-duckdb/duckdb-parquet.sh minio "
CREATE VIEW data AS
  SELECT * FROM read_parquet('s3://bucket/events/**/*.parquet', union_by_name=true);
SELECT event_type, count(*) AS n FROM data GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
"
```

### List files

```bash
./skills/parquet-duckdb/duckdb-parquet.sh local "SELECT * FROM glob('/data/events/**/*.parquet')"
```

---

## Guidelines

- Always run `DESCRIBE` first on an unfamiliar dataset — don't guess column names.
- Use `SUMMARIZE` to understand distributions before writing queries.
- `union_by_name=true` is safe for prefix paths with mixed schemas as long as column names and types are compatible.
- For partitioned datasets (e.g. `s3://bucket/events/year=2025/month=04/`), use the most specific prefix available to reduce scan cost.
- Chain multiple statements in a single `-c "..."` block — DuckDB runs them sequentially.
- For large result sets, always apply `LIMIT` or a `WHERE` clause rather than dumping everything to chat.
