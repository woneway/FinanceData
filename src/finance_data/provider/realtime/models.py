from dataclasses import dataclass
from typing import Any, Dict, Optional


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "price": self.price, "pct_chg": self.pct_chg,
            "volume": self.volume, "amount": self.amount,
            "market_cap": self.market_cap, "pe": self.pe,
            "pb": self.pb, "turnover_rate": self.turnover_rate,
            "timestamp": self.timestamp,
        }
