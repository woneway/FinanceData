"""筹码分布接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class ChipHistoryProtocol(Protocol):
    def get_chip_distribution_history(self, symbol: str) -> DataResult: ...


@dataclass
class ChipDistribution:
    symbol: str
    date: str
    avg_cost: float
    concentration: Optional[float]
    profit_ratio: float
    cost_90: float
    cost_10: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "avg_cost": self.avg_cost, "concentration": self.concentration,
                "cost_profit_ratio": self.profit_ratio,
                "cost_90": self.cost_90, "cost_10": self.cost_10}
