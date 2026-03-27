"""大盘指数历史 K线 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.index.history import IndexBar
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import get_session, has_login_cookie, refresh_session
from finance_data.provider.symbol import to_xueqiu_index

logger = logging.getLogger(__name__)

_KLINE_URL = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _to_xueqiu_index(symbol: str) -> str:
    """将指数代码转为雪球格式: 000001.SH → SH000001"""
    return to_xueqiu_index(symbol)


def _date_to_ts(date_str: str) -> int:
    s = date_str.replace("-", "")[:8]
    dt = datetime.datetime.strptime(s, "%Y%m%d")
    dt = dt.replace(hour=15, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return int(dt.timestamp() * 1000)


def _ts_to_date(ts_ms: int | float) -> str:
    dt = datetime.datetime.fromtimestamp(
        ts_ms / 1000, tz=datetime.timezone(datetime.timedelta(hours=8))
    )
    return dt.strftime("%Y%m%d")


class XueqiuIndexHistory:
    """雪球指数历史 K 线 provider（需要登录 cookie）"""

    def get_index_history(self, symbol: str, start: str, end: str) -> DataResult:
        if not has_login_cookie():
            raise DataFetchError(
                "xueqiu", "kline",
                "XUEQIU_COOKIE 未设置，无法获取指数 K 线数据",
                "auth",
            )

        xq_symbol = _to_xueqiu_index(symbol)
        session = get_session()

        items = self._request(session, xq_symbol, start, end)
        if items is None:
            session = refresh_session()
            items = self._request(session, xq_symbol, start, end)

        if not items:
            raise DataFetchError(
                "xueqiu", "kline",
                f"无数据: {symbol} {start}-{end}", "data"
            )

        bars = self._parse(symbol, items, start=start, end=end)
        return DataResult(
            data=bars,
            source="xueqiu",
            meta={"rows": len(bars), "symbol": symbol, "upstream": "xueqiu"},
        )

    def _request(
        self, session: requests.Session, xq_symbol: str, start: str, end: str
    ) -> list | None:
        end_ts = _date_to_ts(end)
        params = {
            "symbol": xq_symbol,
            "begin": end_ts,
            "period": "day",
            "type": "before",
            "count": -284,
            "indicator": "kline",
        }

        try:
            resp = session.get(_KLINE_URL, params=params, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 400:
                raise DataFetchError(
                    "xueqiu", "kline", "cookie 无效或已过期", "auth"
                ) from e
            raise DataFetchError(
                "xueqiu", "kline", str(e), "network"
            ) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "xueqiu", "kline", str(e), "network"
            ) from e
        except Exception as e:
            raise DataFetchError(
                "xueqiu", "kline", str(e), "data"
            ) from e

        data = body.get("data", {})
        columns = data.get("column", [])
        items = data.get("item", [])

        if not columns or not items:
            return None

        return [dict(zip(columns, row)) for row in items]

    def _parse(self, symbol: str, items: list[dict],
               start: str = "", end: str = "") -> list[dict]:
        bars = []
        for d in items:
            ts_ms = d.get("timestamp")
            if ts_ms is None:
                continue
            date = _ts_to_date(ts_ms)
            if start and date < start:
                continue
            if end and date > end:
                continue
            bars.append(
                IndexBar(
                    symbol=symbol,
                    date=date,
                    open=float(d.get("open", 0) or 0),
                    high=float(d.get("high", 0) or 0),
                    low=float(d.get("low", 0) or 0),
                    close=float(d.get("close", 0) or 0),
                    volume=float(d.get("volume", 0) or 0),
                    amount=float(d.get("amount", 0) or 0),
                    pct_chg=float(d.get("percent", 0) or 0),
                ).to_dict()
            )
        bars.sort(key=lambda b: b["date"])
        return bars
