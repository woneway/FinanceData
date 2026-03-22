from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ChipDistribution:
    symbol: str
    date: str
    avg_cost: float
    concentration: float    # 筹码集中度 %
    profit_ratio: float     # 获利比例 %
    cost_90: float          # 90% 筹码成本区间上沿
    cost_10: float          # 下沿

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "avg_cost": self.avg_cost, "concentration": self.concentration,
                "profit_ratio": self.profit_ratio,
                "cost_90": self.cost_90, "cost_10": self.cost_10}
