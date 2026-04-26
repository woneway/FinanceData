"""Cache-first resolver for tushare API calls.

Usage in tushare providers:

    from finance_data.cache.resolver import fetch_cached, resolve

    # Single-day query (trade_date)
    df = fetch_cached("daily_market", trade_date)
    if df is None:
        df = pro.daily(trade_date=trade_date)

    # trade_date or range (unified)
    df = resolve("stk_auction", trade_date, start_date, end_date)
    if df is None:
        df = pro.stk_auction(**kwargs)

    # With extra filters (e.g. limit_type, ts_code)
    df = resolve("limit_list_ths", trade_date, start_date, end_date,
                 extra_where=f"limit_type = '{limit_type}'")
    if df is None:
        df = pro.limit_list_ths(**kwargs)

Note: Do NOT use ``df = fetch_cached(...) or pro.xxx(...)`` —
pandas DataFrames do not support bool evaluation.
"""
from __future__ import annotations

import datetime
import logging
from typing import Optional

import pandas as pd

from finance_data.cache.db import get_cache_date_range, get_cached_dates, query_df

logger = logging.getLogger(__name__)

def _is_cache_enabled() -> bool:
    """Check if DuckDB cache is enabled. Disable with `[cache] enabled = false` in config.toml."""
    from finance_data.config import is_cache_enabled
    return is_cache_enabled()

# Today's date as YYYYMMDD — only cache T-1 and earlier.
_today: str = ""


def _get_today() -> str:
    global _today
    if not _today or _today != datetime.date.today().strftime("%Y%m%d"):
        _today = datetime.date.today().strftime("%Y%m%d")
    return _today


def fetch_cached(
    table: str,
    trade_date: str,
    *,
    date_column: str = "trade_date",
    extra_where: str = "",
) -> Optional[pd.DataFrame]:
    """Check DuckDB cache for a single trade_date.

    Returns the cached DataFrame (same format as tushare API), or None on miss.
    Skips cache for today's date (data may be incomplete intraday).
    """
    if not trade_date or not _is_cache_enabled():
        return None

    # T-1 rule: don't serve today's data from cache
    if trade_date >= _get_today():
        return None

    df = query_df(
        table,
        trade_date=trade_date,
        date_column=date_column,
        extra_where=extra_where,
    )
    if df is not None:
        logger.debug("Cache HIT: %s trade_date=%s (%d rows)", table, trade_date, len(df))
    return df


def fetch_cached_range(
    table: str,
    start_date: str,
    end_date: str,
    *,
    date_column: str = "trade_date",
    extra_where: str = "",
) -> Optional[pd.DataFrame]:
    """Check DuckDB cache for a date range.

    Returns cached DataFrame only if the range is FULLY covered by the cache.
    Uses all-or-nothing strategy: if any trading day is missing, returns None.

    Skips cache if end_date >= today.
    """
    if not start_date or not end_date or not _is_cache_enabled():
        return None

    # T-1 rule
    if end_date >= _get_today():
        return None

    # Check if the range falls within the cached date range
    cache_range = get_cache_date_range(table, date_column)
    if cache_range is None:
        return None

    cache_min, cache_max = cache_range
    if start_date < cache_min or end_date > cache_max:
        return None

    # Verify coverage: all weekdays in range should have data
    # (We use weekday heuristic; holidays without data are acceptable
    # since the original download also skips them.)
    expected_dates = _weekdays_between(start_date, end_date)
    cached_dates = get_cached_dates(table, start_date, end_date, date_column)

    # Allow up to 15% missing days (accounts for holidays)
    # but require at least some data
    if not cached_dates:
        return None

    missing = expected_dates - cached_dates
    # If too many expected weekdays have no data, likely incomplete cache
    if len(missing) > max(3, len(expected_dates) * 0.15):
        logger.debug(
            "Cache MISS (coverage): %s %s~%s, missing %d/%d days",
            table, start_date, end_date, len(missing), len(expected_dates),
        )
        return None

    df = query_df(
        table,
        start_date=start_date,
        end_date=end_date,
        date_column=date_column,
        extra_where=extra_where,
    )
    if df is not None:
        logger.debug(
            "Cache HIT: %s %s~%s (%d rows)",
            table, start_date, end_date, len(df),
        )
    return df


def resolve(
    table: str,
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    **kwargs,
) -> Optional[pd.DataFrame]:
    """Convenience wrapper: try single-day or range cache lookup.

    Usage in providers:
        df = resolve("stk_auction", trade_date, start_date, end_date) or pro.stk_auction(**kwargs)
    """
    if trade_date:
        return fetch_cached(table, trade_date, **kwargs)
    if start_date and end_date:
        return fetch_cached_range(table, start_date, end_date, **kwargs)
    return None


def _weekdays_between(start: str, end: str) -> set[str]:
    """Generate all weekday dates (Mon-Fri) between start and end (YYYYMMDD)."""
    dt = datetime.datetime.strptime(start[:8], "%Y%m%d")
    dt_end = datetime.datetime.strptime(end[:8], "%Y%m%d")
    result: set[str] = set()
    while dt <= dt_end:
        if dt.weekday() < 5:
            result.add(dt.strftime("%Y%m%d"))
        dt += datetime.timedelta(days=1)
    return result
