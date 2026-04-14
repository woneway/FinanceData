"""实时行情接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class RealtimeQuoteProtocol(Protocol):
    def get_realtime_quote(self, symbol: str) -> DataResult: ...


@dataclass
class RealtimeQuote:
    symbol: str
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    market_cap: Optional[float]
    pe: Optional[float]
    pb: Optional[float]
    turnover_rate: Optional[float]
    timestamp: str  # ISO 8601
    circ_market_cap: Optional[float] = None
    volume_ratio: Optional[float] = None
    limit_up: Optional[float] = None
    limit_down: Optional[float] = None
    prev_close: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "symbol": self.symbol, "name": self.name,
            "price": self.price, "pct_chg": self.pct_chg,
            "volume": self.volume, "amount": self.amount,
            "market_cap": self.market_cap, "pe": self.pe,
            "pb": self.pb, "turnover_rate": self.turnover_rate,
            "timestamp": self.timestamp,
        }
        for key in ("circ_market_cap", "volume_ratio", "limit_up", "limit_down", "prev_close"):
            val = getattr(self, key)
            if val is not None:
                d[key] = val
        return d
