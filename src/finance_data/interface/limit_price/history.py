"""涨跌停价格接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class LimitPriceProtocol(Protocol):
    def get_limit_price(self, symbol: str) -> DataResult: ...


@dataclass
class LimitPrice:
    symbol: str
    name: str
    date: str
    limit_up: float       # 涨停价（元）
    limit_down: float     # 跌停价（元）
    prev_close: float     # 昨收价（元）
    current: float        # 当前价（元）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "limit_up": self.limit_up, "limit_down": self.limit_down,
            "prev_close": self.prev_close, "current": self.current,
        }
