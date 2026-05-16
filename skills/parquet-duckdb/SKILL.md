---
name: parquet-duckdb
description: Explore and query Parquet files on S3-compatible storage or local filesystem using the DuckDB CLI. Supports schema inspection, row sampling, column statistics, arbitrary SQL, and file listing.
---

# parquet-duckdb

Use the DuckDB CLI to investigate and query Parquet files — either on the local filesystem or S3-compatible block storage (AWS S3, MinIO, R2, etc.). Auth is handled entirely via environment variables.

## CLI

```bash
duckdb -c "<sql>"
```

For S3 sources, prepend the httpfs setup to every command (see Auth below).

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

No setup needed.

### AWS S3

```bash
duckdb -c "
INSTALL httpfs; LOAD httpfs;
SET s3_region='${AWS_DEFAULT_REGION:-us-east-1}';
SET s3_access_key_id='$AWS_ACCESS_KEY_ID';
SET s3_secret_access_key='$AWS_SECRET_ACCESS_KEY';
-- your query here
"
```

Include `SET s3_session_token='$AWS_SESSION_TOKEN';` when using temporary credentials.

### S3-compatible (MinIO, R2, etc.)

```bash
duckdb -c "
INSTALL httpfs; LOAD httpfs;
SET s3_region='us-east-1';
SET s3_access_key_id='$AWS_ACCESS_KEY_ID';
SET s3_secret_access_key='$AWS_SECRET_ACCESS_KEY';
SET s3_endpoint='your-endpoint-host:port';
SET s3_use_ssl=false;
SET s3_url_style='path';
-- your query here
"
```

Strip the `https://` or `http://` prefix from `AWS_ENDPOINT_URL` when setting `s3_endpoint`.

---

## Patterns

### Schema

```bash
duckdb -c "DESCRIBE SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true)"
```

### Sample

```bash
duckdb -c "SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true) LIMIT 20"
```

### Stats

```bash
duckdb -c "SUMMARIZE SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true)"
```

Returns per-column count, null percentage, min, max, mean, std, and quartiles.

### Arbitrary SQL

Register the source as a view named `data` then query freely:

```bash
duckdb -c "
CREATE VIEW data AS
  SELECT * FROM read_parquet('/data/events/**/*.parquet', union_by_name=true);
SELECT event_type, count(*) AS n FROM data GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
"
```

### List files

```bash
duckdb -c "SELECT * FROM glob('/data/events/**/*.parquet')"
```

---

## Guidelines

- Always run `DESCRIBE` first on an unfamiliar dataset — don't guess column names.
- Use `SUMMARIZE` to understand distributions before writing queries.
- `union_by_name=true` is safe for prefix paths with mixed schemas as long as column names and types are compatible.
- For partitioned datasets (e.g. `s3://bucket/events/year=2025/month=04/`), use the most specific prefix available to reduce scan cost.
- Chain multiple statements in a single `-c "..."` block — DuckDB runs them sequentially.
- For large result sets, always apply `LIMIT` or a `WHERE` clause rather than dumping everything to chat.
