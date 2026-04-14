"""北向资金 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class NorthFlowProtocol(Protocol):
    def get_north_flow_history(self) -> DataResult: ...


class NorthStockHoldProtocol(Protocol):
    def get_north_stock_hold_history(
        self, symbol: str, trade_date: str,
        start_date: str, end_date: str, exchange: str,
    ) -> DataResult: ...


@dataclass
class NorthFlow:
    date: str
    market: str
    direction: str
    net_buy: float
    net_inflow: float
    balance: float
    up_count: int
    flat_count: int
    down_count: int
    index_name: str
    index_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "market": self.market, "direction": self.direction,
            "net_buy": self.net_buy, "net_inflow": self.net_inflow,
            "balance": self.balance,
            "up_count": self.up_count, "flat_count": self.flat_count,
            "down_count": self.down_count,
            "index_name": self.index_name, "index_pct": self.index_pct,
        }


@dataclass
class NorthStockHold:
    symbol: str
    name: str
    date: str
    hold_volume: float
    hold_ratio: float
    exchange: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "hold_volume": self.hold_volume, "hold_ratio": self.hold_ratio,
            "exchange": self.exchange,
        }
