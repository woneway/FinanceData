"""行业板块历史行情接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class SectorHistoryProtocol(Protocol):
    def get_sector_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "日k",
        adjust: str = "",
    ) -> DataResult: ...


@dataclass
class SectorBar:
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    amount: float
    amplitude: float
    pct_chg: float
    pct_chg_amount: float
    turnover: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "open": self.open,
            "close": self.close,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
            "amplitude": self.amplitude,
            "pct_chg": self.pct_chg,
            "pct_chg_amount": self.pct_chg_amount,
            "turnover": self.turnover,
        }
