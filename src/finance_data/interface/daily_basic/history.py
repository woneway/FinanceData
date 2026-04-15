"""日频基本面接口定义（PE/PB/市值/换手率/量比）"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class DailyBasicProtocol(Protocol):
    def get_daily_basic(self, symbol: str) -> DataResult: ...


@dataclass
class DailyBasic:
    symbol: str
    name: str
    date: str
    pe: float
    pb: float
    market_cap: float         # 总市值（元）
    circ_market_cap: float    # 流通市值（元）
    turnover_rate: float      # 换手率 %
    volume_ratio: float       # 量比

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "pe": self.pe, "pb": self.pb,
            "market_cap": self.market_cap,
            "circ_market_cap": self.circ_market_cap,
            "turnover_rate": self.turnover_rate,
            "volume_ratio": self.volume_ratio,
        }


class DailyBasicMarketProtocol(Protocol):
    def get_daily_basic_market(self, trade_date: str) -> DataResult: ...


@dataclass
class DailyBasicMarket:
    symbol: str
    trade_date: str
    close: float
    turnover_rate: float
    turnover_rate_f: float
    volume_ratio: float
    pe_ttm: float
    pb: float
    total_mv: float
    circ_mv: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "trade_date": self.trade_date,
            "close": self.close,
            "turnover_rate": self.turnover_rate,
            "turnover_rate_f": self.turnover_rate_f,
            "volume_ratio": self.volume_ratio,
            "pe_ttm": self.pe_ttm, "pb": self.pb,
            "total_mv": self.total_mv, "circ_mv": self.circ_mv,
        }
