"""K线历史数据 - tushare"""
import os
import tushare as ts

from finance_data.provider.kline.models import KlineBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_DAILY_FUNC = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
_MIN_FREQ = {"1min": "1min", "5min": "5min", "15min": "15min",
             "30min": "30min", "60min": "60min"}


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


def get_kline(symbol: str, period: str, start: str, end: str,
              adj: str = "qfq") -> DataResult:
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    adj_ts = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adj, "qfq")

    try:
        if period in _DAILY_FUNC:
            fn = getattr(pro, _DAILY_FUNC[period])
            df = fn(ts_code=ts_code, start_date=start, end_date=end,
                    fields="trade_date,open,high,low,close,vol,amount,pct_chg")
        elif period in _MIN_FREQ:
            df = pro.stk_mins(ts_code=ts_code, freq=_MIN_FREQ[period],
                              start_date=start + " 09:00:00",
                              end_date=end + " 15:30:00")
        else:
            raise DataFetchError("tushare", "get_kline",
                                 f"不支持的 period: {period}", "data")
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "get_kline", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "get_kline", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "get_kline",
                             f"无数据: {symbol} {period} {start}-{end}", "data")

    date_col = "trade_time" if period in _MIN_FREQ else "trade_date"
    bars = []
    for _, row in df.iterrows():
        s = str(row.get(date_col, "")).replace("-", "").replace(" ", "")[:8]
        raw_date = s if s.isdigit() else ""
        bars.append(KlineBar(
            symbol=symbol,
            date=raw_date,
            period=period,
            open=float(row.get("open", 0)),
            high=float(row.get("high", 0)),
            low=float(row.get("low", 0)),
            close=float(row.get("close", 0)),
            volume=float(row.get("vol", 0)),
            amount=float(row.get("amount", 0)) * 1000,  # tushare amount 单位为千元
            pct_chg=float(row.get("pct_chg", 0)),
            adj=adj,
        ).to_dict())

    return DataResult(
        data=bars, source="tushare",
        meta={"rows": len(bars), "symbol": symbol, "period": period},
    )
