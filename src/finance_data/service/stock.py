"""股票信息 service - 统一对外入口"""
import logging
import os

from finance_data.interface.stock.history import StockHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.stock.history import AkshareStockHistory

logger = logging.getLogger(__name__)


class _StockHistoryDispatcher:
    def __init__(self, providers: list[StockHistoryProtocol]):
        self._providers = providers

    def get_stock_info_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_stock_info_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_stock_info_history", "所有数据源均失败", "data")


def _build_stock_history() -> _StockHistoryDispatcher:
    providers: list[StockHistoryProtocol] = [AkshareStockHistory()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.stock.history import TushareStockHistory
        providers.append(TushareStockHistory())
    # 雪球作为最后 fallback（无需 token，海外可达）
    from finance_data.provider.xueqiu.stock.history import XueqiuStockHistory
    providers.append(XueqiuStockHistory())
    return _StockHistoryDispatcher(providers=providers)


stock_history = _build_stock_history()
