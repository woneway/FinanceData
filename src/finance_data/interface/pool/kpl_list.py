"""开盘啦榜单接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class KplListProtocol(Protocol):
    def get_kpl_list(self, trade_date: str, tag: str = "涨停") -> DataResult: ...


@dataclass
class KplListEntry:
    symbol: str
    name: str
    trade_date: str
    pct_chg: float
    tag: str
    theme: str
    status: str
    lu_time: str
    lu_desc: str
    amount: Optional[float]
    turnover_rate: Optional[float]
    limit_order: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "trade_date": self.trade_date,
            "pct_chg": self.pct_chg,
            "tag": self.tag,
            "theme": self.theme,
            "status": self.status,
            "lu_time": self.lu_time,
            "lu_desc": self.lu_desc,
            "amount": self.amount,
            "turnover_rate": self.turnover_rate,
            "limit_order": self.limit_order,
        }
