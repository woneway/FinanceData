from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


@dataclass
class MarketStats:
    date: str
    total_count: int
    up_count: int
    down_count: int
    flat_count: int
    total_amount: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "total_count": self.total_count,
            "up_count": self.up_count,
            "down_count": self.down_count,
            "flat_count": self.flat_count,
            "total_amount": self.total_amount,
        }


class MarketRealtimeProtocol(Protocol):
    def get_market_stats_realtime(self) -> DataResult: ...
