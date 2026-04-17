"""Local DuckDB cache for historical finance data."""
from finance_data.cache.db import get_db, DB_PATH

__all__ = ["get_db", "DB_PATH"]
