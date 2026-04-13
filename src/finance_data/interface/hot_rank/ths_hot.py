"""同花顺热股排行接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class ThsHotProtocol(Protocol):
    def get_ths_hot(self, trade_date: str = "") -> DataResult: ...


@dataclass
class ThsHotEntry:
    symbol: str
    name: str
    rank: int
    pct_chg: float
    current_price: float
    hot: Optional[float]
    concept: str
    rank_reason: str
    trade_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "rank": self.rank,
            "pct_chg": self.pct_chg,
            "current_price": self.current_price,
            "hot": self.hot,
            "concept": self.concept,
            "rank_reason": self.rank_reason,
            "trade_date": self.trade_date,
        }
