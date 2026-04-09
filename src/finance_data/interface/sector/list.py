"""行业板块列表接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class SectorListProtocol(Protocol):
    def get_sector_list(self) -> DataResult: ...


@dataclass
class SectorInfo:
    name: str
    code: str
    price: float
    pct_chg: float
    pct_chg_amount: float
    market_cap: float
    turnover: float
    up_count: Optional[int] = None
    down_count: Optional[int] = None
    leader_stock: str = ""
    leader_pct_chg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "price": self.price,
            "pct_chg": self.pct_chg,
            "pct_chg_amount": self.pct_chg_amount,
            "market_cap": self.market_cap,
            "turnover": self.turnover,
            "up_count": self.up_count,
            "down_count": self.down_count,
            "leader_stock": self.leader_stock,
            "leader_pct_chg": self.leader_pct_chg,
        }
