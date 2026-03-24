from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MarginSummary:
    """融资融券汇总（市场/交易所维度）"""
    date: str               # YYYYMMDD
    exchange: str            # SSE(上交所) / SZSE(深交所) / BSE(北交所)
    rzye: float             # 融资余额（元）
    rzmre: float            # 融资买入额（元）
    rzche: float            # 融资偿还额（元）
    rqye: float             # 融券余额（元）
    rqmcl: float            # 融券卖出量（股/份/手）
    rzrqye: float           # 融资融券余额（元）
    rqyl: float             # 融券余量（股/份/手）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "exchange": self.exchange,
            "rzye": self.rzye, "rzmre": self.rzmre, "rzche": self.rzche,
            "rqye": self.rqye, "rqmcl": self.rqmcl,
            "rzrqye": self.rzrqye, "rqyl": self.rqyl,
        }


@dataclass
class MarginDetail:
    """融资融券个股明细"""
    date: str               # YYYYMMDD
    symbol: str             # 股票代码
    name: str               # 股票名称
    rzye: float             # 融资余额（元）
    rqye: float             # 融券余额（元）
    rzmre: float            # 融资买入额（元）
    rqyl: float             # 融券余量（股）
    rzche: float            # 融资偿还额（元）
    rqchl: float            # 融券偿还量（股）
    rqmcl: float            # 融券卖出量（股）
    rzrqye: float           # 融资融券余额（元）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "symbol": self.symbol, "name": self.name,
            "rzye": self.rzye, "rqye": self.rqye,
            "rzmre": self.rzmre, "rqyl": self.rqyl,
            "rzche": self.rzche, "rqchl": self.rqchl,
            "rqmcl": self.rqmcl, "rzrqye": self.rzrqye,
        }
