"""集合竞价接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class AuctionProtocol(Protocol):
    def get_auction(self, trade_date: str) -> DataResult: ...


@dataclass
class AuctionEntry:
    symbol: str
    trade_date: str
    price: float
    volume: float
    amount: float
    pre_close: float
    turnover_rate: Optional[float]
    volume_ratio: Optional[float]
    float_share: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "trade_date": self.trade_date,
            "price": self.price,
            "volume": self.volume,
            "amount": self.amount,
            "pre_close": self.pre_close,
            "turnover_rate": self.turnover_rate,
            "volume_ratio": self.volume_ratio,
            "float_share": self.float_share,
        }
