"""Health probe logic for dashboard"""
import datetime
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Generator, List, Optional, Tuple

from finance_data.dashboard.models import HealthResult
from finance_data.provider.metadata.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT = 30  # seconds


def _get_available_providers() -> Dict[str, bool]:
    """Check which providers are available"""
    has_tushare = bool(os.getenv("TUSHARE_TOKEN"))
    try:
        from finance_data.provider.xueqiu.client import has_login_cookie
        has_xueqiu = has_login_cookie()
    except Exception:
        has_xueqiu = False
    return {
        "akshare": True,
        "tushare": has_tushare,
        "xueqiu": has_xueqiu,
    }


# Per-tool provider mapping: tool_name -> {provider_name: (class_path, method_name)}
# Generated from actual service dispatcher introspection.
_TOOL_PROVIDERS: Dict[str, Dict[str, Tuple[str, str]]] = {
    "tool_get_stock_info_history": {
        "akshare": ("finance_data.provider.akshare.stock.history:AkshareStockHistory", "get_stock_info_history"),
        "tushare": ("finance_data.provider.tushare.stock.history:TushareStockHistory", "get_stock_info_history"),
    },
    "tool_get_kline_history": {
        "akshare": ("finance_data.provider.akshare.kline.history:AkshareKlineHistory", "get_kline_history"),
        "tushare": ("finance_data.provider.tushare.kline.history:TushareKlineHistory", "get_kline_history"),
        "xueqiu": ("finance_data.provider.xueqiu.kline.history:XueqiuKlineHistory", "get_kline_history"),
    },
    "tool_get_realtime_quote": {
        "akshare": ("finance_data.provider.akshare.realtime.realtime:AkshareRealtimeQuote", "get_realtime_quote"),
        "tushare": ("finance_data.provider.tushare.realtime.realtime:TushareRealtimeQuote", "get_realtime_quote"),
        "xueqiu": ("finance_data.provider.xueqiu.realtime.realtime:XueqiuRealtimeQuote", "get_realtime_quote"),
    },
    "tool_get_index_quote_realtime": {
        "akshare": ("finance_data.provider.akshare.index.realtime:AkshareIndexQuote", "get_index_quote_realtime"),
        "tushare": ("finance_data.provider.tushare.index.realtime:TushareIndexQuote", "get_index_quote_realtime"),
        "xueqiu": ("finance_data.provider.xueqiu.index.realtime:XueqiuIndexQuote", "get_index_quote_realtime"),
    },
    "tool_get_index_history": {
        "akshare": ("finance_data.provider.akshare.index.history:AkshareIndexHistory", "get_index_history"),
        "tushare": ("finance_data.provider.tushare.index.history:TushareIndexHistory", "get_index_history"),
        "xueqiu": ("finance_data.provider.xueqiu.index.history:XueqiuIndexHistory", "get_index_history"),
    },
    "tool_get_sector_rank_realtime": {
        "akshare": ("finance_data.provider.akshare.sector.realtime:AkshareSectorRank", "get_sector_rank_realtime"),
    },
    "tool_get_chip_distribution_history": {
        "akshare": ("finance_data.provider.akshare.chip.history:AkshareChipHistory", "get_chip_distribution_history"),
        "tushare": ("finance_data.provider.tushare.chip.history:TushareChipHistory", "get_chip_distribution_history"),
    },
    "tool_get_financial_summary_history": {
        "akshare": ("finance_data.provider.akshare.fundamental.history:AkshareFinancialSummary", "get_financial_summary_history"),
        "tushare": ("finance_data.provider.tushare.fundamental.history:TushareFinancialSummary", "get_financial_summary_history"),
    },
    "tool_get_dividend_history": {
        "akshare": ("finance_data.provider.akshare.fundamental.history:AkshareDividend", "get_dividend_history"),
        "tushare": ("finance_data.provider.tushare.fundamental.history:TushareDividend", "get_dividend_history"),
    },
    "tool_get_earnings_forecast_history": {
        "akshare": ("finance_data.provider.akshare.fundamental.history:AkshareEarningsForecast", "get_earnings_forecast_history"),
    },
    "tool_get_stock_capital_flow_realtime": {
        "akshare": ("finance_data.provider.akshare.cashflow.realtime:AkshareStockCapitalFlow", "get_stock_capital_flow_realtime"),
    },
    "tool_get_trade_calendar_history": {
        "tushare": ("finance_data.provider.tushare.calendar.history:TushareTradeCalendar", "get_trade_calendar_history"),
        "akshare": ("finance_data.provider.akshare.calendar.history:AkshareTradeCalendar", "get_trade_calendar_history"),
    },
    "tool_get_lhb_detail": {
        "akshare": ("finance_data.provider.akshare.lhb.history:AkshareLhbDetail", "get_lhb_detail_history"),
        "tushare": ("finance_data.provider.tushare.lhb.history:TushareLhbDetail", "get_lhb_detail_history"),
    },
    "tool_get_lhb_stock_stat": {
        "akshare": ("finance_data.provider.akshare.lhb.history:AkshareLhbStockStat", "get_lhb_stock_stat_history"),
    },
    "tool_get_lhb_active_traders": {
        "akshare": ("finance_data.provider.akshare.lhb.history:AkshareLhbActiveTraders", "get_lhb_active_traders_history"),
    },
    "tool_get_lhb_trader_stat": {
        "akshare": ("finance_data.provider.akshare.lhb.history:AkshareLhbTraderStat", "get_lhb_trader_stat_history"),
    },
    "tool_get_lhb_stock_detail": {
        "akshare": ("finance_data.provider.akshare.lhb.history:AkshareLhbStockDetail", "get_lhb_stock_detail_history"),
    },
    "tool_get_zt_pool": {
        "akshare": ("finance_data.provider.akshare.pool.history:AkshareZtPool", "get_zt_pool_history"),
    },
    "tool_get_strong_stocks": {
        "akshare": ("finance_data.provider.akshare.pool.history:AkshareStrongStocks", "get_strong_stocks_history"),
    },
    "tool_get_previous_zt": {
        "akshare": ("finance_data.provider.akshare.pool.history:AksharePreviousZt", "get_previous_zt_history"),
    },
    "tool_get_zbgc_pool": {
        "akshare": ("finance_data.provider.akshare.pool.history:AkshareZbgcPool", "get_zbgc_pool_history"),
    },
    "tool_get_north_stock_hold": {
        "akshare": ("finance_data.provider.akshare.north_flow.history:AkshareNorthStockHold", "get_north_stock_hold_history"),
        "tushare": ("finance_data.provider.tushare.north_flow.history:TushareNorthStockHold", "get_north_stock_hold_history"),
    },
    "tool_get_margin": {
        "tushare": ("finance_data.provider.tushare.margin.history:TushareMargin", "get_margin_history"),
        "akshare": ("finance_data.provider.akshare.margin.history:AkshareMargin", "get_margin_history"),
    },
    "tool_get_margin_detail": {
        "tushare": ("finance_data.provider.tushare.margin.history:TushareMarginDetail", "get_margin_detail_history"),
        "akshare": ("finance_data.provider.akshare.margin.history:AkshareMarginDetail", "get_margin_detail_history"),
    },
    "tool_get_market_stats_realtime": {
        "akshare": ("finance_data.provider.akshare.market.realtime:AkshareMarketRealtime", "get_market_stats_realtime"),
    },
    "tool_get_market_north_capital": {
        "akshare": ("finance_data.provider.akshare.north_flow.history:AkshareNorthFlow", "get_north_flow_history"),
    },
    "tool_get_sector_capital_flow": {
        "akshare": ("finance_data.provider.akshare.sector_fund_flow.history:AkshareSectorCapitalFlow", "get_sector_capital_flow_history"),
    },
}


def _import_class(dotted_path: str):
    """Import a class from 'module.path:ClassName'"""
    module_path, class_name = dotted_path.rsplit(":", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_test_params(tool_name: str) -> dict:
    """Return test parameters for a given tool"""
    today = datetime.date.today().strftime("%Y%m%d")
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y%m%d")
    month_ago = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y%m%d")

    params_map = {
        "tool_get_stock_info_history": {"symbol": "000001"},
        "tool_get_kline_history": {
            "symbol": "000001", "period": "daily",
            "start": month_ago, "end": today, "adj": "qfq",
        },
        "tool_get_realtime_quote": {"symbol": "000001"},
        "tool_get_index_quote_realtime": {"symbol": "000001.SH"},
        "tool_get_index_history": {
            "symbol": "000001.SH", "start": month_ago, "end": today,
        },
        "tool_get_sector_rank_realtime": {},
        "tool_get_chip_distribution_history": {"symbol": "000001"},
        "tool_get_financial_summary_history": {"symbol": "000001"},
        "tool_get_dividend_history": {"symbol": "000001"},
        "tool_get_earnings_forecast_history": {"symbol": "000001"},
        "tool_get_stock_capital_flow_realtime": {"symbol": "000001"},
        "tool_get_trade_calendar_history": {"start": month_ago, "end": today},
        "tool_get_lhb_detail": {"start_date": week_ago, "end_date": yesterday},
        "tool_get_lhb_stock_stat": {"period": "近一月"},
        "tool_get_lhb_active_traders": {"start_date": week_ago, "end_date": yesterday},
        "tool_get_lhb_trader_stat": {"period": "近一月"},
        "tool_get_lhb_stock_detail": {
            "symbol": "600077", "date": yesterday, "flag": "买入",
        },
        "tool_get_zt_pool": {"date": yesterday},
        "tool_get_strong_stocks": {"date": yesterday},
        "tool_get_previous_zt": {"date": yesterday},
        "tool_get_zbgc_pool": {"date": yesterday},
        "tool_get_north_stock_hold": {
            "market": "沪股通", "indicator": "5日排行",
        },
        "tool_get_margin": {"trade_date": yesterday},
        "tool_get_margin_detail": {"trade_date": yesterday},
        "tool_get_market_stats_realtime": {},
        "tool_get_market_north_capital": {},
        "tool_get_sector_capital_flow": {
            "indicator": "今日", "sector_type": "行业资金流",
        },
    }
    return params_map.get(tool_name, {})


def get_providers_for_tool(tool_name: str) -> List[Tuple[str, str, str]]:
    """Return (provider_name, class_path, method_name) tuples for a tool.

    Only includes providers whose credentials are available.
    """
    tool_providers = _TOOL_PROVIDERS.get(tool_name, {})
    if not tool_providers:
        return []

    available = _get_available_providers()
    results = []
    for provider_name, (class_path, method_name) in tool_providers.items():
        if available.get(provider_name, False):
            results.append((provider_name, class_path, method_name))
    return results


def _run_single_probe(
    tool_name: str,
    provider_name: str,
    class_path: str,
    method_name: str,
) -> HealthResult:
    """Execute a single probe"""
    params = _get_test_params(tool_name)

    try:
        cls = _import_class(class_path)
        instance = cls()
        method = getattr(instance, method_name)
        start = time.monotonic()
        result = method(**params)
        elapsed = (time.monotonic() - start) * 1000
        record_count = len(result.data) if hasattr(result, "data") else 0
        return HealthResult(
            tool=tool_name,
            provider=provider_name,
            status="ok",
            response_time_ms=round(elapsed, 1),
            record_count=record_count,
        )
    except Exception as e:
        elapsed = 0.0
        status = "timeout" if "timeout" in str(e).lower() else "error"
        return HealthResult(
            tool=tool_name,
            provider=provider_name,
            status=status,
            response_time_ms=round(elapsed, 1),
            error=str(e)[:200],
        )


def run_probes(
    tool_name: Optional[str] = None,
) -> Generator[HealthResult, None, None]:
    """Run health probes and yield results as they complete.

    Args:
        tool_name: If given, only probe this specific tool. Otherwise probe all.
    """
    tasks: List[Tuple[str, str, str, str]] = []

    if tool_name:
        tools = {tool_name: TOOL_REGISTRY[tool_name]} if tool_name in TOOL_REGISTRY else {}
    else:
        tools = TOOL_REGISTRY

    for tname in tools:
        for provider_name, class_path, method_name in get_providers_for_tool(tname):
            tasks.append((tname, provider_name, class_path, method_name))

    if not tasks:
        return

    with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as pool:
        futures = {
            pool.submit(_run_single_probe, t, p, c, m): (t, p)
            for t, p, c, m in tasks
        }
        for future in as_completed(futures):
            yield future.result()
