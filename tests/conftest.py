"""Global test fixtures — disable DuckDB cache during tests."""
import os

os.environ["FINANCE_DATA_CACHE"] = "0"
