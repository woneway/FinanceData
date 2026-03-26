"""融资融券个股明细 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.margin.history import MarginDetail
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    refresh_session,
)

logger = logging.getLogger(__name__)

_MARGIN_URL = "https://stock.xueqiu.com/v5/stock/capital/margin.json"
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


class XueqiuMarginDetail:
    """雪球融资融券个股明细 provider

    仅支持个股查询（需传入 ts_code）。
    不支持按日期查询全市场数据。
    """

    def get_margin_detail_history(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        ts_code: str = "",
    ) -> DataResult:
        if not ts_code:
            raise DataFetchError(
                "xueqiu", "margin", "雪球融资融券仅支持个股查询，需提供 ts_code", "data"
            )

        # ts_code 可能是 "000001" 或 "000001.SZ"
        symbol = ts_code.split(".")[0] if "." in ts_code else ts_code
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "margin", f"无法获取融资融券数据: {symbol}", "data"
            )

        rows = [self._parse(symbol, item) for item in data]
        rows = [r for r in rows if r is not None]

        # 按日期过滤
        if trade_date:
            rows = [r for r in rows if r.date == trade_date]
        elif start_date or end_date:
            if start_date:
                rows = [r for r in rows if r.date >= start_date]
            if end_date:
                rows = [r for r in rows if r.date <= end_date]

        if not rows:
            raise DataFetchError(
                "xueqiu", "margin", f"无有效融资融券数据: {symbol}", "data"
            )

        return DataResult(
            data=[r.to_dict() for r in rows],
            source="xueqiu",
            meta={"rows": len(rows), "symbol": symbol},
        )

    def _request(
        self, session: requests.Session, xq_symbol: str,
    ) -> list | None:
        try:
            resp = session.get(
                _MARGIN_URL,
                params={"symbol": xq_symbol, "count": "30"},
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError("xueqiu", "margin", str(e), kind) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError("xueqiu", "margin", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("xueqiu", "margin", str(e), "data") from e

        items = body.get("data", {}).get("items")
        if not items:
            return None
        return items

    def _parse(self, symbol: str, item: dict) -> MarginDetail | None:
        date = _ms_to_date(item.get("td_date"))
        if not date:
            return None

        rzye = item.get("margin_trading_balance") or 0.0
        rqye = item.get("short_selling_amt_balance") or 0.0
        rzmre = item.get("margin_trading_buy_amt") or 0.0
        net_buy = item.get("margin_trading_net_buy_amt") or 0.0
        rzrqye = item.get("margin_trading_amt_balance") or 0.0

        # 融资偿还额 = 融资买入额 - 融资净买入额
        rzche = rzmre - net_buy if rzmre and net_buy else 0.0

        return MarginDetail(
            date=date,
            symbol=symbol,
            name="",  # 雪球此 API 不返回股票名称
            rzye=rzye,
            rqye=rqye,
            rzmre=rzmre,
            rqyl=0.0,  # 雪球不提供融券余量
            rzche=rzche,
            rqchl=0.0,  # 雪球不提供融券偿还量
            rqmcl=0.0,  # 雪球不提供融券卖出量
            rzrqye=rzrqye,
        )
