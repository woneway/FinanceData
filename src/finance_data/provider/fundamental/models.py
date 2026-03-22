from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class FinancialSummary:
    symbol: str
    period: str             # YYYYMMDD 报告期
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    cash_flow: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "revenue": self.revenue, "net_profit": self.net_profit,
                "roe": self.roe, "gross_margin": self.gross_margin,
                "cash_flow": self.cash_flow}


@dataclass
class DividendRecord:
    symbol: str
    ex_date: str
    per_share: float
    record_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "ex_date": self.ex_date,
                "per_share": self.per_share, "record_date": self.record_date}


@dataclass
class EarningsForecast:
    symbol: str
    period: str
    forecast_type: str      # 预增/预减/扭亏/首亏/续盈/续亏/略增/略减
    change_low: Optional[float] = None
    change_high: Optional[float] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "forecast_type": self.forecast_type,
                "change_low": self.change_low,
                "change_high": self.change_high,
                "summary": self.summary}
