from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class NorthFlow:
    """北向资金日频资金流"""
    date: str               # YYYYMMDD
    market: str             # 沪股通 / 深股通
    direction: str          # 北向 / 南向
    net_buy: float          # 成交净买额（元）
    net_inflow: float       # 资金净流入（元）
    balance: float          # 当日资金余额（元）
    up_count: int           # 上涨数
    flat_count: int         # 持平数
    down_count: int         # 下跌数
    index_name: str         # 相关指数
    index_pct: float        # 指数涨跌幅 %

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date, "market": self.market, "direction": self.direction,
            "net_buy": self.net_buy, "net_inflow": self.net_inflow,
            "balance": self.balance,
            "up_count": self.up_count, "flat_count": self.flat_count, "down_count": self.down_count,
            "index_name": self.index_name, "index_pct": self.index_pct,
        }


@dataclass
class NorthStockHold:
    """北向资金持股明细"""
    symbol: str             # 股票代码
    name: str              # 股票名称
    date: str              # 日期 YYYYMMDD
    close_price: float     # 今日收盘价
    pct_change: float      # 今日涨跌幅 %
    hold_volume: float     # 持股数量（股）
    hold_market_cap: float # 持股市值（元）
    hold_float_ratio: float # 占流通股比 %
    hold_total_ratio: float # 占总股本比 %
    # 5日增持（akshare 特有字段，tushare 无则填 None）
    increase_5d_volume: float = None   # 5日增持估计-股数
    increase_5d_cap: float = None     # 5日增持估计-市值（元）
    increase_5d_cap_pct: float = None # 5日增持估计-市值增幅 %
    increase_5d_float_ratio: float = None  # 5日增持占流通股比 %
    increase_5d_total_ratio: float = None  # 5日增持占总股本比 %
    board: str = None                    # 所属板块

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "date": self.date,
            "close_price": self.close_price, "pct_change": self.pct_change,
            "hold_volume": self.hold_volume, "hold_market_cap": self.hold_market_cap,
            "hold_float_ratio": self.hold_float_ratio, "hold_total_ratio": self.hold_total_ratio,
            "increase_5d_volume": self.increase_5d_volume,
            "increase_5d_cap": self.increase_5d_cap,
            "increase_5d_cap_pct": self.increase_5d_cap_pct,
            "increase_5d_float_ratio": self.increase_5d_float_ratio,
            "increase_5d_total_ratio": self.increase_5d_total_ratio,
            "board": self.board,
        }
