from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class FundFlow:
    symbol: str
    date: str
    net_inflow: float       # 净流入（元）
    net_inflow_pct: float   # 净流入占比 %
    main_inflow: float      # 主力净流入
    main_inflow_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "net_inflow": self.net_inflow,
                "net_inflow_pct": self.net_inflow_pct,
                "main_inflow": self.main_inflow,
                "main_inflow_pct": self.main_inflow_pct}
