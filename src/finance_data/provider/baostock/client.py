"""baostock 会话管理

baostock 使用全局 TCP 连接，需要 login/logout。
提供 context manager 确保会话正确释放。

特点：免费、极稳定、无需 token、历史数据完整。
限制：无实时行情、无日频基本面（PE/PB/市值）。
"""
import contextlib
import logging
import threading

import baostock as bs

from finance_data.interface.types import DataFetchError
from finance_data.provider.symbol import normalize

logger = logging.getLogger(__name__)

_lock = threading.Lock()


@contextlib.contextmanager
def baostock_session():
    """线程安全的 baostock 会话 context manager。

    baostock 内部维护全局 TCP 连接，并发调用需串行化。
    """
    with _lock:
        login_result = bs.login()
        if login_result.error_code != "0":
            raise DataFetchError("baostock", "login", login_result.error_msg, "network")
        try:
            yield bs
        finally:
            bs.logout()


def to_baostock(symbol: str) -> str:
    """任意格式 → baostock 格式（sz.000001 / sh.600519）"""
    code, exchange = normalize(symbol)
    return f"{exchange.lower()}.{code}"


def _format_date(date_str: str) -> str:
    """YYYYMMDD → YYYY-MM-DD（baostock 需要连字符格式）"""
    d = date_str.replace("-", "")
    if len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return date_str


def _parse_date(date_str: str) -> str:
    """YYYY-MM-DD → YYYYMMDD（统一为项目内格式）"""
    return date_str.replace("-", "")


def rs_to_list(rs) -> list[list[str]]:
    """将 baostock ResultData 转为二维列表"""
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    return rows
