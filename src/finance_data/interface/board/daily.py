"""东财板块日行情接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class BoardDailyProtocol(Protocol):
    def get_board_daily(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult: ...


@dataclass
class BoardDailyRow:
    board_code: str
    board_name: str
    idx_type: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    change: float
    pct_chg: float
    volume: float
    amount: float
    swing: float
    turnover_rate: float
    level: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_code": self.board_code,
            "board_name": self.board_name,
            "idx_type": self.idx_type,
            "trade_date": self.trade_date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "change": self.change,
            "pct_chg": self.pct_chg,
            "volume": self.volume,
            "amount": self.amount,
            "swing": self.swing,
            "turnover_rate": self.turnover_rate,
            "level": self.level,
        }
