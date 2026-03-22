"""实时行情 - tushare"""
import datetime
import os
import tushare as ts

from finance_data.provider.realtime.models import RealtimeQuote
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _opt_float(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def get_realtime_quote(symbol: str) -> DataResult:
    """获取实时行情（tushare daily 最新一条作为近实时数据）。"""
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    try:
        df = pro.daily(ts_code=ts_code, limit=1)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "daily", f"未找到股票: {symbol}", "data")

    row = df.iloc[0]
    quote = RealtimeQuote(
        symbol=symbol,
        name="",  # tushare daily 不含股票名称
        price=float(row.get("close", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
        volume=float(row.get("vol", 0)),
        amount=float(row.get("amount", 0)) * 1000,  # tushare amount 单位为千元
        market_cap=None,
        pe=None,
        pb=None,
        turnover_rate=None,
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(
        data=[quote.to_dict()], source="tushare",
        meta={"rows": 1, "symbol": symbol},
    )
