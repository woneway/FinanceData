from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ZtPoolEntry:
    """涨停股池记录"""
    symbol: str
    name: str
    pct_change: float       # 涨跌幅 %
    price: float            # 最新价
    amount: float           # 成交额（元）
    float_mv: float         # 流通市值（元）
    total_mv: float         # 总市值（元）
    turnover: float         # 换手率 %
    seal_amount: float      # 封板资金（元）
    first_seal_time: str    # 首次封板时间 HHMMSS
    last_seal_time: str     # 最后封板时间 HHMMSS
    open_times: int         # 炸板次数
    continuous_days: int    # 连板数
    industry: str           # 所属行业

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
    """强势股池记录"""
    symbol: str
    name: str
    pct_change: float       # 涨跌幅 %
    price: float
    limit_price: float      # 涨停价
    amount: float           # 成交额（元）
    float_mv: float         # 流通市值（元）
    total_mv: float         # 总市值（元）
    turnover: float         # 换手率 %
    volume_ratio: float     # 量比
    is_new_high: bool       # 是否创新高
    reason: str             # 入选理由
    industry: str           # 所属行业

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
    """昨日涨停今日数据记录"""
    symbol: str
    name: str
    pct_change: float       # 今日涨跌幅 %
    price: float            # 今日最新价
    limit_price: float      # 昨日涨停价
    amount: float           # 今日成交额（元）
    float_mv: float
    total_mv: float
    turnover: float
    prev_seal_time: str     # 昨日封板时间 HHMMSS
    prev_continuous_days: int  # 昨日连板数
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
    """炸板股池记录"""
    symbol: str
    name: str
    pct_change: float
    price: float
    limit_price: float      # 涨停价
    amount: float
    float_mv: float
    total_mv: float
    turnover: float
    first_seal_time: str    # 首次封板时间
    open_times: int         # 炸板次数
    amplitude: float        # 振幅 %
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
