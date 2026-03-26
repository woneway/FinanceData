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

# Map tool -> list of (provider_name, callable_factory)
# callable_factory returns a function that executes the probe
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


# Provider class locations for each domain
_PROVIDER_MAP: Dict[str, Dict[str, str]] = {
    "stock": {
        "akshare": "finance_data.provider.akshare.stock.history:AkshareStockHistory",
        "tushare": "finance_data.provider.tushare.stock.history:TushareStockHistory",
    },
    "kline": {
        "akshare": "finance_data.provider.akshare.kline.history:AkshareKlineHistory",
        "tushare": "finance_data.provider.tushare.kline.history:TushareKlineHistory",
        "xueqiu": "finance_data.provider.xueqiu.kline.history:XueqiuKlineHistory",
    },
    "realtime": {
        "akshare": "finance_data.provider.akshare.realtime.realtime:AkshareRealtimeQuote",
        "tushare": "finance_data.provider.tushare.realtime.realtime:TushareRealtimeQuote",
        "xueqiu": "finance_data.provider.xueqiu.realtime.realtime:XueqiuRealtimeQuote",
    },
    "index": {
        "akshare_realtime": "finance_data.provider.akshare.index.realtime:AkshareIndexQuote",
        "tushare_realtime": "finance_data.provider.tushare.index.realtime:TushareIndexQuote",
        "xueqiu_realtime": "finance_data.provider.xueqiu.index.realtime:XueqiuIndexQuote",
        "akshare_history": "finance_data.provider.akshare.index.history:AkshareIndexHistory",
        "tushare_history": "finance_data.provider.tushare.index.history:TushareIndexHistory",
        "xueqiu_history": "finance_data.provider.xueqiu.index.history:XueqiuIndexHistory",
    },
    "sector": {
        "akshare": "finance_data.provider.akshare.sector.realtime:AkshareSectorRank",
    },
    "chip": {
        "akshare": "finance_data.provider.akshare.chip.history:AkshareChipHistory",
        "tushare": "finance_data.provider.tushare.chip.history:TushareChipHistory",
    },
    "fundamental": {
        "akshare": "finance_data.provider.akshare.fundamental.history:AkshareFundamentalHistory",
        "tushare": "finance_data.provider.tushare.fundamental.history:TushareFundamentalHistory",
    },
    "cashflow": {
        "akshare": "finance_data.provider.akshare.cashflow.realtime:AkshareCashflowRealtime",
    },
    "calendar": {
        "akshare": "finance_data.provider.akshare.calendar.history:AkshareCalendarHistory",
        "tushare": "finance_data.provider.tushare.calendar.history:TushareCalendarHistory",
    },
    "market": {
        "akshare": "finance_data.provider.akshare.market.realtime:AkshareMarketRealtime",
    },
    "lhb": {
        "akshare": "finance_data.provider.akshare.lhb.history:AkshareLhbHistory",
        "tushare": "finance_data.provider.tushare.lhb.history:TushareLhbHistory",
    },
    "pool": {
        "akshare": "finance_data.provider.akshare.pool.history:AksharePoolHistory",
    },
    "north_flow": {
        "akshare": "finance_data.provider.akshare.north_flow.history:AkshareNorthFlowHistory",
        "tushare": "finance_data.provider.tushare.north_flow.history:TushareNorthFlowHistory",
    },
    "margin": {
        "akshare": "finance_data.provider.akshare.margin.history:AkshareMarginHistory",
        "tushare": "finance_data.provider.tushare.margin.history:TushareMarginHistory",
    },
    "sector_fund_flow": {
        "akshare": "finance_data.provider.akshare.sector_fund_flow.history:AkshareSectorFundFlowHistory",
    },
}

# Tool -> provider key mapping (handles tools that share a domain)
_TOOL_PROVIDER_KEYS: Dict[str, List[str]] = {
    "tool_get_index_quote_realtime": ["akshare_realtime", "tushare_realtime", "xueqiu_realtime"],
    "tool_get_index_history": ["akshare_history", "tushare_history", "xueqiu_history"],
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


def _get_probe_method_name(tool_name: str) -> str:
    """Map tool name to provider method name"""
    method_map = {
        "tool_get_stock_info_history": "get_stock_info_history",
        "tool_get_kline_history": "get_kline_history",
        "tool_get_realtime_quote": "get_realtime_quote",
        "tool_get_index_quote_realtime": "get_index_quote_realtime",
        "tool_get_index_history": "get_index_history",
        "tool_get_sector_rank_realtime": "get_sector_rank_realtime",
        "tool_get_chip_distribution_history": "get_chip_distribution_history",
        "tool_get_financial_summary_history": "get_financial_summary_history",
        "tool_get_dividend_history": "get_dividend_history",
        "tool_get_earnings_forecast_history": "get_earnings_forecast_history",
        "tool_get_stock_capital_flow_realtime": "get_stock_capital_flow_realtime",
        "tool_get_trade_calendar_history": "get_trade_calendar_history",
        "tool_get_lhb_detail": "get_lhb_detail_history",
        "tool_get_lhb_stock_stat": "get_lhb_stock_stat_history",
        "tool_get_lhb_active_traders": "get_lhb_active_traders_history",
        "tool_get_lhb_trader_stat": "get_lhb_trader_stat_history",
        "tool_get_lhb_stock_detail": "get_lhb_stock_detail_history",
        "tool_get_zt_pool": "get_zt_pool_history",
        "tool_get_strong_stocks": "get_strong_stocks_history",
        "tool_get_previous_zt": "get_previous_zt_history",
        "tool_get_zbgc_pool": "get_zbgc_pool_history",
        "tool_get_north_stock_hold": "get_north_stock_hold_history",
        "tool_get_margin": "get_margin_history",
        "tool_get_margin_detail": "get_margin_detail_history",
        "tool_get_market_stats_realtime": "get_market_stats_realtime",
        "tool_get_market_north_capital": "get_north_flow_history",
        "tool_get_sector_capital_flow": "get_sector_capital_flow_history",
    }
    return method_map.get(tool_name, "")


def _get_providers_for_tool(tool_name: str) -> List[Tuple[str, str]]:
    """Return (provider_name, dotted_path) pairs for a tool"""
    meta = TOOL_REGISTRY.get(tool_name)
    if not meta:
        return []

    domain = meta.domain
    domain_providers = _PROVIDER_MAP.get(domain, {})
    available = _get_available_providers()

    # Some tools in the same domain use different provider keys (e.g., index)
    provider_keys = _TOOL_PROVIDER_KEYS.get(tool_name)

    results = []
    if provider_keys:
        for key in provider_keys:
            if key in domain_providers:
                # Extract base provider name (e.g., "akshare_realtime" -> "akshare")
                base_provider = key.split("_")[0]
                if available.get(base_provider, False):
                    results.append((base_provider, domain_providers[key]))
    else:
        for key, path in domain_providers.items():
            base_provider = key.split("_")[0]
            if available.get(base_provider, False):
                results.append((base_provider, path))

    return results


def _run_single_probe(
    tool_name: str,
    provider_name: str,
    dotted_path: str,
) -> HealthResult:
    """Execute a single probe"""
    method_name = _get_probe_method_name(tool_name)
    params = _get_test_params(tool_name)

    try:
        cls = _import_class(dotted_path)
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
    tasks: List[Tuple[str, str, str]] = []

    if tool_name:
        tools = {tool_name: TOOL_REGISTRY[tool_name]} if tool_name in TOOL_REGISTRY else {}
    else:
        tools = TOOL_REGISTRY

    for tname in tools:
        for provider_name, dotted_path in _get_providers_for_tool(tname):
            tasks.append((tname, provider_name, dotted_path))

    if not tasks:
        return

    with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as pool:
        futures = {
            pool.submit(_run_single_probe, t, p, d): (t, p)
            for t, p, d in tasks
        }
        for future in as_completed(futures):
            yield future.result()
