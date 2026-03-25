"""大盘指数实时行情接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class IndexQuoteProtocol(Protocol):
    def get_index_quote_realtime(self, symbol: str) -> DataResult: ...


@dataclass
class IndexQuote:
    symbol: str
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
