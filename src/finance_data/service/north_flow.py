"""北向资金 service - 统一对外入口"""
import logging
import os

from finance_data.interface.north_flow.history import NorthFlowProtocol, NorthStockHoldProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.north_flow.history import AkshareNorthFlow, AkshareNorthStockHold

logger = logging.getLogger(__name__)


class _NorthFlowDispatcher:
    def __init__(self, providers: list[NorthFlowProtocol]):
        self._providers = providers

    def get_north_flow_history(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_north_flow_history()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_north_flow_history", "所有数据源均失败", "data")


class _NorthStockHoldDispatcher:
    def __init__(self, providers: list[NorthStockHoldProtocol]):
        self._providers = providers

    def get_north_stock_hold_history(
        self, market: str, indicator: str, symbol: str, trade_date: str
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_north_stock_hold_history(market, indicator, symbol, trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_north_stock_hold_history", "所有数据源均失败", "data")


def _build_north_stock_hold() -> _NorthStockHoldDispatcher:
    providers: list[NorthStockHoldProtocol] = [AkshareNorthStockHold()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.north_flow.history import TushareNorthStockHold
        providers.append(TushareNorthStockHold())
    return _NorthStockHoldDispatcher(providers=providers)


north_flow = _NorthFlowDispatcher(providers=[AkshareNorthFlow()])
north_stock_hold = _build_north_stock_hold()
