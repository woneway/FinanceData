"""龙虎榜 service - 统一对外入口"""
import logging
import os

from finance_data.interface.lhb.history import (
    LhbDetailProtocol, LhbStockStatProtocol, LhbActiveTradersProtocol,
    LhbTraderStatProtocol, LhbStockDetailProtocol,
)
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.lhb.history import (
    AkshareLhbDetail, AkshareLhbStockStat, AkshareLhbActiveTraders,
    AkshareLhbTraderStat, AkshareLhbStockDetail,
)

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

    def get_lhb_stock_stat_history(self, period: str) -> DataResult:
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

    def get_lhb_trader_stat_history(self, period: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_trader_stat_history(period)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_trader_stat_history", "所有数据源均失败", "data")


class _LhbStockDetailDispatcher:
    def __init__(self, providers: list[LhbStockDetailProtocol]):
        self._providers = providers

    def get_lhb_stock_detail_history(self, symbol: str, date: str, flag: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_lhb_stock_detail_history(symbol, date, flag)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_lhb_stock_detail_history", "所有数据源均失败", "data")


def _build_lhb_detail() -> _LhbDetailDispatcher:
    providers: list[LhbDetailProtocol] = [AkshareLhbDetail()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.lhb.history import TushareLhbDetail
        providers.append(TushareLhbDetail())
    return _LhbDetailDispatcher(providers=providers)


lhb_detail = _build_lhb_detail()
lhb_stock_stat = _LhbStockStatDispatcher(providers=[AkshareLhbStockStat()])
lhb_active_traders = _LhbActiveTradersDispatcher(providers=[AkshareLhbActiveTraders()])
lhb_trader_stat = _LhbTraderStatDispatcher(providers=[AkshareLhbTraderStat()])
lhb_stock_detail = _LhbStockDetailDispatcher(providers=[AkshareLhbStockDetail()])
