"""龙虎榜 service - 统一对外入口

- lhb_detail: tushare（akshare 东财源已禁用）
- lhb_stock_stat, lhb_active_traders, lhb_trader_stat, lhb_stock_detail: akshare 新浪源
"""
import logging
import os

from finance_data.interface.lhb.history import (
    LhbDetailProtocol, LhbStockStatProtocol,
    LhbActiveTradersProtocol, LhbTraderStatProtocol, LhbStockDetailProtocol,
)
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _LhbDetailDispatcher:
    def __init__(self, providers: list[LhbDetailProtocol]):
        self._providers = providers

    def get_lhb_detail_history(self, start_date: str, end_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_detail_history(start_date, end_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_detail_history", "所有数据源均失败", "data")


class _LhbStockStatDispatcher:
    def __init__(self, providers: list[LhbStockStatProtocol]):
        self._providers = providers

    def get_lhb_stock_stat_history(self, period: str = "近一月") -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_stock_stat_history(period)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_stock_stat_history", "所有数据源均失败", "data")


class _LhbActiveTradersDispatcher:
    def __init__(self, providers: list[LhbActiveTradersProtocol]):
        self._providers = providers

    def get_lhb_active_traders_history(self, start_date: str, end_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_active_traders_history(start_date, end_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_active_traders_history", "所有数据源均失败", "data")


class _LhbTraderStatDispatcher:
    def __init__(self, providers: list[LhbTraderStatProtocol]):
        self._providers = providers

    def get_lhb_trader_stat_history(self, period: str = "近一月") -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_trader_stat_history(period)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_trader_stat_history", "所有数据源均失败", "data")


class _LhbStockDetailDispatcher:
    def __init__(self, providers: list[LhbStockDetailProtocol]):
        self._providers = providers

    def get_lhb_stock_detail_history(self, symbol: str, date: str, flag: str = "买入") -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_stock_detail_history(symbol, date, flag)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_stock_detail_history", "所有数据源均失败", "data")


def _build_lhb_detail() -> _LhbDetailDispatcher:
    # akshare 龙虎榜详情已禁用（依赖东财 stock_lhb_detail_em）
    providers: list[LhbDetailProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.lhb.history import TushareLhbDetail
        providers.append(TushareLhbDetail())
    return _LhbDetailDispatcher(providers=providers)


def _build_lhb_stock_stat() -> _LhbStockStatDispatcher:
    from finance_data.provider.akshare.lhb.history import AkshareLhbStockStat
    return _LhbStockStatDispatcher(providers=[AkshareLhbStockStat()])


def _build_lhb_active_traders() -> _LhbActiveTradersDispatcher:
    from finance_data.provider.akshare.lhb.history import AkshareLhbActiveTraders
    return _LhbActiveTradersDispatcher(providers=[AkshareLhbActiveTraders()])


def _build_lhb_trader_stat() -> _LhbTraderStatDispatcher:
    from finance_data.provider.akshare.lhb.history import AkshareLhbTraderStat
    return _LhbTraderStatDispatcher(providers=[AkshareLhbTraderStat()])


def _build_lhb_stock_detail() -> _LhbStockDetailDispatcher:
    from finance_data.provider.akshare.lhb.history import AkshareLhbStockDetail
    return _LhbStockDetailDispatcher(providers=[AkshareLhbStockDetail()])


lhb_detail = _build_lhb_detail()
lhb_stock_stat = _build_lhb_stock_stat()
lhb_active_traders = _build_lhb_active_traders()
lhb_trader_stat = _build_lhb_trader_stat()
lhb_stock_detail = _build_lhb_stock_detail()
