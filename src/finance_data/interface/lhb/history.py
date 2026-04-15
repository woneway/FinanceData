"""龙虎榜 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional
from typing import Protocol

from finance_data.interface.types import DataResult


class LhbDetailProtocol(Protocol):
    def get_lhb_detail_history(self, start_date: str, end_date: str) -> DataResult: ...


class LhbStockStatProtocol(Protocol):
    def get_lhb_stock_stat_history(self, period: str) -> DataResult: ...


class LhbActiveTradersProtocol(Protocol):
    def get_lhb_active_traders_history(self, start_date: str, end_date: str) -> DataResult: ...


class LhbTraderStatProtocol(Protocol):
    def get_lhb_trader_stat_history(self, period: str) -> DataResult: ...


class LhbStockDetailProtocol(Protocol):
    def get_lhb_stock_detail_history(self, symbol: str, date: str, flag: str) -> DataResult: ...


class LhbInstDetailProtocol(Protocol):
    def get_lhb_inst_detail_history(self, start_date: str, end_date: str) -> DataResult: ...


@dataclass
class LhbEntry:
    symbol: str
    name: str
    date: str
    close: float
    pct_chg: float
    lhb_net_buy: float
    lhb_buy: float
    lhb_sell: float
    lhb_amount: float
    market_amount: float
    net_rate: float
    amount_rate: float
    turnover_rate: float
    float_value: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "close": self.close, "pct_chg": self.pct_chg,
            "lhb_net_buy": self.lhb_net_buy, "lhb_buy": self.lhb_buy,
            "lhb_sell": self.lhb_sell, "lhb_amount": self.lhb_amount,
            "market_amount": self.market_amount,
            "net_rate": self.net_rate, "amount_rate": self.amount_rate,
            "turnover_rate": self.turnover_rate, "float_value": self.float_value,
            "reason": self.reason,
        }


@dataclass
class LhbStockStat:
    symbol: str
    name: str
    last_date: str
    times: int
    lhb_net_buy: float
    lhb_buy: float
    lhb_sell: float
    lhb_amount: float
    inst_buy_times: int
    inst_sell_times: int
    inst_net_buy: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "last_date": self.last_date,
            "times": self.times,
            "lhb_net_buy": self.lhb_net_buy, "lhb_buy": self.lhb_buy,
            "lhb_sell": self.lhb_sell, "lhb_amount": self.lhb_amount,
            "inst_buy_times": self.inst_buy_times,
            "inst_sell_times": self.inst_sell_times,
            "inst_net_buy": self.inst_net_buy,
        }


@dataclass
class LhbActiveTrader:
    branch_name: str
    date: str
    buy_count: int
    sell_count: int
    buy_amount: float
    sell_amount: float
    net_amount: float
    stocks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_name": self.branch_name, "date": self.date,
            "buy_count": self.buy_count, "sell_count": self.sell_count,
            "buy_amount": self.buy_amount, "sell_amount": self.sell_amount,
            "net_amount": self.net_amount, "stocks": self.stocks,
        }


@dataclass
class LhbTraderStat:
    branch_name: str
    lhb_amount: float
    times: int
    buy_amount: float
    buy_times: int
    sell_amount: float
    sell_times: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_name": self.branch_name,
            "lhb_amount": self.lhb_amount, "times": self.times,
            "buy_amount": self.buy_amount, "buy_times": self.buy_times,
            "sell_amount": self.sell_amount, "sell_times": self.sell_times,
        }


@dataclass
class LhbStockDetail:
    symbol: str
    date: str
    flag: str
    branch_name: str
    trade_amount: float
    buy_rate: float
    sell_rate: float
    net_amount: float
    seat_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "flag": self.flag,
            "branch_name": self.branch_name,
            "trade_amount": self.trade_amount, "buy_rate": self.buy_rate,
            "sell_rate": self.sell_rate, "net_amount": self.net_amount,
            "seat_type": self.seat_type,
        }


@dataclass
class LhbInstDetail:
    symbol: str
    name: str
    close: float
    pct_change: float
    inst_buy_count: int
    inst_sell_count: int
    inst_buy_amount: float
    inst_sell_amount: float
    inst_net_buy: float
    market_amount: float
    inst_net_rate: float
    turnover_rate: float
    float_value: float
    reason: str
    date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "close": self.close, "pct_change": self.pct_change,
            "inst_buy_count": self.inst_buy_count, "inst_sell_count": self.inst_sell_count,
            "inst_buy_amount": self.inst_buy_amount, "inst_sell_amount": self.inst_sell_amount,
            "inst_net_buy": self.inst_net_buy, "market_amount": self.market_amount,
            "inst_net_rate": self.inst_net_rate, "turnover_rate": self.turnover_rate,
            "float_value": self.float_value, "reason": self.reason, "date": self.date,
        }
