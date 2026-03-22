from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LhbEntry:
    """龙虎榜每日上榜记录"""
    symbol: str
    name: str
    date: str               # YYYYMMDD
    close: float
    pct_change: float       # %
    lhb_net_buy: float      # 龙虎榜净买额（元）
    lhb_buy: float          # 龙虎榜买入额（元）
    lhb_sell: float         # 龙虎榜卖出额（元）
    lhb_amount: float       # 龙虎榜成交额（元）
    market_amount: float    # 市场总成交额（元）
    net_rate: float         # 净买额占总成交比 %
    amount_rate: float      # 成交额占总成交比 %
    turnover_rate: float    # 换手率 %
    float_value: float      # 流通市值（元）
    reason: str             # 上榜原因

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "close": self.close, "pct_change": self.pct_change,
            "lhb_net_buy": self.lhb_net_buy, "lhb_buy": self.lhb_buy,
            "lhb_sell": self.lhb_sell, "lhb_amount": self.lhb_amount,
            "market_amount": self.market_amount,
            "net_rate": self.net_rate, "amount_rate": self.amount_rate,
            "turnover_rate": self.turnover_rate, "float_value": self.float_value,
            "reason": self.reason,
        }


@dataclass
class LhbStockStat:
    """个股上榜统计"""
    symbol: str
    name: str
    last_date: str          # 最近上榜日 YYYYMMDD
    times: int              # 上榜次数
    lhb_net_buy: float      # 龙虎榜净买额（元）
    lhb_buy: float
    lhb_sell: float
    lhb_amount: float       # 龙虎榜总成交额（元）
    inst_buy_times: int     # 买方机构次数
    inst_sell_times: int    # 卖方机构次数
    inst_net_buy: float     # 机构净买额（元）

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
    """每日活跃营业部（游资席位）"""
    branch_name: str
    date: str               # YYYYMMDD
    buy_count: int          # 买入个股数
    sell_count: int         # 卖出个股数
    buy_amount: float       # 买入总金额（元）
    sell_amount: float      # 卖出总金额（元）
    net_amount: float       # 总买卖净额（元）
    stocks: str             # 买入股票列表（空格分隔）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_name": self.branch_name, "date": self.date,
            "buy_count": self.buy_count, "sell_count": self.sell_count,
            "buy_amount": self.buy_amount, "sell_amount": self.sell_amount,
            "net_amount": self.net_amount, "stocks": self.stocks,
        }


@dataclass
class LhbTraderStat:
    """营业部统计（游资战绩）"""
    branch_name: str
    lhb_amount: float       # 龙虎榜成交金额（元）
    times: int              # 上榜次数
    buy_amount: float       # 买入额（元）
    buy_times: int
    sell_amount: float      # 卖出额（元）
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
    """个股龙虎榜席位明细"""
    symbol: str
    date: str               # YYYYMMDD
    flag: str               # 买入 / 卖出
    branch_name: str        # 交易营业部名称
    trade_amount: float     # 交易金额（元）：flag=买入时为买入金额，flag=卖出时为卖出金额
    buy_rate: float         # 买入金额占总成交比例 %
    sell_rate: float        # 卖出金额占总成交比例 %
    net_amount: float       # 净额（元）
    seat_type: str          # 类型（席位类型/上榜原因）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "flag": self.flag,
            "branch_name": self.branch_name,
            "trade_amount": self.trade_amount, "buy_rate": self.buy_rate,
            "sell_rate": self.sell_rate, "net_amount": self.net_amount,
            "seat_type": self.seat_type,
        }
