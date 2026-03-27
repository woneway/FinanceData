"""股票池 service - 统一对外入口（仅 akshare）"""
import logging

from finance_data.interface.pool.history import (
    ZtPoolProtocol, StrongStocksProtocol, PreviousZtProtocol, ZbgcPoolProtocol,
)
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.pool.history import (
    AkshareZtPool, AkshareStrongStocks, AksharePreviousZt, AkshareZbgcPool,
)

logger = logging.getLogger(__name__)


class _ZtPoolDispatcher:
    def __init__(self, providers: list[ZtPoolProtocol]):
        self._providers = providers

    def get_zt_pool_history(self, date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_zt_pool_history(date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_zt_pool_history", "所有数据源均失败", "data")


class _StrongStocksDispatcher:
    def __init__(self, providers: list[StrongStocksProtocol]):
        self._providers = providers

    def get_strong_stocks_history(self, date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_strong_stocks_history(date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_strong_stocks_history", "所有数据源均失败", "data")


class _PreviousZtDispatcher:
    def __init__(self, providers: list[PreviousZtProtocol]):
        self._providers = providers

    def get_previous_zt_history(self, date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_previous_zt_history(date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_previous_zt_history", "所有数据源均失败", "data")


class _ZbgcPoolDispatcher:
    def __init__(self, providers: list[ZbgcPoolProtocol]):
        self._providers = providers

    def get_zbgc_pool_history(self, date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_zbgc_pool_history(date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_zbgc_pool_history", "所有数据源均失败", "data")


zt_pool = _ZtPoolDispatcher(providers=[AkshareZtPool()])
strong_stocks = _StrongStocksDispatcher(providers=[AkshareStrongStocks()])
previous_zt = _PreviousZtDispatcher(providers=[AksharePreviousZt()])
zbgc_pool = _ZbgcPoolDispatcher(providers=[AkshareZbgcPool()])
