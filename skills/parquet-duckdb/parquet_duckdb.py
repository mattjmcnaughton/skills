#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["duckdb>=1.0", "typer>=0.12"]
# ///
"""parquet-duckdb: explore and query Parquet files on S3-compatible storage or local filesystem."""

import os
import sys
from typing import Optional

import duckdb
import typer

app = typer.Typer(no_args_is_help=True, help="Explore and query Parquet files with DuckDB.")

ROW_LIMIT = 100
CELL_MAX = 200


def _build_con(uri: str) -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection configured for the given URI."""
    con = duckdb.connect()

    if uri.startswith("s3://") or uri.startswith("s3a://"):
        con.execute("INSTALL httpfs; LOAD httpfs;")

        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        con.execute(f"SET s3_region='{region}';")

        key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        if key:
            con.execute(f"SET s3_access_key_id='{key}';")
        if secret:
            con.execute(f"SET s3_secret_access_key='{secret}';")

        token = os.environ.get("AWS_SESSION_TOKEN", "")
        if token:
            con.execute(f"SET s3_session_token='{token}';")

        # S3-compatible endpoint (MinIO, R2, etc.)
        endpoint = os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL", "")
        if endpoint:
            ep = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
            con.execute(f"SET s3_endpoint='{ep}';")
            use_ssl = not any(ep.startswith(h) for h in ("localhost", "127.", "0.0.0.0"))
            con.execute(f"SET s3_use_ssl={'true' if use_ssl else 'false'};")
            con.execute("SET s3_url_style='path';")

    return con


def _to_glob(uri: str) -> str:
    """Convert a URI to a glob pattern for read_parquet."""
    if uri.endswith(".parquet"):
        return uri
    return uri.rstrip("/") + "/**/*.parquet"


def _md_table(columns: list[str], rows: list) -> str:
    """Format query results as a markdown table."""
    if not rows:
        return "(no rows returned)"

    str_rows = [
        [str(v)[:CELL_MAX] if v is not None else "NULL" for v in row]
        for row in rows[:ROW_LIMIT]
    ]

    widths = [
        max(len(col), max((len(r[i]) for r in str_rows), default=0))
        for i, col in enumerate(columns)
    ]

    def fmt_row(r: list[str]) -> str:
        return "| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(r)) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [fmt_row(columns), sep] + [fmt_row(r) for r in str_rows]

    if len(rows) > ROW_LIMIT:
        lines.append(f"\n_(showing {ROW_LIMIT} of {len(rows)} rows — use --limit or a WHERE clause to narrow)_")

    return "\n".join(lines)


@app.command()
def schema(
    uri: str = typer.Argument(..., help="Parquet file, directory, or s3:// URI"),
):
    """Show column names and types."""
    con = _build_con(uri)
    glob = _to_glob(uri)
    try:
        rel = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob}', union_by_name=true)")
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
        print(f"Schema: {uri}\n")
        print(_md_table(cols, rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command()
def sample(
    uri: str = typer.Argument(..., help="Parquet file, directory, or s3:// URI"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of rows to return"),
):
    """Show the first N rows."""
    con = _build_con(uri)
    glob = _to_glob(uri)
    try:
        rel = con.execute(
            f"SELECT * FROM read_parquet('{glob}', union_by_name=true) LIMIT {limit}"
        )
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
        print(f"Sample ({limit} rows): {uri}\n")
        print(_md_table(cols, rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command()
def stats(
    uri: str = typer.Argument(..., help="Parquet file, directory, or s3:// URI"),
):
    """Show per-column statistics: count, nulls, min, max, mean, quartiles."""
    con = _build_con(uri)
    glob = _to_glob(uri)
    try:
        rel = con.execute(
            f"SUMMARIZE SELECT * FROM read_parquet('{glob}', union_by_name=true)"
        )
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
        print(f"Stats: {uri}\n")
        print(_md_table(cols, rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command()
def query(
    uri: str = typer.Argument(..., help="Parquet file, directory, or s3:// URI"),
    sql: str = typer.Option(..., "--sql", "-q", help="SQL to run; use 'data' as the table name"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Append LIMIT N to query"),
):
    """Run arbitrary SQL. The parquet source is available as table 'data'."""
    con = _build_con(uri)
    glob = _to_glob(uri)
    try:
        con.execute(
            f"CREATE VIEW data AS SELECT * FROM read_parquet('{glob}', union_by_name=true);"
        )
        full_sql = f"{sql.rstrip(';')} LIMIT {limit}" if limit else sql
        rel = con.execute(full_sql)
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
        print(f"Query: {uri}\n  {sql}\n")
        print(_md_table(cols, rows))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command()
def ls(
    uri: str = typer.Argument(..., help="S3 prefix or local directory to list"),
):
    """List Parquet files at a URI prefix."""
    con = _build_con(uri)
    glob_pattern = _to_glob(uri)
    try:
        rel = con.execute(f"SELECT * FROM glob('{glob_pattern}')")
        files = [r[0] for r in rel.fetchall()]
        if not files:
            print(f"No Parquet files found at: {uri}")
        else:
            print(f"{len(files)} Parquet file(s) at {uri}:\n")
            for f in files:
                print(f"  {f}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    app()
