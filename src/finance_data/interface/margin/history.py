"""融资融券 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class MarginProtocol(Protocol):
    def get_margin_history(
        self,
        trade_date: str,
        start_date: str,
        end_date: str,
        exchange_id: str,
    ) -> DataResult: ...


class MarginDetailProtocol(Protocol):
    def get_margin_detail_history(
        self,
        trade_date: str,
        start_date: str,
        end_date: str,
        ts_code: str,
    ) -> DataResult: ...


@dataclass
class MarginSummary:
    date: str
    exchange: str
    rzye: float
    rzmre: float
    rzche: float
    rqye: float
    rqmcl: float
    rzrqye: float
    rqyl: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "exchange": self.exchange,
            "rzye": self.rzye, "rzmre": self.rzmre, "rzche": self.rzche,
            "rqye": self.rqye, "rqmcl": self.rqmcl,
            "rzrqye": self.rzrqye, "rqyl": self.rqyl,
        }


@dataclass
class MarginDetail:
    date: str
    symbol: str
    name: str
    rzye: float
    rqye: float
    rzmre: float
    rqyl: float
    rzche: float
    rqchl: float
    rqmcl: float
    rzrqye: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "symbol": self.symbol, "name": self.name,
            "rzye": self.rzye, "rqye": self.rqye, "rzmre": self.rzmre,
            "rqyl": self.rqyl, "rzche": self.rzche, "rqchl": self.rqchl,
            "rqmcl": self.rqmcl, "rzrqye": self.rzrqye,
        }
