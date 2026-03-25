"""市场统计 service - 统一对外入口"""
import logging
import os

from finance_data.interface.market.realtime import MarketRealtimeProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.market.realtime import AkshareMarketRealtime

logger = logging.getLogger(__name__)


class _MarketRealtimeDispatcher:
    def __init__(self, providers: list[MarketRealtimeProtocol]):
        self._providers = providers

    def get_market_stats_realtime(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_market_stats_realtime()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_market_stats_realtime", "所有数据源均失败", "data")


def _build_market_realtime() -> _MarketRealtimeDispatcher:
    providers: list[MarketRealtimeProtocol] = [AkshareMarketRealtime()]
    # tushare 无等效接口，不注册
    return _MarketRealtimeDispatcher(providers=providers)


market_realtime = _build_market_realtime()
