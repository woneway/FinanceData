"""全市场日线行情接口定义（按 trade_date 查询全市场 OHLCV）"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class DailyMarketProtocol(Protocol):
    def get_daily_market(self, trade_date: str) -> DataResult: ...


@dataclass
class DailyMarketBar:
    symbol: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    volume: float
    amount: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "trade_date": self.trade_date,
            "open": self.open, "high": self.high, "low": self.low,
            "close": self.close, "pre_close": self.pre_close,
            "change": self.change, "pct_chg": self.pct_chg,
            "volume": self.volume, "amount": self.amount,
        }
