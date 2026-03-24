from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SectorFundFlow:
    """板块资金流"""
    rank: int              # 序号
    name: str              # 板块名称
    pct_change: float     # 今日涨跌幅 %
    main_net_inflow: float       # 今日主力净流入（元）
    main_net_inflow_pct: float   # 今日主力净流入净占比 %
    super_large_net_inflow: float  # 今日超大单净流入（元）
    super_large_net_inflow_pct: float
    large_net_inflow: float       # 今日大单净流入（元）
    large_net_inflow_pct: float
    medium_net_inflow: float      # 今日中单净流入（元）
    medium_net_inflow_pct: float
    small_net_inflow: float       # 今日小单净流入（元）
    small_net_inflow_pct: float
    top_stock: str        # 今日主力净流入最大股

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank, "name": self.name,
            "pct_change": self.pct_change,
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
