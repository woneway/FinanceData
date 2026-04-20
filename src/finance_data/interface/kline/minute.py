from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


@dataclass
class MinuteKlineBar:
    symbol: str
    date: str       # YYYYMMDD
    time: str       # HHmmss
    period: str     # 5min / 15min / 30min / 60min
    open: float
    high: float
    low: float
    close: float
    volume: float   # 股
    amount: float   # 元
    adj: str        # qfq / hfq / none

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "time": self.time,
            "period": self.period, "open": self.open, "high": self.high,
            "low": self.low, "close": self.close, "volume": self.volume,
            "amount": self.amount, "adj": self.adj,
        }


class MinuteKlineHistoryProtocol(Protocol):
    def get_minute_kline_history(
        self, symbol: str, period: str, start: str, end: str,
        adj: str = "qfq",
    ) -> DataResult: ...
