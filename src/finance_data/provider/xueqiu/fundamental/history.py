"""财务摘要 + 分红记录 - 雪球实现"""
import datetime
import logging
import re

import requests

from finance_data.interface.fundamental.history import (
    DividendRecord,
    FinancialSummary,
)
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    refresh_session,
)

logger = logging.getLogger(__name__)

_INDICATOR_URL = "https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json"
_BONUS_URL = "https://stock.xueqiu.com/v5/stock/f10/cn/bonus.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


_CN_TZ = datetime.timezone(datetime.timedelta(hours=8))


def _ms_to_date(val) -> str:
    """Convert millisecond timestamp to YYYYMMDD string (UTC+8)."""
    if val is None:
        return ""
    try:
        ts = float(val) / 1000
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        return dt.astimezone(_CN_TZ).strftime("%Y%m%d")
    except (TypeError, ValueError, OSError):
        return ""


def _extract_value(arr) -> float | None:
    """Extract first element from [value, yoy_change] array."""
    if arr is None:
        return None
    if isinstance(arr, (list, tuple)) and len(arr) > 0:
        v = arr[0]
        if v is None:
            return None
        try:
            f = float(v)
            return None if f != f else f
        except (TypeError, ValueError):
            return None
    try:
        f = float(arr)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 财务摘要
# ---------------------------------------------------------------------------

class XueqiuFinancialSummary:
    """雪球财务摘要 provider（无需登录 cookie）"""

    def get_financial_summary_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "indicator", f"无法获取财务摘要: {symbol}", "data"
            )

        rows = [self._parse(symbol, item) for item in data]
        rows = [r for r in rows if r is not None]
        if not rows:
            raise DataFetchError(
                "xueqiu", "indicator", f"无有效财务数据: {symbol}", "data"
            )

        dicts = [r.to_dict() for r in rows]
        if start_date or end_date:
            dicts = [d for d in dicts if
                     (not start_date or d.get("period", "") >= start_date) and
                     (not end_date or d.get("period", "") <= end_date)]

        return DataResult(
            data=dicts,
            source="xueqiu",
            meta={"rows": len(dicts), "symbol": symbol},
        )

    def _request(
        self, session: requests.Session, xq_symbol: str,
    ) -> list | None:
        try:
            resp = session.get(
                _INDICATOR_URL,
                params={
                    "symbol": xq_symbol,
                    "type": "Q4",
                    "is_detail": "true",
                    "count": "20",
                },
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError("xueqiu", "indicator", str(e), kind) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError("xueqiu", "indicator", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("xueqiu", "indicator", str(e), "data") from e

        items = body.get("data", {}).get("list")
        if not items:
            return None
        return items

    def _parse(self, symbol: str, item: dict) -> FinancialSummary | None:
        period = _ms_to_date(item.get("report_date"))
        if not period:
            return None

        return FinancialSummary(
            symbol=symbol,
            period=period,
            revenue=_extract_value(item.get("total_revenue")),
            net_profit=_extract_value(item.get("net_profit_atsopc")),
            roe=_extract_value(item.get("avg_roe")),
            gross_margin=_extract_value(item.get("gross_selling_rate")),
            cash_flow=None,  # indicator API 仅有每股值，无总额
        )


# ---------------------------------------------------------------------------
# 分红记录
# ---------------------------------------------------------------------------

_DIVIDEND_RE = re.compile(r"(\d+)派([\d.]+)元")


class XueqiuDividend:
    """雪球分红记录 provider（无需登录 cookie）"""

    def get_dividend_history(self, symbol: str) -> DataResult:
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "bonus", f"无法获取分红记录: {symbol}", "data"
            )

        rows = [self._parse(symbol, item) for item in data]
        rows = [r for r in rows if r is not None]
        if not rows:
            raise DataFetchError(
                "xueqiu", "bonus", f"无有效分红记录: {symbol}", "data"
            )

        return DataResult(
            data=[r.to_dict() for r in rows],
            source="xueqiu",
            meta={"rows": len(rows), "symbol": symbol},
        )

    def _request(self, session: requests.Session, xq_symbol: str) -> list | None:
        try:
            resp = session.get(
                _BONUS_URL,
                params={"symbol": xq_symbol, "size": "50", "page": "1"},
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError("xueqiu", "bonus", str(e), kind) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError("xueqiu", "bonus", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("xueqiu", "bonus", str(e), "data") from e

        items = body.get("data", {}).get("items")
        if not items:
            return None
        return items

    def _parse(self, symbol: str, item: dict) -> DividendRecord | None:
        ex_date = _ms_to_date(item.get("ashare_ex_dividend_date"))
        if not ex_date:
            return None  # 跳过未实施的预案

        record_date = _ms_to_date(item.get("equity_date"))

        plan = str(item.get("plan_explain", ""))
        m = _DIVIDEND_RE.search(plan)
        if m:
            base = float(m.group(1))
            amount = float(m.group(2))
            per_share = amount / base if base > 0 else 0.0
        else:
            per_share = 0.0

        return DividendRecord(
            symbol=symbol,
            ex_date=ex_date,
            per_share=round(per_share, 4),
            record_date=record_date,
        )
