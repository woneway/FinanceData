from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


@dataclass
class StockInfo:
    symbol: str
    name: str
    industry: str
    list_date: str
    exchange: str = ""
    full_name: str = ""
    established_date: str = ""
    chairman: str = ""
    general_manager: str = ""
    secretary: str = ""
    reg_capital: Optional[float] = None
    staff_num: Optional[int] = None
    website: str = ""
    email: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "industry": self.industry,
            "list_date": self.list_date, "exchange": self.exchange,
            "full_name": self.full_name,
            "established_date": self.established_date,
            "chairman": self.chairman,
            "general_manager": self.general_manager, "secretary": self.secretary,
            "reg_capital": self.reg_capital, "staff_num": self.staff_num,
            "website": self.website, "email": self.email,
        }


class StockHistoryProtocol(Protocol):
    def get_stock_info_history(self, symbol: str) -> DataResult: ...
