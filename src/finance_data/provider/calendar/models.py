from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TradeDate:
    date: str       # YYYYMMDD
    is_open: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "is_open": self.is_open}
