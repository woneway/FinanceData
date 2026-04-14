"""融资融券 service - 统一对外入口"""
import logging
import os

from finance_data.interface.margin.history import MarginProtocol, MarginDetailProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.margin.history import AkshareMarginDetail

logger = logging.getLogger(__name__)


class _MarginDispatcher:
    def __init__(self, providers: list[MarginProtocol]):
        self._providers = providers

    def get_margin_history(
        self, trade_date: str, start_date: str, end_date: str, exchange_id: str
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_margin_history(trade_date, start_date, end_date, exchange_id)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_margin_history", "所有数据源均失败", "data")


class _MarginDetailDispatcher:
    def __init__(self, providers: list[MarginDetailProtocol]):
        self._providers = providers

    def get_margin_detail_history(
        self, trade_date: str, start_date: str, end_date: str, ts_code: str
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_margin_detail_history(trade_date, start_date, end_date, ts_code)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_margin_detail_history", "所有数据源均失败", "data")


def _build_margin() -> _MarginDispatcher:
    providers: list[MarginProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.margin.history import TushareMargin
        providers.append(TushareMargin())
    return _MarginDispatcher(providers=providers)


def _build_margin_detail() -> _MarginDetailDispatcher:
    # tushare 优先（支持日期范围+个股查询）
    providers: list[MarginDetailProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.margin.history import TushareMarginDetail
        providers.append(TushareMarginDetail())
    providers.append(AkshareMarginDetail())
    # 雪球作为最后 fallback（仅支持个股查询）
    from finance_data.provider.xueqiu.margin.history import XueqiuMarginDetail
    providers.append(XueqiuMarginDetail())
    return _MarginDetailDispatcher(providers=providers)


margin = _build_margin()
margin_detail = _build_margin_detail()
