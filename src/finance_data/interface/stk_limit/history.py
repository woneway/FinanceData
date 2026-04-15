"""全市场涨跌停价接口定义（按 trade_date 查询）"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class StkLimitProtocol(Protocol):
    def get_stk_limit(self, trade_date: str) -> DataResult: ...


@dataclass
class StkLimitEntry:
    symbol: str
    trade_date: str
    pre_close: float
    up_limit: float
    down_limit: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "trade_date": self.trade_date,
            "pre_close": self.pre_close,
            "up_limit": self.up_limit, "down_limit": self.down_limit,
        }
