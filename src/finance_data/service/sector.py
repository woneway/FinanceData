"""行业板块排名 service - 统一对外入口"""
import logging

from finance_data.interface.sector.realtime import SectorRankProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.sector.realtime import AkshareSectorRank

logger = logging.getLogger(__name__)


class _SectorRankDispatcher:
    def __init__(self, providers: list[SectorRankProtocol]):
        self._providers = providers

    def get_sector_rank_realtime(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_sector_rank_realtime()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_sector_rank_realtime", "所有数据源均失败", "data")


sector_rank = _SectorRankDispatcher(providers=[AkshareSectorRank()])
