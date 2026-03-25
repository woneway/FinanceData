"""个股资金流向 service - 统一对外入口"""
import logging

from finance_data.interface.cashflow.realtime import StockCapitalFlowProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.cashflow.realtime import AkshareStockCapitalFlow

logger = logging.getLogger(__name__)


class _StockCapitalFlowDispatcher:
    def __init__(self, providers: list[StockCapitalFlowProtocol]):
        self._providers = providers

    def get_stock_capital_flow_realtime(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_stock_capital_flow_realtime(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_stock_capital_flow_realtime", "所有数据源均失败", "data")


stock_capital_flow = _StockCapitalFlowDispatcher(providers=[AkshareStockCapitalFlow()])
