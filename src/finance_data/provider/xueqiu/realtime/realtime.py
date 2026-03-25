"""实时行情 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.realtime.realtime import RealtimeQuote
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    refresh_session,
)

logger = logging.getLogger(__name__)

_QUOTEC_URL = "https://stock.xueqiu.com/v5/stock/realtime/quotec.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _opt_float(val) -> float | None:
    if val is None:
        return None
    try:
        v = float(val)
        return None if v != v else v  # NaN check
    except (TypeError, ValueError):
        return None


class XueqiuRealtimeQuote:
    """雪球实时行情 provider（无需登录 cookie）"""

    def get_realtime_quote(self, symbol: str) -> DataResult:
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            # cookie 可能过期，刷新后重试一次
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "quotec", f"无法获取行情: {symbol}", "data"
            )

        quote = self._parse(symbol, data)
        return DataResult(
            data=[quote.to_dict()],
            source="xueqiu",
            meta={"rows": 1, "symbol": symbol},
        )

    def _request(self, session: requests.Session, xq_symbol: str) -> dict | None:
        try:
            resp = session.get(
                _QUOTEC_URL,
                params={"symbol": xq_symbol},
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError(
                "xueqiu", "quotec", str(e), kind
            ) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "xueqiu", "quotec", str(e), "network"
            ) from e
        except Exception as e:
            raise DataFetchError(
                "xueqiu", "quotec", str(e), "data"
            ) from e

        items = body.get("data", [])
        if not items:
            return None
        return items[0]

    def _parse(self, symbol: str, d: dict) -> RealtimeQuote:
        ts_ms = d.get("timestamp")
        if ts_ms:
            dt = datetime.datetime.fromtimestamp(
                ts_ms / 1000, tz=datetime.timezone.utc
            )
            timestamp = dt.astimezone(
                datetime.timezone(datetime.timedelta(hours=8))
            ).isoformat(timespec="seconds")
        else:
            timestamp = datetime.datetime.now().isoformat(timespec="seconds")

        return RealtimeQuote(
            symbol=symbol,
            name=str(d.get("name", "")),
            price=float(d.get("current", 0) or 0),
            pct_chg=float(d.get("percent", 0) or 0),
            volume=float(d.get("volume", 0) or 0),
            amount=float(d.get("amount", 0) or 0),
            market_cap=_opt_float(d.get("market_capital")),
            pe=_opt_float(d.get("pe_ttm")),
            pb=_opt_float(d.get("pb")),
            turnover_rate=_opt_float(d.get("turnover_rate")),
            timestamp=timestamp,
        )
