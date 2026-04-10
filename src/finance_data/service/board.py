"""Board service - 统一对外入口"""
import logging

from finance_data.interface.board.daily import BoardDailyProtocol
from finance_data.interface.board.index import BoardIndexProtocol
from finance_data.interface.board.member import BoardMemberProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.board.daily import TushareBoardDaily
from finance_data.provider.tushare.board.index import TushareBoardIndex
from finance_data.provider.tushare.board.member import TushareBoardMember

logger = logging.getLogger(__name__)


class _BoardIndexDispatcher:
    def __init__(self, providers: list[BoardIndexProtocol]):
        self._providers = providers

    def get_board_index(self, idx_type: str, trade_date: str = "") -> DataResult:
        for p in self._providers:
            try:
                return p.get_board_index(idx_type=idx_type, trade_date=trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_board_index", "所有数据源均失败", "data")


class _BoardMemberDispatcher:
    def __init__(self, providers: list[BoardMemberProtocol]):
        self._providers = providers

    def get_board_member(self, board_name: str, idx_type: str, trade_date: str = "") -> DataResult:
        for p in self._providers:
            try:
                return p.get_board_member(
                    board_name=board_name,
                    idx_type=idx_type,
                    trade_date=trade_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_board_member", "所有数据源均失败", "data")


class _BoardDailyDispatcher:
    def __init__(self, providers: list[BoardDailyProtocol]):
        self._providers = providers

    def get_board_daily(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_board_daily(
                    board_name=board_name,
                    idx_type=idx_type,
                    trade_date=trade_date,
                    start_date=start_date,
                    end_date=end_date,
                )
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_board_daily", "所有数据源均失败", "data")


board_index = _BoardIndexDispatcher(providers=[TushareBoardIndex()])
board_member = _BoardMemberDispatcher(providers=[TushareBoardMember()])
board_daily = _BoardDailyDispatcher(providers=[TushareBoardDaily()])
