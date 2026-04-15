"""大盘资金流向 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class MarketMoneyflowProtocol(Protocol):
    def get_market_moneyflow(
        self,
        trade_date: str,
        start_date: str,
        end_date: str,
    ) -> DataResult: ...


@dataclass
class MarketMoneyflowRow:
    trade_date: str
    close_sh: float
    pct_change_sh: float
    close_sz: float
    pct_change_sz: float
    net_amount: float
    net_amount_rate: float
    buy_lg_amount: float
    buy_lg_amount_rate: float
    buy_md_amount: float
    buy_md_amount_rate: float
    buy_sm_amount: float
    buy_sm_amount_rate: float
    buy_elg_amount: float
    buy_elg_amount_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "close_sh": self.close_sh, "pct_change_sh": self.pct_change_sh,
            "close_sz": self.close_sz, "pct_change_sz": self.pct_change_sz,
            "net_amount": self.net_amount, "net_amount_rate": self.net_amount_rate,
            "buy_lg_amount": self.buy_lg_amount,
            "buy_lg_amount_rate": self.buy_lg_amount_rate,
            "buy_md_amount": self.buy_md_amount,
            "buy_md_amount_rate": self.buy_md_amount_rate,
            "buy_sm_amount": self.buy_sm_amount,
            "buy_sm_amount_rate": self.buy_sm_amount_rate,
            "buy_elg_amount": self.buy_elg_amount,
            "buy_elg_amount_rate": self.buy_elg_amount_rate,
        }
