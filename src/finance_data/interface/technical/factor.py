"""股票技术面因子 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class StockFactorProtocol(Protocol):
    def get_stock_factor(
        self,
        ts_code: str,
        trade_date: str,
        start_date: str,
        end_date: str,
    ) -> DataResult: ...


@dataclass
class StockFactor:
    trade_date: str
    symbol: str
    close: float
    open: float
    high: float
    low: float
    pre_close: float
    change: float
    pct_chg: float
    volume: float
    amount: float
    turnover_rate: float
    turnover_rate_f: float
    volume_ratio: float
    pe: float
    pe_ttm: float
    pb: float
    ps: float
    ps_ttm: float
    total_share: float
    float_share: float
    free_share: float
    total_mv: float
    circ_mv: float
    dv_ratio: float
    dv_ttm: float
    free_mv: float
    ma5: float
    ma10: float
    ma20: float
    ma30: float
    ma60: float
    ma90: float
    ma250: float
    macd_dif: float
    macd_dea: float
    macd: float
    kdj_k: float
    kdj_d: float
    kdj_j: float
    rsi_6: float
    rsi_12: float
    rsi_24: float
    boll_upper: float
    boll_mid: float
    boll_lower: float
    cci: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_date": self.trade_date, "symbol": self.symbol,
            "close": self.close, "open": self.open,
            "high": self.high, "low": self.low,
            "pre_close": self.pre_close, "change": self.change,
            "pct_chg": self.pct_chg, "volume": self.volume,
            "amount": self.amount, "turnover_rate": self.turnover_rate,
            "turnover_rate_f": self.turnover_rate_f,
            "volume_ratio": self.volume_ratio,
            "pe": self.pe, "pe_ttm": self.pe_ttm,
            "pb": self.pb, "ps": self.ps, "ps_ttm": self.ps_ttm,
            "total_share": self.total_share, "float_share": self.float_share,
            "free_share": self.free_share, "total_mv": self.total_mv,
            "circ_mv": self.circ_mv, "dv_ratio": self.dv_ratio,
            "dv_ttm": self.dv_ttm, "free_mv": self.free_mv,
            "ma5": self.ma5, "ma10": self.ma10, "ma20": self.ma20,
            "ma30": self.ma30, "ma60": self.ma60,
            "ma90": self.ma90, "ma250": self.ma250,
            "macd_dif": self.macd_dif, "macd_dea": self.macd_dea,
            "macd": self.macd, "kdj_k": self.kdj_k, "kdj_d": self.kdj_d,
            "kdj_j": self.kdj_j, "rsi_6": self.rsi_6,
            "rsi_12": self.rsi_12, "rsi_24": self.rsi_24,
            "boll_upper": self.boll_upper, "boll_mid": self.boll_mid,
            "boll_lower": self.boll_lower, "cci": self.cci,
        }
