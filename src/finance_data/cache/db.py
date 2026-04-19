"""DuckDB connection and bulk upsert helpers.

Tables are auto-created from the first DataFrame inserted. This avoids
schema drift when tushare adds new columns.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = _PROJECT_ROOT / "data" / "finance.duckdb"

_conn: Optional[duckdb.DuckDBPyConnection] = None


def get_db() -> duckdb.DuckDBPyConnection:
    """Return a shared DuckDB connection (lazy)."""
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(str(DB_PATH))
    return _conn


def upsert_df(
    table: str,
    df: pd.DataFrame,
    primary_key: tuple[str, ...],
) -> int:
    """Insert or replace rows from df into table.

    Creates the table from df's dtypes if it doesn't exist.
    Uses DELETE + INSERT for upsert (DuckDB has no native ON CONFLICT
    for composite PKs in all versions).

    Returns inserted row count.
    """
    if df is None or df.empty:
        return 0

    con = get_db()
    # Create table if missing
    existing = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchall()
    if not existing:
        cols_ddl = ", ".join(
            f'"{col}" {_pd_to_duckdb(df[col].dtype)}' for col in df.columns
        )
        con.execute(f"CREATE TABLE {table} ({cols_ddl})")
        logger.info("Created table %s with %d columns", table, len(df.columns))

    # Align columns: add missing columns to existing table
    existing_cols = {
        r[0] for r in con.execute(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = ?",
            [table],
        ).fetchall()
    }
    for col in df.columns:
        if col not in existing_cols:
            dtype = _pd_to_duckdb(df[col].dtype)
            con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")

    # Delete existing rows matching PKs, then insert
    if primary_key:
        pk_df = df[list(primary_key)].drop_duplicates()
        con.register("_pk_df", pk_df)
        where = " AND ".join(f"{table}.{k} = _pk_df.{k}" for k in primary_key)
        con.execute(
            f"DELETE FROM {table} USING _pk_df WHERE {where}"
        )
        con.unregister("_pk_df")

    con.register("_insert_df", df)
    # Align column order
    cols = ", ".join(df.columns)
    con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM _insert_df")
    con.unregister("_insert_df")
    return len(df)


def _pd_to_duckdb(dtype) -> str:
    s = str(dtype)
    if "int" in s:
        return "BIGINT"
    if "float" in s:
        return "DOUBLE"
    if "bool" in s:
        return "BOOLEAN"
    if "datetime" in s:
        return "TIMESTAMP"
    return "VARCHAR"


def query_df(
    table: str,
    *,
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    date_column: str = "trade_date",
    extra_where: str = "",
) -> pd.DataFrame | None:
    """Query cached data from DuckDB.

    Returns a pandas DataFrame (same format as tushare API output),
    or None if the table doesn't exist or no data matches.
    """
    con = get_db()
    try:
        con.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()
    except Exception:
        return None

    # Check table exists
    if not con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchall():
        return None

    conditions: list[str] = []
    if trade_date:
        conditions.append(f"{date_column} = '{trade_date}'")
    elif start_date and end_date:
        conditions.append(f"{date_column} >= '{start_date}'")
        conditions.append(f"{date_column} <= '{end_date}'")
    elif start_date:
        conditions.append(f"{date_column} >= '{start_date}'")
    elif end_date:
        conditions.append(f"{date_column} <= '{end_date}'")

    if extra_where:
        conditions.append(extra_where)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    try:
        df = con.execute(f"SELECT * FROM {table}{where}").fetchdf()
        return df if not df.empty else None
    except Exception:
        return None


def get_cache_date_range(
    table: str, date_column: str = "trade_date",
) -> tuple[str, str] | None:
    """Return (min_date, max_date) for a cached table, or None."""
    con = get_db()
    try:
        row = con.execute(
            f"SELECT MIN({date_column}), MAX({date_column}) FROM {table}"
        ).fetchone()
        if row and row[0] and row[1]:
            return (str(row[0]), str(row[1]))
    except Exception:
        pass
    return None


def get_cached_dates(
    table: str,
    start_date: str,
    end_date: str,
    date_column: str = "trade_date",
) -> set[str]:
    """Return the set of distinct dates cached in [start, end]."""
    con = get_db()
    try:
        rows = con.execute(
            f"SELECT DISTINCT {date_column} FROM {table} "
            f"WHERE {date_column} >= '{start_date}' AND {date_column} <= '{end_date}'"
        ).fetchall()
        return {str(r[0]) for r in rows}
    except Exception:
        return set()


def count_rows(table: str) -> int:
    con = get_db()
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except duckdb.CatalogException:
        return 0


def list_tables() -> list[tuple[str, int]]:
    """Return (table_name, row_count) for all tables."""
    con = get_db()
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()
    return [(t[0], count_rows(t[0])) for t in tables]
