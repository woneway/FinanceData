"""热股排行 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class HotRankProtocol(Protocol):
    def get_hot_rank_realtime(self) -> DataResult: ...


@dataclass
class HotRankEntry:
    rank: int
    symbol: str
    name: str
    latest_price: float
    change_amount: float
    pct_chg: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "symbol": self.symbol,
            "name": self.name,
            "latest_price": self.latest_price,
            "change_amount": self.change_amount,
            "pct_chg": self.pct_chg,
        }
