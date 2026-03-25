from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

ErrorKind = Literal["network", "data", "auth", "quota"]
_VALID_KINDS = {"network", "data", "auth", "quota"}


@dataclass
class DataResult:
    """所有 provider 函数的统一返回类型"""
    data: List[Dict[str, Any]]
    source: str
    meta: Dict[str, Any] = field(default_factory=dict)


class DataFetchError(Exception):
    """数据获取错误"""

    def __init__(self, source: str, func: str, reason: str, kind: str):
        if kind not in _VALID_KINDS:
            raise ValueError(f"kind 必须是 {_VALID_KINDS} 之一，got: {kind!r}")
        self.source = source
        self.func = func
        self.reason = reason
        self.kind = kind
        super().__init__(f"[{source}] {func} 失败 ({kind}): {reason}")
