"""股票信息 service - 统一对外入口"""
import logging
from finance_data.config import has_tushare_token

from finance_data.interface.stock.history import StockHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
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
    providers: list[StockHistoryProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.stock.history import TushareStockHistory
        providers.append(TushareStockHistory())
    # 雪球作为主要数据源（无需 token，海外可达）
    from finance_data.provider.xueqiu.stock.history import XueqiuStockHistory
    providers.append(XueqiuStockHistory())
    return _StockHistoryDispatcher(providers=providers)


stock_history = _build_stock_history()


# --- 全市场股票列表 ---

class _StockBasicListDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_stock_basic_list(self, list_status: str = "L") -> DataResult:
        for p in self._providers:
            try:
                return p.get_stock_basic_list(list_status)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_stock_basic_list", "所有数据源均失败", "data")


def _build_stock_basic_list() -> _StockBasicListDispatcher:
    from finance_data.provider.tushare.stock.basic_list import TushareStockBasicList
    return _StockBasicListDispatcher(providers=[TushareStockBasicList()])


stock_basic_list = _build_stock_basic_list()
