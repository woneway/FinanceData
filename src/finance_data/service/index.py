"""大盘指数 service - 统一对外入口"""
import logging
import os

from finance_data.interface.index.realtime import IndexQuoteProtocol
from finance_data.interface.index.history import IndexHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.index.realtime import AkshareIndexQuote
from finance_data.provider.akshare.index.history import AkshareIndexHistory
from finance_data.provider.xueqiu.client import has_login_cookie

logger = logging.getLogger(__name__)


class _IndexQuoteDispatcher:
    def __init__(self, providers: list[IndexQuoteProtocol]):
        self._providers = providers

    def get_index_quote_realtime(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_index_quote_realtime(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_index_quote_realtime", "所有数据源均失败", "data")


class _IndexHistoryDispatcher:
    def __init__(self, providers: list[IndexHistoryProtocol]):
        self._providers = providers

    def get_index_history(self, symbol: str, start: str, end: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_index_history(symbol, start, end)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_index_history", "所有数据源均失败", "data")


def _build_index_quote() -> _IndexQuoteDispatcher:
    providers: list[IndexQuoteProtocol] = [AkshareIndexQuote()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.index.realtime import TushareIndexQuote
        providers.append(TushareIndexQuote())
    # 雪球指数实时行情作为最后 fallback（无需 token，海外可达）
    from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote
    providers.append(XueqiuIndexQuote())
    return _IndexQuoteDispatcher(providers=providers)


def _build_index_history() -> _IndexHistoryDispatcher:
    providers: list[IndexHistoryProtocol] = [AkshareIndexHistory()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.index.history import TushareIndexHistory
        providers.append(TushareIndexHistory())
    # 雪球指数 K 线需要登录 cookie
    if has_login_cookie():
        from finance_data.provider.xueqiu.index.history import XueqiuIndexHistory
        providers.append(XueqiuIndexHistory())
    return _IndexHistoryDispatcher(providers=providers)


index_quote = _build_index_quote()
index_history = _build_index_history()
