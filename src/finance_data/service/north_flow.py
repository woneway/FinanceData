"""北向资金 service - 统一对外入口"""
import logging

from finance_data.interface.north_flow.history import NorthFlowProtocol, NorthStockHoldProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.north_flow.history import AkshareNorthFlow
from finance_data.provider.tushare.north_flow.history import TushareNorthStockHold

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
        self, symbol: str = "", trade_date: str = "",
        start_date: str = "", end_date: str = "",
        exchange: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_north_stock_hold_history(
                    symbol=symbol, trade_date=trade_date,
                    start_date=start_date, end_date=end_date,
                    exchange=exchange,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_north_stock_hold_history", "所有数据源均失败", "data")


north_flow = _NorthFlowDispatcher(providers=[AkshareNorthFlow()])
north_stock_hold = _NorthStockHoldDispatcher(providers=[TushareNorthStockHold()])
