"""实时行情 service - 统一对外入口（含 TTL 缓存）

雪球提供核心行情，腾讯补充 circ_market_cap/volume_ratio/limit_up/limit_down/prev_close。
"""
import logging

from cachetools import TTLCache

from finance_data.interface.realtime.realtime import RealtimeQuoteProtocol
from finance_data.interface.types import DataFetchError, DataResult
logger = logging.getLogger(__name__)

_quote_cache: TTLCache = TTLCache(maxsize=512, ttl=1200)


def _enrich_with_tencent(result: DataResult, symbol: str) -> DataResult:
    """用腾讯 API 补充雪球缺少的字段（best-effort，失败不影响主流程）"""
    try:
        from finance_data.provider.tencent.client import fetch_quote
        tq = fetch_quote(symbol)
        for row in result.data:
            row["circ_market_cap"] = tq.get("circ_market_cap")
            row["volume_ratio"] = tq.get("volume_ratio")
            row["limit_up"] = tq.get("limit_up")
            row["limit_down"] = tq.get("limit_down")
            row["prev_close"] = tq.get("prev_close")
    except Exception as e:
        logger.debug(f"腾讯补充字段失败（不影响主流程）: {e}")
    return result


class _RealtimeQuoteDispatcher:
    def __init__(self, providers: list[RealtimeQuoteProtocol]):
        self._providers = providers

    def get_realtime_quote(self, symbol: str) -> DataResult:
        cache_key = f"realtime:{symbol}"
        cached = _quote_cache.get(cache_key)
        if cached is not None:
            return cached

        for p in self._providers:
            try:
                result = p.get_realtime_quote(symbol)
                result = _enrich_with_tencent(result, symbol)
                _quote_cache[cache_key] = result
                return result
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_realtime_quote", "所有数据源均失败", "data")


def _build_realtime_quote() -> _RealtimeQuoteDispatcher:
    from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
    return _RealtimeQuoteDispatcher(providers=[XueqiuRealtimeQuote()])


realtime_quote = _build_realtime_quote()
