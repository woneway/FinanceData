"""股票池 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class ZtPoolProtocol(Protocol):
    def get_zt_pool_history(self, date: str) -> DataResult: ...


class StrongStocksProtocol(Protocol):
    def get_strong_stocks_history(self, date: str) -> DataResult: ...


class PreviousZtProtocol(Protocol):
    def get_previous_zt_history(self, date: str) -> DataResult: ...


class ZbgcPoolProtocol(Protocol):
    def get_zbgc_pool_history(self, date: str) -> DataResult: ...


@dataclass
class ZtPoolEntry:
    symbol: str
    name: str
    pct_change: float
    price: float
    amount: float
    float_mv: float
    total_mv: float
    turnover: float
    seal_amount: float
    first_seal_time: str
    last_seal_time: str
    open_times: int
    continuous_days: int
    industry: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "pct_change": self.pct_change, "price": self.price,
            "amount": self.amount, "float_mv": self.float_mv,
            "total_mv": self.total_mv, "turnover": self.turnover,
            "seal_amount": self.seal_amount,
            "first_seal_time": self.first_seal_time,
            "last_seal_time": self.last_seal_time,
            "open_times": self.open_times,
            "continuous_days": self.continuous_days,
            "industry": self.industry,
        }


@dataclass
class StrongStockEntry:
    symbol: str
    name: str
    pct_change: float
    price: float
    limit_price: float
    amount: float
    float_mv: float
    total_mv: float
    turnover: float
    volume_ratio: float
    is_new_high: bool
    reason: str
    industry: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "pct_change": self.pct_change, "price": self.price,
            "limit_price": self.limit_price, "amount": self.amount,
            "float_mv": self.float_mv, "total_mv": self.total_mv,
            "turnover": self.turnover, "volume_ratio": self.volume_ratio,
            "is_new_high": self.is_new_high, "reason": self.reason,
            "industry": self.industry,
        }


@dataclass
class PreviousZtEntry:
    symbol: str
    name: str
    pct_change: float
    price: float
    limit_price: float
    amount: float
    float_mv: float
    total_mv: float
    turnover: float
    prev_seal_time: str
    prev_continuous_days: int
    industry: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "pct_change": self.pct_change, "price": self.price,
            "limit_price": self.limit_price, "amount": self.amount,
            "float_mv": self.float_mv, "total_mv": self.total_mv,
            "turnover": self.turnover,
            "prev_seal_time": self.prev_seal_time,
            "prev_continuous_days": self.prev_continuous_days,
            "industry": self.industry,
        }


@dataclass
class ZbgcEntry:
    symbol: str
    name: str
    pct_change: float
    price: float
    limit_price: float
    amount: float
    float_mv: float
    total_mv: float
    turnover: float
    first_seal_time: str
    open_times: int
    amplitude: float
    industry: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "pct_change": self.pct_change, "price": self.price,
            "limit_price": self.limit_price, "amount": self.amount,
            "float_mv": self.float_mv, "total_mv": self.total_mv,
            "turnover": self.turnover,
            "first_seal_time": self.first_seal_time,
            "open_times": self.open_times, "amplitude": self.amplitude,
            "industry": self.industry,
        }
