"""全市场日线行情 service - 统一对外入口"""
import logging

from finance_data.interface.daily_market.history import DailyMarketProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _DailyMarketDispatcher:
    def __init__(self, providers: list[DailyMarketProtocol]):
        self._providers = providers

    def get_daily_market(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_daily_market(trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_daily_market", "所有数据源均失败", "data")


def _build_daily_market() -> _DailyMarketDispatcher:
    from finance_data.provider.tushare.daily_market.history import TushareDailyMarket
    return _DailyMarketDispatcher(providers=[TushareDailyMarket()])


daily_market = _build_daily_market()
