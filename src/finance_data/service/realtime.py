"""实时行情 service - 统一对外入口（含 TTL 缓存）"""
import logging
import os

from cachetools import TTLCache

from finance_data.interface.realtime.realtime import RealtimeQuoteProtocol
from finance_data.interface.types import DataFetchError, DataResult
logger = logging.getLogger(__name__)

# 实时行情缓存：最多 512 支股票，20 分钟 TTL
_quote_cache: TTLCache = TTLCache(maxsize=512, ttl=1200)


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
                _quote_cache[cache_key] = result
                return result
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_realtime_quote", "所有数据源均失败", "data")


def _build_realtime_quote() -> _RealtimeQuoteDispatcher:
    # 实时行情仅使用 xueqiu（真正的盘中实时价格，无需 token/cookie）
    # tushare 已移除：pro.daily(limit=1) 返回的是收盘价，不是实时行情
    # akshare 已禁用：东财源不可用，新浪源太慢
    from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
    return _RealtimeQuoteDispatcher(providers=[XueqiuRealtimeQuote()])


realtime_quote = _build_realtime_quote()
