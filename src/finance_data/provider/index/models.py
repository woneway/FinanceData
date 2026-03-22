from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class IndexQuote:
    symbol: str     # 000001.SH
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "name": self.name,
                "price": self.price, "pct_chg": self.pct_chg,
                "volume": self.volume, "amount": self.amount,
                "timestamp": self.timestamp}


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
