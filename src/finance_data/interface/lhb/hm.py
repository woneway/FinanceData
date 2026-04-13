"""游资名录与明细接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class HmListProtocol(Protocol):
    def get_hm_list(self) -> DataResult: ...


class HmDetailProtocol(Protocol):
    def get_hm_detail(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
        hm_name: str = "",
    ) -> DataResult: ...


@dataclass
class HmEntry:
    name: str
    desc: str
    orgs: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "desc": self.desc, "orgs": self.orgs}


@dataclass
class HmDetailEntry:
    trade_date: str
    symbol: str
    name: str
    buy_amount: float
    sell_amount: float
    net_amount: float
    hm_name: str
    hm_orgs: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "name": self.name,
            "buy_amount": self.buy_amount,
            "sell_amount": self.sell_amount,
            "net_amount": self.net_amount,
            "hm_name": self.hm_name,
            "hm_orgs": self.hm_orgs,
        }
