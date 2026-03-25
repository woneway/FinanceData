"""个股资金流向接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class StockCapitalFlowProtocol(Protocol):
    def get_stock_capital_flow_realtime(self, symbol: str) -> DataResult: ...


@dataclass
class FundFlow:
    symbol: str
    date: str
    net_inflow: float
    net_inflow_pct: float
    main_net_inflow: float
    main_net_inflow_pct: float
    super_large_net_inflow: float
    super_large_net_inflow_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "net_inflow": self.net_inflow,
                "net_inflow_pct": self.net_inflow_pct,
                "main_net_inflow": self.main_net_inflow,
                "main_net_inflow_pct": self.main_net_inflow_pct,
                "super_large_net_inflow": self.super_large_net_inflow,
                "super_large_net_inflow_pct": self.super_large_net_inflow_pct}
