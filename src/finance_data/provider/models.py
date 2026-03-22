from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class StockInfo:
    """所有 provider 的个股信息统一输出格式"""
    symbol: str
    name: str
    industry: str
    list_date: str
    area: str = ""
    market: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "industry": self.industry,
            "list_date": self.list_date,
            "area": self.area,
            "market": self.market,
        }
