"""K线历史数据 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    has_login_cookie,
    refresh_session,
)

logger = logging.getLogger(__name__)

_KLINE_URL = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

# 雪球 period 参数映射
_PERIOD_MAP = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
}


def _date_to_ts(date_str: str) -> int:
    """YYYYMMDD → 毫秒时间戳"""
    s = date_str.replace("-", "")[:8]
    dt = datetime.datetime.strptime(s, "%Y%m%d")
    dt = dt.replace(hour=15, tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
    return int(dt.timestamp() * 1000)


def _ts_to_date(ts_ms: int | float) -> str:
    """毫秒时间戳 → YYYYMMDD"""
    dt = datetime.datetime.fromtimestamp(
        ts_ms / 1000, tz=datetime.timezone(datetime.timedelta(hours=8))
    )
    return dt.strftime("%Y%m%d")


class XueqiuKlineHistory:
    """雪球 K 线 provider（需要登录 cookie）"""

    def get_kline_history(
        self,
        symbol: str,
        period: str,
        start: str,
        end: str,
        adj: str = "qfq",
    ) -> DataResult:
        if not has_login_cookie():
            raise DataFetchError(
                "xueqiu",
                "kline",
                "XUEQIU_COOKIE 未设置，无法获取 K 线数据",
                "auth",
            )

        xq_period = _PERIOD_MAP.get(period)
        if xq_period is None:
            raise DataFetchError(
                "xueqiu", "kline", f"不支持的 period: {period}", "data"
            )

        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        items = self._request(session, xq_symbol, xq_period, start, end, adj)
        if items is None:
            # cookie 过期重试
            session = refresh_session()
            items = self._request(session, xq_symbol, xq_period, start, end, adj)

        if not items:
            raise DataFetchError(
                "xueqiu", "kline",
                f"无数据: {symbol} {period} {start}-{end}", "data"
            )

        bars = self._parse(symbol, period, adj, items)
        return DataResult(
            data=bars,
            source="xueqiu",
            meta={
                "rows": len(bars),
                "symbol": symbol,
                "period": period,
                "upstream": "xueqiu",
            },
        )

    def _request(
        self,
        session: requests.Session,
        xq_symbol: str,
        xq_period: str,
        start: str,
        end: str,
        adj: str,
    ) -> list | None:
        begin_ts = _date_to_ts(start)
        end_ts = _date_to_ts(end)

        # 雪球的 begin/end 是毫秒时间戳，count=-1 表示不限数量
        params = {
            "symbol": xq_symbol,
            "begin": end_ts,
            "period": xq_period,
            "type": "before",
            "count": -284,  # 足够大，覆盖一年多
            "indicator": "kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance",
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

        # 转为 dict 列表
        return [dict(zip(columns, row)) for row in items]

    def _parse(
        self, symbol: str, period: str, adj: str, items: list[dict]
    ) -> list[dict]:
        bars = []
        for d in items:
            ts_ms = d.get("timestamp")
            if ts_ms is None:
                continue
            date = _ts_to_date(ts_ms)
            bars.append(
                KlineBar(
                    symbol=symbol,
                    date=date,
                    period=period,
                    open=float(d.get("open", 0) or 0),
                    high=float(d.get("high", 0) or 0),
                    low=float(d.get("low", 0) or 0),
                    close=float(d.get("close", 0) or 0),
                    volume=float(d.get("volume", 0) or 0),
                    amount=float(d.get("amount", 0) or 0),
                    pct_chg=float(d.get("percent", 0) or 0),
                    adj=adj,
                ).to_dict()
            )
        # 按日期升序
        bars.sort(key=lambda b: b["date"])
        return bars
