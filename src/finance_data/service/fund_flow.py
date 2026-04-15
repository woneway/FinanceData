"""资金流向（板块+大盘）- 业务编排层"""
import logging
import os

from finance_data.interface.fund_flow.board import BoardMoneyflowProtocol
from finance_data.interface.fund_flow.market import MarketMoneyflowProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _BoardMoneyflowDispatcher:
    def __init__(self, providers: list[BoardMoneyflowProtocol]):
        self._providers = providers

    def get_board_moneyflow(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        ts_code: str = "",
        content_type: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_board_moneyflow(trade_date, start_date, end_date, ts_code, content_type)
            except DataFetchError as e:
                logger.warning("%s 失败: %s", type(p).__name__, e)
        raise DataFetchError("all", "get_board_moneyflow", "所有数据源均失败", "data")


class _MarketMoneyflowDispatcher:
    def __init__(self, providers: list[MarketMoneyflowProtocol]):
        self._providers = providers

    def get_market_moneyflow(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_market_moneyflow(trade_date, start_date, end_date)
            except DataFetchError as e:
                logger.warning("%s 失败: %s", type(p).__name__, e)
        raise DataFetchError("all", "get_market_moneyflow", "所有数据源均失败", "data")


def _build_board_moneyflow() -> _BoardMoneyflowDispatcher:
    providers: list[BoardMoneyflowProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.fund_flow.board import TushareBoardMoneyflow
        providers.append(TushareBoardMoneyflow())
    return _BoardMoneyflowDispatcher(providers=providers)


def _build_market_moneyflow() -> _MarketMoneyflowDispatcher:
    providers: list[MarketMoneyflowProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.fund_flow.market import TushareMarketMoneyflow
        providers.append(TushareMarketMoneyflow())
    return _MarketMoneyflowDispatcher(providers=providers)


board_moneyflow = _build_board_moneyflow()
market_moneyflow = _build_market_moneyflow()
