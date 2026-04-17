"""板块资金流 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class SectorCapitalFlowProtocol(Protocol):
    def get_sector_capital_flow_history(
        self, indicator: str, sector_type: str
    ) -> DataResult: ...


@dataclass
class SectorFundFlow:
    rank: int
    name: str
    pct_chg: float
    main_net_inflow: float
    main_net_inflow_pct: float
    super_large_net_inflow: float
    super_large_net_inflow_pct: float
    large_net_inflow: float
    large_net_inflow_pct: float
    medium_net_inflow: float
    medium_net_inflow_pct: float
    small_net_inflow: float
    small_net_inflow_pct: float
    top_stock: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank, "name": self.name, "pct_chg": self.pct_chg,
            "main_net_inflow": self.main_net_inflow,
            "main_net_inflow_pct": self.main_net_inflow_pct,
            "super_large_net_inflow": self.super_large_net_inflow,
            "super_large_net_inflow_pct": self.super_large_net_inflow_pct,
            "large_net_inflow": self.large_net_inflow,
            "large_net_inflow_pct": self.large_net_inflow_pct,
            "medium_net_inflow": self.medium_net_inflow,
            "medium_net_inflow_pct": self.medium_net_inflow_pct,
            "small_net_inflow": self.small_net_inflow,
            "small_net_inflow_pct": self.small_net_inflow_pct,
            "top_stock": self.top_stock,
        }
