from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class FundFlow:
    symbol: str
    date: str
    net_inflow: float               # 主力净流入（元）= main_net_inflow
    net_inflow_pct: float           # 主力净流入占比 %
    main_net_inflow: float          # 主力净流入（元）
    main_net_inflow_pct: float      # 主力净流入占比 %
    super_large_net_inflow: float   # 超大单净流入（元）
    super_large_net_inflow_pct: float  # 超大单净流入占比 %

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "net_inflow": self.net_inflow,
                "net_inflow_pct": self.net_inflow_pct,
                "main_net_inflow": self.main_net_inflow,
                "main_net_inflow_pct": self.main_net_inflow_pct,
                "super_large_net_inflow": self.super_large_net_inflow,
                "super_large_net_inflow_pct": self.super_large_net_inflow_pct}
