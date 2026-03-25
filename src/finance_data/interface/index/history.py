"""大盘指数历史 K线接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class IndexHistoryProtocol(Protocol):
    def get_index_history(self, symbol: str, start: str, end: str) -> DataResult: ...


@dataclass
class IndexBar:
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "open": self.open, "high": self.high, "low": self.low,
                "close": self.close, "volume": self.volume,
                "amount": self.amount, "pct_chg": self.pct_chg}
