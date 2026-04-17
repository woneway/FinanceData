"""Bulk download past N months of tushare historical data into DuckDB.

Usage:
    python scripts/download_all.py --months 3
    python scripts/download_all.py --months 3 --only daily,daily_basic
    python scripts/download_all.py --months 3 --start 20260101 --end 20260410

Failure policy: log-and-skip. Failed (table, date) tuples are written to
data/download_failures.jsonl for later retry.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from finance_data.cache.db import count_rows, get_db, upsert_df, DB_PATH
from finance_data.provider.tushare.client import get_pro

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("download")

FAILURE_LOG = DB_PATH.parent / "download_failures.jsonl"


# ------------------------------------------------------------------
# Interface registry: (table, pull_type, fetcher, primary_key)
# pull_type: "per_date_full" | "per_date_with_tag" | "range_once" | "snapshot"
# ------------------------------------------------------------------

def _fetch_per_date(api_name: str, **extra):
    """Build a fetcher that calls pro.<api>(trade_date=date, **extra)."""
    def fetcher(date: str):
        pro = get_pro()
        fn = getattr(pro, api_name)
        return fn(trade_date=date, **extra)
    fetcher.__name__ = f"fetch_{api_name}"
    return fetcher


_LIMIT_LIST_THS_STR_COLS = [
    "lu_desc", "tag", "status", "first_lu_time", "last_lu_time",
    "first_ld_time", "last_ld_time",
]


def _fetch_limit_list_ths(date: str):
    """Pull all 5 limit types into one table."""
    import pandas as pd
    pro = get_pro()
    parts = []
    for lt in ("涨停池", "连扳池", "炸板池", "跌停池", "冲刺涨停"):
        df = pro.limit_list_ths(trade_date=date, limit_type=lt)
        if df is not None and not df.empty:
            df = df.copy()
            df["limit_type"] = lt
            parts.append(df)
        time.sleep(0.5)
    if not parts:
        return None
    result = pd.concat(parts, ignore_index=True)
    for col in _LIMIT_LIST_THS_STR_COLS:
        if col in result.columns:
            result[col] = result[col].astype(str).replace("nan", "")
    return result


_KPL_LIST_STR_COLS = [
    "lu_time", "ld_time", "open_time", "last_time", "lu_desc", "status",
]


def _fetch_kpl_list(date: str):
    """Pull all 5 kpl tags."""
    import pandas as pd
    pro = get_pro()
    parts = []
    for tag in ("涨停", "跌停", "炸板", "自然涨停", "竞价"):
        df = pro.kpl_list(trade_date=date, tag=tag)
        if df is not None and not df.empty:
            df = df.copy()
            df["tag"] = tag
            parts.append(df)
        time.sleep(0.5)
    if not parts:
        return None
    result = pd.concat(parts, ignore_index=True)
    for col in _KPL_LIST_STR_COLS:
        if col in result.columns:
            result[col] = result[col].astype(str).replace("nan", "")
    return result


PER_DATE_INTERFACES: dict[str, tuple[Callable, tuple[str, ...]]] = {
    # table_name: (fetcher, primary_key_cols)
    "daily_market": (_fetch_per_date("daily"), ("ts_code", "trade_date")),
    "daily_basic_market": (_fetch_per_date("daily_basic"), ("ts_code", "trade_date")),
    "stk_limit": (_fetch_per_date("stk_limit"), ("ts_code", "trade_date")),
    "stk_auction": (_fetch_per_date("stk_auction"), ("ts_code", "trade_date")),
    "stk_auction_close": (_fetch_per_date("stk_auction_c"), ("ts_code", "trade_date")),
    "lhb_detail": (_fetch_per_date("top_list"), ("ts_code", "trade_date")),
    "limit_list_ths": (_fetch_limit_list_ths, ("ts_code", "trade_date", "limit_type")),
    "kpl_list": (_fetch_kpl_list, ("ts_code", "trade_date", "tag")),
    "limit_step": (_fetch_per_date("limit_step"), ("ts_code", "trade_date")),
    "hm_detail": (_fetch_per_date("hm_detail"), ("ts_code", "trade_date", "hm_name")),
    "stk_factor_pro": (_fetch_per_date("stk_factor_pro"), ("ts_code", "trade_date")),
    "dc_board_moneyflow": (_fetch_per_date("moneyflow_ind_dc"), ("ts_code", "trade_date", "content_type")),
    "dc_market_moneyflow": (_fetch_per_date("moneyflow_mkt_dc"), ("trade_date",)),
    "ths_hot": (_fetch_per_date("ths_hot"), ("ts_code", "trade_date")),
    "cyq_perf": (_fetch_per_date("cyq_perf"), ("ts_code", "trade_date")),
    "margin": (_fetch_per_date("margin"), ("exchange_id", "trade_date")),
    "margin_detail": (_fetch_per_date("margin_detail"), ("ts_code", "trade_date")),
}


# ------------------------------------------------------------------
# Trading day helpers
# ------------------------------------------------------------------

def get_trading_days(start: str, end: str) -> list[str]:
    """Use tushare trade_cal to list trading days in [start, end]."""
    pro = get_pro()
    df = pro.trade_cal(exchange="SSE", start_date=start, end_date=end, is_open=1)
    return sorted(df["cal_date"].tolist())


# ------------------------------------------------------------------
# Main download loop
# ------------------------------------------------------------------

def log_failure(table: str, date: str, error: str) -> None:
    with FAILURE_LOG.open("a") as f:
        f.write(json.dumps({
            "ts": datetime.now().isoformat(),
            "table": table, "date": date, "error": error[:200],
        }, ensure_ascii=False) + "\n")


def download_per_date(
    table: str,
    fetcher: Callable,
    primary_key: tuple[str, ...],
    trading_days: list[str],
    rate_limit_per_min: int = 400,
) -> tuple[int, int]:
    """Download one interface for all trading days.

    Returns (success_count, fail_count).
    """
    min_interval = 60.0 / rate_limit_per_min
    success = 0
    fail = 0
    total_rows = 0
    total = len(trading_days)

    for i, date in enumerate(trading_days, 1):
        t0 = time.monotonic()
        try:
            df = fetcher(date)
            if df is None or df.empty:
                logger.debug("[%s] %s: empty", table, date)
                success += 1
            else:
                n = upsert_df(table, df, primary_key)
                total_rows += n
                success += 1
                if i % 10 == 0 or i == total:
                    logger.info(
                        "[%s] %d/%d days, +%d rows (last: %s)",
                        table, i, total, total_rows, date,
                    )
        except Exception as e:
            fail += 1
            err_msg = str(e)
            log_failure(table, date, err_msg)
            logger.warning("[%s] %s FAILED: %s", table, date, err_msg[:100])
        # Rate limiting
        elapsed = time.monotonic() - t0
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    return success, fail


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=3,
                        help="Months of history to pull (default 3)")
    parser.add_argument("--start", type=str, help="Override start date YYYYMMDD")
    parser.add_argument("--end", type=str, help="Override end date YYYYMMDD")
    parser.add_argument("--only", type=str,
                        help="Comma-separated table names (default: all)")
    parser.add_argument("--rate", type=int, default=400,
                        help="Max API calls per minute (default 400)")
    args = parser.parse_args()

    # Resolve date range
    end = args.end or datetime.now().strftime("%Y%m%d")
    if args.start:
        start = args.start
    else:
        start_dt = datetime.strptime(end, "%Y%m%d") - timedelta(days=args.months * 31)
        start = start_dt.strftime("%Y%m%d")

    logger.info("Target range: %s → %s", start, end)
    logger.info("DuckDB path: %s", DB_PATH)

    # Resolve which tables to pull
    selected = set(args.only.split(",")) if args.only else None
    if selected:
        targets = {k: v for k, v in PER_DATE_INTERFACES.items() if k in selected}
        missing = selected - set(targets)
        if missing:
            logger.error("Unknown tables: %s", missing)
            return 2
    else:
        targets = PER_DATE_INTERFACES

    # Fetch trading days
    logger.info("Fetching trading calendar...")
    trading_days = get_trading_days(start, end)
    logger.info("Found %d trading days in range", len(trading_days))

    # Download each interface
    summary = []
    for table, (fetcher, pk) in targets.items():
        logger.info("=== %s (pk=%s) ===", table, pk)
        t0 = time.monotonic()
        ok, fail = download_per_date(table, fetcher, pk, trading_days, args.rate)
        elapsed = time.monotonic() - t0
        rows = count_rows(table)
        summary.append((table, ok, fail, rows, elapsed))
        logger.info(
            "[%s] done: ok=%d fail=%d rows=%d in %.1fs",
            table, ok, fail, rows, elapsed,
        )

    # Summary
    print("\n" + "=" * 80)
    print(f"{'Table':<28} {'OK':>6} {'Fail':>6} {'Rows':>12} {'Time':>10}")
    print("-" * 80)
    total_fail = 0
    for table, ok, fail, rows, elapsed in summary:
        total_fail += fail
        print(f"{table:<28} {ok:>6} {fail:>6} {rows:>12,} {elapsed:>8.1f}s")
    print("=" * 80)
    if total_fail:
        print(f"⚠ {total_fail} failures logged to {FAILURE_LOG}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
