"""日频基本面 service - 统一对外入口

数据源优先级：tencent（实时65ms）
"""
import logging

from finance_data.interface.daily_basic.history import DailyBasicProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tencent.daily_basic import TencentDailyBasic

logger = logging.getLogger(__name__)


class _DailyBasicDispatcher:
    def __init__(self, providers: list[DailyBasicProtocol]):
        self._providers = providers

    def get_daily_basic(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_daily_basic(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_daily_basic", "所有数据源均失败", "data")


daily_basic = _DailyBasicDispatcher(providers=[TencentDailyBasic()])


# --- 全市场按日期查询 ---

class _DailyBasicMarketDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_daily_basic_market(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_daily_basic_market(trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_daily_basic_market", "所有数据源均失败", "data")


def _build_daily_basic_market() -> _DailyBasicMarketDispatcher:
    from finance_data.provider.tushare.daily_basic.history import TushareDailyBasicMarket
    return _DailyBasicMarketDispatcher(providers=[TushareDailyBasicMarket()])


daily_basic_market = _build_daily_basic_market()
