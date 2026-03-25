from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


@dataclass
class StockInfo:
    symbol: str
    name: str
    industry: str
    list_date: str
    area: str = ""
    market: str = ""
    city: str = ""
    exchange: str = ""
    ts_code: str = ""
    full_name: str = ""
    established_date: str = ""
    main_business: str = ""
    introduction: str = ""
    chairman: str = ""
    legal_representative: str = ""
    general_manager: str = ""
    secretary: str = ""
    reg_capital: Optional[float] = None
    staff_num: Optional[int] = None
    website: str = ""
    email: str = ""
    reg_address: str = ""
    actual_controller: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name, "industry": self.industry,
            "list_date": self.list_date, "area": self.area, "market": self.market,
            "city": self.city, "exchange": self.exchange, "ts_code": self.ts_code,
            "full_name": self.full_name, "established_date": self.established_date,
            "main_business": self.main_business, "introduction": self.introduction,
            "chairman": self.chairman, "legal_representative": self.legal_representative,
            "general_manager": self.general_manager, "secretary": self.secretary,
            "reg_capital": self.reg_capital, "staff_num": self.staff_num,
            "website": self.website, "email": self.email,
            "reg_address": self.reg_address, "actual_controller": self.actual_controller,
        }


class StockHistoryProtocol(Protocol):
    def get_stock_info_history(self, symbol: str) -> DataResult: ...
