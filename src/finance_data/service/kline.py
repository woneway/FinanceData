"""K线数据 service - 统一对外入口"""
import logging
import os

from finance_data.interface.kline.history import (
    DailyKlineHistoryProtocol,
    KlineHistoryProtocol,
    MonthlyKlineHistoryProtocol,
    WeeklyKlineHistoryProtocol,
)
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.kline.history import AkshareKlineHistory
from finance_data.provider.xueqiu.client import has_login_cookie

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 旧接口（保留兼容，将在旧 tool_get_kline_history 下线后删除）
# ---------------------------------------------------------------------------

class _KlineHistoryDispatcher:
    def __init__(self, providers: list[KlineHistoryProtocol]):
        self._providers = providers

    def get_kline_history(self, symbol: str, period: str, start: str, end: str,
                          adj: str = "qfq") -> DataResult:
        for p in self._providers:
            try:
                return p.get_kline_history(symbol, period, start, end, adj)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_kline_history", "所有数据源均失败", "data")


def _build_kline_history() -> _KlineHistoryDispatcher:
    providers: list[KlineHistoryProtocol] = [AkshareKlineHistory()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    # 雪球 K 线需要登录 cookie
    if has_login_cookie():
        from finance_data.provider.xueqiu.kline.history import XueqiuKlineHistory
        providers.append(XueqiuKlineHistory())
    # baostock 作为最终 fallback（极稳定，免费）
    from finance_data.provider.baostock.kline.history import BaostockKlineHistory
    providers.append(BaostockKlineHistory())
    return _KlineHistoryDispatcher(providers=providers)


kline_history = _build_kline_history()


# ---------------------------------------------------------------------------
# 新接口：日线 / 周线 / 月线 独立 dispatcher
# 日线: tushare + akshare；周/月线: tushare
# ---------------------------------------------------------------------------

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
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    providers.append(AkshareKlineHistory())
    return _DailyKlineDispatcher(providers=providers)


def _build_weekly() -> _WeeklyKlineDispatcher:
    providers: list[WeeklyKlineHistoryProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    return _WeeklyKlineDispatcher(providers=providers)


def _build_monthly() -> _MonthlyKlineDispatcher:
    providers: list[MonthlyKlineHistoryProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.kline.history import TushareKlineHistory
        providers.append(TushareKlineHistory())
    return _MonthlyKlineDispatcher(providers=providers)


daily_kline_history = _build_daily()
weekly_kline_history = _build_weekly()
monthly_kline_history = _build_monthly()
