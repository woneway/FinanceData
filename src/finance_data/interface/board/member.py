"""东财板块成分接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class BoardMemberProtocol(Protocol):
    def get_board_member(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult: ...


@dataclass
class BoardMemberRow:
    board_code: str
    board_name: str
    idx_type: str
    trade_date: str
    symbol: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_code": self.board_code,
            "board_name": self.board_name,
            "idx_type": self.idx_type,
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "name": self.name,
        }
