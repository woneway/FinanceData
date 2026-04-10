from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


@dataclass
class KlineBar:
    symbol: str
    date: str
    period: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float
    adj: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "period": self.period,
            "open": self.open, "high": self.high, "low": self.low,
            "close": self.close, "volume": self.volume, "amount": self.amount,
            "pct_chg": self.pct_chg, "adj": self.adj,
        }


class KlineHistoryProtocol(Protocol):
    """旧接口，保留供内部兼容。"""
    def get_kline_history(self, symbol: str, period: str, start: str, end: str,
                          adj: str) -> DataResult: ...


class DailyKlineHistoryProtocol(Protocol):
    def get_daily_kline_history(self, symbol: str, start: str, end: str,
                                adj: str = "qfq") -> DataResult: ...


class WeeklyKlineHistoryProtocol(Protocol):
    def get_weekly_kline_history(self, symbol: str, start: str, end: str,
                                 adj: str = "qfq") -> DataResult: ...


class MonthlyKlineHistoryProtocol(Protocol):
    def get_monthly_kline_history(self, symbol: str, start: str, end: str,
                                  adj: str = "qfq") -> DataResult: ...
