"""大盘指数 - tushare"""
import datetime
import os
import tushare as ts

from finance_data.provider.index.models import IndexQuote, IndexBar
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


def get_index_quote(symbol: str) -> DataResult:
    """获取指数最新行情（取 daily 最近一条）。"""
    pro = _get_pro()
    try:
        df = pro.index_daily(ts_code=symbol, limit=1)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "index_daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "index_daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "index_daily", f"未找到指数: {symbol}", "data")

    row = df.iloc[0]
    quote = IndexQuote(
        symbol=symbol, name="",
        price=float(row.get("close", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
        volume=float(row.get("vol", 0)),
        amount=float(row.get("amount", 0)),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(data=[quote.to_dict()], source="tushare",
                      meta={"rows": 1, "symbol": symbol})


def get_index_history(symbol: str, start: str, end: str) -> DataResult:
    """获取指数历史 K线。"""
    pro = _get_pro()
    try:
        df = pro.index_daily(ts_code=symbol, start_date=start, end_date=end)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "index_daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "index_daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "index_daily",
                             f"无数据: {symbol} {start}-{end}", "data")

    bars = [IndexBar(
        symbol=symbol,
        date=str(row.get("trade_date", "")),
        open=float(row.get("open", 0)), high=float(row.get("high", 0)),
        low=float(row.get("low", 0)), close=float(row.get("close", 0)),
        volume=float(row.get("vol", 0)), amount=float(row.get("amount", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
    ).to_dict() for _, row in df.iterrows()]

    return DataResult(data=bars, source="tushare",
                      meta={"rows": len(bars), "symbol": symbol})
