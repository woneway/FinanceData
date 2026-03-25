"""交易日历接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class TradeCalendarProtocol(Protocol):
    def get_trade_calendar_history(self, start: str, end: str) -> DataResult: ...


@dataclass
class TradeDate:
    date: str
    is_open: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "is_open": self.is_open}
