"""收盘集合竞价接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class AuctionCloseProtocol(Protocol):
    def get_auction_close(self, trade_date: str) -> DataResult: ...


@dataclass
class AuctionCloseEntry:
    symbol: str
    trade_date: str
    close: float
    open: float
    high: float
    low: float
    volume: float
    amount: float
    vwap: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "trade_date": self.trade_date,
            "close": self.close,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
            "vwap": self.vwap,
        }
