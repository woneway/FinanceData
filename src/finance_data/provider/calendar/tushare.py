"""交易日历 - tushare"""
import os
import tushare as ts

from finance_data.provider.calendar.models import TradeDate
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


def get_trade_calendar(start: str, end: str, exchange: str = "SSE") -> DataResult:
    """获取交易日历。"""
    pro = _get_pro()
    try:
        df = pro.trade_cal(exchange=exchange, start_date=start, end_date=end,
                           fields="cal_date,is_open")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "trade_cal", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "trade_cal", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "trade_cal", f"无数据: {start}-{end}", "data")

    rows = [TradeDate(
        date=str(r["cal_date"]),
        is_open=bool(int(r.get("is_open", 0))),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "start": start, "end": end})
