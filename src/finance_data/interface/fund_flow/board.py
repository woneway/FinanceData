"""东财板块资金流向 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class BoardMoneyflowProtocol(Protocol):
    def get_board_moneyflow(
        self,
        trade_date: str,
        start_date: str,
        end_date: str,
        ts_code: str,
        content_type: str,
    ) -> DataResult: ...


@dataclass
class BoardMoneyflowRow:
    trade_date: str
    ts_code: str
    name: str
    content_type: str
    pct_chg: float
    close: float
    net_amount: float
    net_amount_rate: float
    buy_elg_amount: float
    buy_elg_amount_rate: float
    buy_lg_amount: float
    buy_lg_amount_rate: float
    buy_md_amount: float
    buy_md_amount_rate: float
    buy_sm_amount: float
    buy_sm_amount_rate: float
    buy_sm_amount_stock: str
    rank: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_date": self.trade_date, "ts_code": self.ts_code,
            "name": self.name, "content_type": self.content_type,
            "pct_chg": self.pct_chg, "close": self.close,
            "net_amount": self.net_amount, "net_amount_rate": self.net_amount_rate,
            "buy_elg_amount": self.buy_elg_amount,
            "buy_elg_amount_rate": self.buy_elg_amount_rate,
            "buy_lg_amount": self.buy_lg_amount,
            "buy_lg_amount_rate": self.buy_lg_amount_rate,
            "buy_md_amount": self.buy_md_amount,
            "buy_md_amount_rate": self.buy_md_amount_rate,
            "buy_sm_amount": self.buy_sm_amount,
            "buy_sm_amount_rate": self.buy_sm_amount_rate,
            "buy_sm_amount_stock": self.buy_sm_amount_stock,
            "rank": self.rank,
        }
