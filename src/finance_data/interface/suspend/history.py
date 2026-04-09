"""停牌信息 - 接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class SuspendProtocol(Protocol):
    def get_suspend_history(self, date: str) -> DataResult: ...


@dataclass
class SuspendInfo:
    symbol: str
    name: str
    suspend_date: str
    resume_date: str
    suspend_duration: str
    suspend_reason: str
    market: str
    expected_resume_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "suspend_date": self.suspend_date,
            "resume_date": self.resume_date,
            "suspend_duration": self.suspend_duration,
            "suspend_reason": self.suspend_reason,
            "market": self.market,
            "expected_resume_date": self.expected_resume_date,
        }
