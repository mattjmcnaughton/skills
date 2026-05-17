#!/usr/bin/env bash
set -euo pipefail

# Wrapper around duckdb that handles httpfs setup and S3/MinIO authentication.
# Credentials are passed via environment variables and never appear in the SQL.
#
# Usage: duckdb-parquet <backend> <sql>
#   backend: local | s3 | minio

usage() {
  echo "Usage: duckdb-parquet <backend> <sql>" >&2
  echo "  backend: local | s3 | minio" >&2
  exit 1
}

[[ $# -eq 2 ]] || usage

backend="$1"
sql="$2"

case "$backend" in
  local)
    duckdb -c "$sql"
    ;;
  s3)
    duckdb -c "
INSTALL httpfs; LOAD httpfs;
CREATE OR REPLACE SECRET s3_secret (
    TYPE s3,
    PROVIDER credential_chain
);
$sql
"
    ;;
  minio)
    : "${MINIO_ACCESS_KEY_ID:?MINIO_ACCESS_KEY_ID must be set}"
    : "${MINIO_SECRET_ACCESS_KEY:?MINIO_SECRET_ACCESS_KEY must be set}"
    : "${MINIO_ENDPOINT:?MINIO_ENDPOINT must be set}"

    AWS_ACCESS_KEY_ID="$MINIO_ACCESS_KEY_ID" \
    AWS_SECRET_ACCESS_KEY="$MINIO_SECRET_ACCESS_KEY" \
    duckdb -c "
INSTALL httpfs; LOAD httpfs;
CREATE OR REPLACE SECRET s3_secret (
    TYPE s3,
    PROVIDER credential_chain,
    CHAIN 'env',
    ENDPOINT '$MINIO_ENDPOINT',
    URL_STYLE 'path',
    USE_SSL false
);
$sql
"
    ;;
  *)
    echo "Unknown backend: $backend (expected local, s3, or minio)" >&2
    exit 1
    ;;
esac
