"""K线数据 service - 统一对外入口"""
import logging
import os

from finance_data.interface.kline.history import KlineHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.kline.history import AkshareKlineHistory

logger = logging.getLogger(__name__)


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
    # 雪球 K 线需要登录 cookie，仅当配置了 XUEQIU_COOKIE 时启用
    if os.getenv("XUEQIU_COOKIE"):
        from finance_data.provider.xueqiu.kline.history import XueqiuKlineHistory
        providers.append(XueqiuKlineHistory())
    return _KlineHistoryDispatcher(providers=providers)


kline_history = _build_kline_history()
