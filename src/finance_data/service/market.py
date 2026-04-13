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


class _AuctionDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_auction(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_auction(trade_date=trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_auction", "所有数据源均失败", "data")


def _build_auction() -> _AuctionDispatcher:
    providers = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.market.auction import TushareAuction
        providers.append(TushareAuction())
    return _AuctionDispatcher(providers=providers)


class _AuctionCloseDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_auction_close(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_auction_close(trade_date=trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_auction_close", "所有数据源均失败", "data")


def _build_auction_close() -> _AuctionCloseDispatcher:
    providers = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.market.auction_close import TushareAuctionClose
        providers.append(TushareAuctionClose())
    return _AuctionCloseDispatcher(providers=providers)


market_realtime = _build_market_realtime()
auction = _build_auction()
auction_close = _build_auction_close()
