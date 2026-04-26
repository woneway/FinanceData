"""Global test fixtures — disable DuckDB cache during tests.

monkeypatch finance_data.config.is_cache_enabled to return False, ensuring
mocked provider tests are not silently bypassed by a cache hit. This replaces
the historical FINANCE_DATA_CACHE=0 environment variable approach.
"""
import finance_data.config as _config

_config.is_cache_enabled = lambda: False
