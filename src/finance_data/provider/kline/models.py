from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class KlineBar:
    symbol: str
    date: str       # YYYYMMDD
    period: str     # daily/weekly/monthly/1min/5min/15min/30min/60min
    open: float
    high: float
    low: float
    close: float
    volume: float   # 手
    amount: float   # 元
    pct_chg: float  # 涨跌幅 %
    adj: str        # qfq/hfq/none

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "period": self.period,
            "open": self.open, "high": self.high, "low": self.low,
            "close": self.close, "volume": self.volume, "amount": self.amount,
            "pct_chg": self.pct_chg, "adj": self.adj,
        }
