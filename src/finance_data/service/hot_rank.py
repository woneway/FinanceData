"""热股排行 service - 统一对外入口"""
import logging

from finance_data.interface.hot_rank.realtime import HotRankProtocol
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


def _build_hot_rank() -> _HotRankDispatcher:
    from finance_data.provider.akshare.hot_rank.realtime import AkshareHotRank
    return _HotRankDispatcher(providers=[AkshareHotRank()])


hot_rank = _build_hot_rank()
