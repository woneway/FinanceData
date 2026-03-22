from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SectorRank:
    name: str
    pct_chg: float
    leader_stock: str
    leader_pct_chg: float
    up_count: Optional[int] = None
    down_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "pct_chg": self.pct_chg,
                "leader_stock": self.leader_stock,
                "leader_pct_chg": self.leader_pct_chg,
                "up_count": self.up_count, "down_count": self.down_count}
