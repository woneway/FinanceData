"""东财板块索引/快照接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class BoardIndexProtocol(Protocol):
    def get_board_index(
        self,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult: ...


@dataclass
class BoardIndexRow:
    board_code: str
    board_name: str
    idx_type: str
    trade_date: str
    level: Optional[str]
    leading_stock: str
    leading_stock_code: str
    pct_change: float
    leading_pct: float
    total_mv: float
    turnover_rate: float
    up_num: Optional[int]
    down_num: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_code": self.board_code,
            "board_name": self.board_name,
            "idx_type": self.idx_type,
            "trade_date": self.trade_date,
            "level": self.level,
            "leading_stock": self.leading_stock,
            "leading_stock_code": self.leading_stock_code,
            "pct_change": self.pct_change,
            "leading_pct": self.leading_pct,
            "total_mv": self.total_mv,
            "turnover_rate": self.turnover_rate,
            "up_num": self.up_num,
            "down_num": self.down_num,
        }
