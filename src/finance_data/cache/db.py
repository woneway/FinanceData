"""DuckDB connection and bulk upsert helpers.

Tables are auto-created from the first DataFrame inserted. This avoids
schema drift when tushare adds new columns.
"""
from __future__ import annotations

import logging
import os
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
        con.register("_tmp_init", df.head(0))
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM _tmp_init")
        con.unregister("_tmp_init")
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
