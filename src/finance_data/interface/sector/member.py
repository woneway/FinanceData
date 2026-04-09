"""行业板块成分股接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class SectorMemberProtocol(Protocol):
    def get_sector_member(self, symbol: str) -> DataResult: ...


@dataclass
class SectorMember:
    symbol: str
    name: str
    price: float
    pct_chg: float
    pct_chg_amount: float
    volume: float
    amount: float
    amplitude: float
    high: float
    low: float
    open: float
    prev_close: float
    turnover: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "pct_chg": self.pct_chg,
            "pct_chg_amount": self.pct_chg_amount,
            "volume": self.volume,
            "amount": self.amount,
            "amplitude": self.amplitude,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "prev_close": self.prev_close,
            "turnover": self.turnover,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
        }
