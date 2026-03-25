"""大盘指数实时行情 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.index.realtime import IndexQuote
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import get_session, refresh_session

logger = logging.getLogger(__name__)

_QUOTEC_URL = "https://stock.xueqiu.com/v5/stock/realtime/quotec.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

# 指数代码映射：000001.SH → SH000001
_INDEX_MAP = {
    "000001.SH": "SH000001",  # 上证指数
    "399001.SZ": "SZ399001",  # 深证成指
    "399006.SZ": "SZ399006",  # 创业板指
    "000300.SH": "SH000300",  # 沪深300
    "000016.SH": "SH000016",  # 上证50
    "000905.SH": "SH000905",  # 中证500
    "000852.SH": "SH000852",  # 中证1000
}


def _to_xueqiu_index(symbol: str) -> str:
    """将指数代码转为雪球格式"""
    if symbol in _INDEX_MAP:
        return _INDEX_MAP[symbol]
    code = symbol.split(".")[0]
    suffix = symbol.split(".")[-1] if "." in symbol else ("SH" if code.startswith("0") else "SZ")
    return f"{suffix}{code}"


class XueqiuIndexQuote:
    """雪球指数实时行情（无需登录 cookie）"""

    def get_index_quote_realtime(self, symbol: str) -> DataResult:
        xq_symbol = _to_xueqiu_index(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "quotec", f"无法获取指数行情: {symbol}", "data"
            )

        ts_ms = data.get("timestamp")
        if ts_ms:
            dt = datetime.datetime.fromtimestamp(
                ts_ms / 1000, tz=datetime.timezone.utc
            )
            timestamp = dt.astimezone(
                datetime.timezone(datetime.timedelta(hours=8))
            ).isoformat(timespec="seconds")
        else:
            timestamp = datetime.datetime.now().isoformat(timespec="seconds")

        quote = IndexQuote(
            symbol=symbol,
            name=str(data.get("symbol", "")),
            price=float(data.get("current", 0) or 0),
            pct_chg=float(data.get("percent", 0) or 0),
            volume=float(data.get("volume", 0) or 0),
            amount=float(data.get("amount", 0) or 0),
            timestamp=timestamp,
        )
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
            raise DataFetchError(
                "xueqiu", "quotec", str(e), "network"
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
