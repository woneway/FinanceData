"""全市场涨跌停价 service - 统一对外入口"""
import logging

from finance_data.interface.stk_limit.history import StkLimitProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _StkLimitDispatcher:
    def __init__(self, providers: list[StkLimitProtocol]):
        self._providers = providers

    def get_stk_limit(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_stk_limit(trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_stk_limit", "所有数据源均失败", "data")


def _build_stk_limit() -> _StkLimitDispatcher:
    from finance_data.provider.tushare.stk_limit.history import TushareStkLimit
    return _StkLimitDispatcher(providers=[TushareStkLimit()])


stk_limit = _build_stk_limit()
