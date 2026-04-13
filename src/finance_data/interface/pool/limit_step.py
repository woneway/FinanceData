"""连板天梯接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class LimitStepProtocol(Protocol):
    def get_limit_step(self, trade_date: str) -> DataResult: ...


@dataclass
class LimitStepEntry:
    symbol: str
    name: str
    trade_date: str
    nums: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "trade_date": self.trade_date,
            "nums": self.nums,
        }
