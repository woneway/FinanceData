"""交易日历 service - 统一对外入口（tushare 优先）"""
import logging
import os

from finance_data.interface.calendar.history import TradeCalendarProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.calendar.history import AkshareTradeCalendar

logger = logging.getLogger(__name__)


class _TradeCalendarDispatcher:
    def __init__(self, providers: list[TradeCalendarProtocol]):
        self._providers = providers

    def get_trade_calendar_history(self, start: str, end: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_trade_calendar_history(start, end)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_trade_calendar_history", "所有数据源均失败", "data")


def _build_trade_calendar() -> _TradeCalendarDispatcher:
    # tushare 优先
    providers: list[TradeCalendarProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.calendar.history import TushareTradeCalendar
        providers.append(TushareTradeCalendar())
    providers.append(AkshareTradeCalendar())
    return _TradeCalendarDispatcher(providers=providers)


trade_calendar = _build_trade_calendar()
