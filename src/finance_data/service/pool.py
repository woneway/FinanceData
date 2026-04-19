"""股票池 service - 统一对外入口"""
import logging
from finance_data.config import has_tushare_token

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


class _LimitListDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_limit_list(
        self,
        trade_date: str = "",
        limit_type: str = "涨停池",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_limit_list(
                    trade_date=trade_date, limit_type=limit_type,
                    start_date=start_date, end_date=end_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_limit_list", "所有数据源均失败", "data")


def _build_limit_list() -> _LimitListDispatcher:
    providers = []
    if has_tushare_token():
        from finance_data.provider.tushare.pool.limit_list import TushareLimitList
        providers.append(TushareLimitList())
    return _LimitListDispatcher(providers=providers)


class _KplListDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_kpl_list(
        self, trade_date: str = "", tag: str = "涨停",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_kpl_list(
                    trade_date=trade_date, tag=tag,
                    start_date=start_date, end_date=end_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_kpl_list", "所有数据源均失败", "data")


class _LimitStepDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_limit_step(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_limit_step(
                    trade_date=trade_date, start_date=start_date, end_date=end_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_limit_step", "所有数据源均失败", "data")


def _build_kpl_list() -> _KplListDispatcher:
    providers = []
    if has_tushare_token():
        from finance_data.provider.tushare.pool.kpl_list import TushareKplList
        providers.append(TushareKplList())
    return _KplListDispatcher(providers=providers)


def _build_limit_step() -> _LimitStepDispatcher:
    providers = []
    if has_tushare_token():
        from finance_data.provider.tushare.pool.limit_step import TushareLimitStep
        providers.append(TushareLimitStep())
    return _LimitStepDispatcher(providers=providers)


zt_pool = _ZtPoolDispatcher(providers=[AkshareZtPool()])
strong_stocks = _StrongStocksDispatcher(providers=[AkshareStrongStocks()])
previous_zt = _PreviousZtDispatcher(providers=[AksharePreviousZt()])
zbgc_pool = _ZbgcPoolDispatcher(providers=[AkshareZbgcPool()])
limit_list = _build_limit_list()
kpl_list = _build_kpl_list()
limit_step = _build_limit_step()
