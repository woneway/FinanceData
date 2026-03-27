"""个股资金流向 service - 统一对外入口"""
import logging

from finance_data.interface.cashflow.realtime import StockCapitalFlowProtocol
from finance_data.interface.types import DataFetchError, DataResult

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


def _build_stock_capital_flow() -> _StockCapitalFlowDispatcher:
    # akshare 资金流向已禁用（依赖东财 stock_individual_fund_flow）
    providers: list[StockCapitalFlowProtocol] = []
    # 雪球作为主要数据源（无需 token，海外可达）
    from finance_data.provider.xueqiu.cashflow.realtime import XueqiuStockCapitalFlow
    providers.append(XueqiuStockCapitalFlow())
    return _StockCapitalFlowDispatcher(providers=providers)


stock_capital_flow = _build_stock_capital_flow()
