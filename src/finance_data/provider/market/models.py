from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MarketStats:
    date: str
    total_count: int
    up_count: int
    down_count: int
    flat_count: int
    total_amount: Optional[float] = None    # 总成交额（元）

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "total_count": self.total_count,
                "up_count": self.up_count, "down_count": self.down_count,
                "flat_count": self.flat_count, "total_amount": self.total_amount}
