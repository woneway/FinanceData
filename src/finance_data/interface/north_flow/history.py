"""北向资金 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class NorthFlowProtocol(Protocol):
    def get_north_flow_history(self) -> DataResult: ...


class NorthStockHoldProtocol(Protocol):
    def get_north_stock_hold_history(
        self, market: str, indicator: str, symbol: str, trade_date: str
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
    close_price: float
    pct_change: float
    hold_volume: float
    hold_market_cap: float
    hold_float_ratio: float
    hold_total_ratio: float
    increase_5d_volume: Optional[float] = None
    increase_5d_cap: Optional[float] = None
    increase_5d_cap_pct: Optional[float] = None
    increase_5d_float_ratio: Optional[float] = None
    increase_5d_total_ratio: Optional[float] = None
    board: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "close_price": self.close_price, "pct_change": self.pct_change,
            "hold_volume": self.hold_volume, "hold_market_cap": self.hold_market_cap,
            "hold_float_ratio": self.hold_float_ratio,
            "hold_total_ratio": self.hold_total_ratio,
            "increase_5d_volume": self.increase_5d_volume,
            "increase_5d_cap": self.increase_5d_cap,
            "increase_5d_cap_pct": self.increase_5d_cap_pct,
            "increase_5d_float_ratio": self.increase_5d_float_ratio,
            "increase_5d_total_ratio": self.increase_5d_total_ratio,
            "board": self.board,
        }
