"""行业板块 service - 统一对外入口"""
import logging

from finance_data.interface.sector.realtime import SectorRankProtocol
from finance_data.interface.sector.list import SectorListProtocol
from finance_data.interface.sector.member import SectorMemberProtocol
from finance_data.interface.sector.history import SectorHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.sector.realtime import AkshareSectorRank
from finance_data.provider.akshare.sector.list import AkshareSectorList
from finance_data.provider.akshare.sector.member import AkshareSectorMember
from finance_data.provider.akshare.sector.history import AkshareSectorHistory

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


class _SectorListDispatcher:
    def __init__(self, providers: list[SectorListProtocol]):
        self._providers = providers

    def get_sector_list(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_sector_list()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_sector_list", "所有数据源均失败", "data")


class _SectorMemberDispatcher:
    def __init__(self, providers: list[SectorMemberProtocol]):
        self._providers = providers

    def get_sector_member(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_sector_member(symbol=symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_sector_member", "所有数据源均失败", "data")


class _SectorHistoryDispatcher:
    def __init__(self, providers: list[SectorHistoryProtocol]):
        self._providers = providers

    def get_sector_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "日k",
        adjust: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_sector_history(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    adjust=adjust,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_sector_history", "所有数据源均失败", "data")


sector_rank = _SectorRankDispatcher(providers=[AkshareSectorRank()])
sector_list = _SectorListDispatcher(providers=[AkshareSectorList()])
sector_member = _SectorMemberDispatcher(providers=[AkshareSectorMember()])
sector_history = _SectorHistoryDispatcher(providers=[AkshareSectorHistory()])
