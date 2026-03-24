"""融资融券 - tushare"""
import os
import tushare as ts

from finance_data.provider.margin.models import MarginSummary, MarginDetail
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_EXCHANGE_MAP = {"SSE": "上交所", "SZSE": "深交所", "BSE": "北交所"}


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


def get_margin(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    exchange_id: str = "",
) -> DataResult:
    """
    获取融资融券汇总数据（按交易所）。

    Args:
        trade_date: 交易日期 YYYYMMDD（二选一，与 start_date/end_date 互斥）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        exchange_id: 交易所代码 choice of {"SSE", "SZSE", "BSE"}，空则返回全部

    Returns:
        DataResult，data 为 [MarginSummary.to_dict(), ...]
    """
    pro = _get_pro()
    try:
        df = pro.margin(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            exchange_id=exchange_id,
        )
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "margin", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "margin", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "margin",
                             f"无数据: trade_date={trade_date} start={start_date} end={end_date}", "data")

    rows = []
    for _, row in df.iterrows():
        exchange_raw = str(row.get("exchange_id", ""))
        exchange = _EXCHANGE_MAP.get(exchange_raw, exchange_raw)
        rows.append(MarginSummary(
            date=str(row.get("trade_date", "")).replace("-", ""),
            exchange=exchange,
            rzye=float(row.get("rzye", 0) or 0),
            rzmre=float(row.get("rzmre", 0) or 0),
            rzche=float(row.get("rzche", 0) or 0),
            rqye=float(row.get("rqye", 0) or 0),
            rqmcl=float(row.get("rqmcl", 0) or 0),
            rzrqye=float(row.get("rzrqye", 0) or 0),
            rqyl=float(row.get("rqyl", 0) or 0),
        ).to_dict())

    rows.sort(key=lambda x: x["date"], reverse=True)
    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "trade_date": trade_date,
                            "start_date": start_date, "end_date": end_date})


def get_margin_detail(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    ts_code: str = "",
) -> DataResult:
    """
    获取融资融券个股明细。

    Args:
        trade_date: 交易日期 YYYYMMDD
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        ts_code: 股票代码（如 "000001.SZ"）

    Returns:
        DataResult，data 为 [MarginDetail.to_dict(), ...]
    """
    pro = _get_pro()
    try:
        df = pro.margin_detail(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            ts_code=ts_code,
        )
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "margin_detail", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "margin_detail", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "margin_detail",
                           f"无数据: trade_date={trade_date} ts_code={ts_code}", "data")

    rows = []
    for _, row in df.iterrows():
        ts_code_val = str(row.get("ts_code", ""))
        symbol = ts_code_val.split(".")[0] if "." in ts_code_val else ts_code_val
        rows.append(MarginDetail(
            date=str(row.get("trade_date", "")).replace("-", ""),
            symbol=symbol,
            name=str(row.get("name", "") or ""),
            rzye=float(row.get("rzye", 0) or 0),
            rqye=float(row.get("rqye", 0) or 0),
            rzmre=float(row.get("rzmre", 0) or 0),
            rqyl=float(row.get("rqyl", 0) or 0),
            rzche=float(row.get("rzche", 0) or 0),
            rqchl=float(row.get("rqchl", 0) or 0),
            rqmcl=float(row.get("rqmcl", 0) or 0),
            rzrqye=float(row.get("rzrqye", 0) or 0),
        ).to_dict())

    return DataResult(data=rows, source="tushare",
                     meta={"rows": len(rows), "trade_date": trade_date,
                           "start_date": start_date, "end_date": end_date,
                           "ts_code": ts_code})
