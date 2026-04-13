"""同花顺涨跌停榜单接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class LimitListProtocol(Protocol):
    def get_limit_list(self, trade_date: str, limit_type: str = "涨停池") -> DataResult: ...


@dataclass
class LimitListEntry:
    symbol: str
    name: str
    trade_date: str
    price: float
    pct_chg: float
    limit_type: str
    open_num: int
    lu_desc: str
    tag: str
    status: str
    limit_order: Optional[float]
    limit_amount: Optional[float]
    turnover_rate: Optional[float]
    limit_up_suc_rate: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "trade_date": self.trade_date,
            "price": self.price,
            "pct_chg": self.pct_chg,
            "limit_type": self.limit_type,
            "open_num": self.open_num,
            "lu_desc": self.lu_desc,
            "tag": self.tag,
            "status": self.status,
            "limit_order": self.limit_order,
            "limit_amount": self.limit_amount,
            "turnover_rate": self.turnover_rate,
            "limit_up_suc_rate": self.limit_up_suc_rate,
        }
