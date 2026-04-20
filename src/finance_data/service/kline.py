"""K线数据 service - 统一对外入口

日线: tushare + akshare(腾讯源)
周线/月线: tushare
分钟(5/15/30/60min): baostock
"""
import logging
from finance_data.config import has_tushare_token

from finance_data.interface.kline.history import (
    DailyKlineHistoryProtocol,
    MonthlyKlineHistoryProtocol,
    WeeklyKlineHistoryProtocol,
)
from finance_data.interface.kline.minute import MinuteKlineHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.kline.history import AkshareKlineHistory

logger = logging.getLogger(__name__)

class _DailyKlineDispatcher:
    def __init__(self, providers: list[DailyKlineHistoryProtocol]):
        self._providers = providers

    def get_daily_kline_history(self, symbol: str, start: str, end: str,
                                adj: str = "qfq") -> DataResult:
        for p in self._providers:
            try:
                return p.get_daily_kline_history(symbol, start, end, adj)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} daily 失败: {e}")
        raise DataFetchError("all", "get_daily_kline_history", "所有数据源均失败", "data")


class _WeeklyKlineDispatcher:
    def __init__(self, providers: list[WeeklyKlineHistoryProtocol]):
        self._providers = providers

    def get_weekly_kline_history(self, symbol: str, start: str, end: str,
                                 adj: str = "qfq") -> DataResult:
        for p in self._providers:
            try:
                return p.get_weekly_kline_history(symbol, start, end, adj)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} weekly 失败: {e}")
        raise DataFetchError("all", "get_weekly_kline_history", "所有数据源均失败", "data")


class _MonthlyKlineDispatcher:
    def __init__(self, providers: list[MonthlyKlineHistoryProtocol]):
        self._providers = providers

    def get_monthly_kline_history(self, symbol: str, start: str, end: str,
                                  adj: str = "qfq") -> DataResult:
        for p in self._providers:
            try:
                return p.get_monthly_kline_history(symbol, start, end, adj)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} monthly 失败: {e}")
        raise DataFetchError("all", "get_monthly_kline_history", "所有数据源均失败", "data")


def _build_daily() -> _DailyKlineDispatcher:
    providers: list[DailyKlineHistoryProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    providers.append(AkshareKlineHistory())
    return _DailyKlineDispatcher(providers=providers)


def _build_weekly() -> _WeeklyKlineDispatcher:
    providers: list[WeeklyKlineHistoryProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    return _WeeklyKlineDispatcher(providers=providers)


def _build_monthly() -> _MonthlyKlineDispatcher:
    providers: list[MonthlyKlineHistoryProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    return _MonthlyKlineDispatcher(providers=providers)


class _MinuteKlineDispatcher:
    def __init__(self, providers: list[MinuteKlineHistoryProtocol]):
        self._providers = providers

    def get_minute_kline_history(self, symbol: str, period: str, start: str, end: str,
                                 adj: str = "qfq") -> DataResult:
        for p in self._providers:
            try:
                return p.get_minute_kline_history(symbol, period, start, end, adj)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} minute 失败: {e}")
        raise DataFetchError("all", "get_minute_kline_history", "所有数据源均失败", "data")


def _build_minute() -> _MinuteKlineDispatcher:
    from finance_data.provider.baostock.kline.minute import BaostockMinuteKline
    return _MinuteKlineDispatcher(providers=[BaostockMinuteKline()])


daily_kline_history = _build_daily()
weekly_kline_history = _build_weekly()
monthly_kline_history = _build_monthly()
minute_kline_history = _build_minute()
