"""财务基本面接口定义"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class FinancialSummaryProtocol(Protocol):
    def get_financial_summary_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult: ...


class DividendProtocol(Protocol):
    def get_dividend_history(self, symbol: str) -> DataResult: ...


class EarningsForecastProtocol(Protocol):
    def get_earnings_forecast_history(self, symbol: str) -> DataResult: ...


@dataclass
class FinancialSummary:
    symbol: str
    period: str
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    cash_flow: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "revenue": self.revenue, "net_profit": self.net_profit,
                "roe": self.roe}


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
    forecast_type: str
    net_profit_min: Optional[float] = None
    net_profit_max: Optional[float] = None
    change_low: Optional[float] = None
    change_high: Optional[float] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "forecast_type": self.forecast_type,
                "net_profit_min": self.net_profit_min,
                "net_profit_max": self.net_profit_max,
                "change_low": self.change_low,
                "change_high": self.change_high,
                "summary": self.summary}
