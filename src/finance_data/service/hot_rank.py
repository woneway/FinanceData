"""热股排行 service - 统一对外入口"""
import logging
from finance_data.config import has_tushare_token

from finance_data.interface.hot_rank.realtime import HotRankProtocol
from finance_data.interface.hot_rank.ths_hot import ThsHotProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _HotRankDispatcher:
    def __init__(self, providers: list[HotRankProtocol]):
        self._providers = providers

    def get_hot_rank_realtime(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_hot_rank_realtime()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_hot_rank_realtime", "所有数据源均失败", "data")


class _ThsHotDispatcher:
    def __init__(self, providers: list[ThsHotProtocol]):
        self._providers = providers

    def get_ths_hot(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_ths_hot(
                    trade_date=trade_date, start_date=start_date, end_date=end_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_ths_hot", "所有数据源均失败", "data")


def _build_hot_rank() -> _HotRankDispatcher:
    from finance_data.provider.akshare.hot_rank.realtime import AkshareHotRank
    return _HotRankDispatcher(providers=[AkshareHotRank()])


def _build_ths_hot() -> _ThsHotDispatcher:
    providers: list[ThsHotProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.hot_rank.ths_hot import TushareThsHot
        providers.append(TushareThsHot())
    return _ThsHotDispatcher(providers=providers)


hot_rank = _build_hot_rank()
ths_hot = _build_ths_hot()
