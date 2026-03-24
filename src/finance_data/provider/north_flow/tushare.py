"""北向资金 - tushare

tushare 的北向资金接口 hk_hold 提供个股持股明细，
无直接的日频北向资金净流入汇总（akshare 有 stock_hsgt_fund_flow_summary_em）。
"""
import os
import tushare as ts

from finance_data.provider.north_flow.models import NorthStockHold
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


def get_north_stock_hold(
    symbol: str = "",
    trade_date: str = "",
    exchange: str = "",
) -> DataResult:
    """
    获取北向资金持股明细（tushare hk_hold）。

    Args:
        symbol: 股票代码，如 "600000"（可选）
        trade_date: 交易日期 YYYYMMDD（如 "20240301"）
        exchange: 类型 choice of {"SH", "SZ", "HK"}，
                  SH=沪股通（北向）SZ=深股通（北向）HK=港股通（南向）

    Returns:
        DataResult，data 为 [NorthStockHold.to_dict(), ...]

    Note:
        交易所于2024年8月20日起停止发布日度北向资金数据，改为季度披露。
        近期数据可能仅返回历史季度数据。
    """
    pro = _get_pro()
    try:
        df = pro.hk_hold(
            ts_code=symbol,
            trade_date=trade_date,
            exchange=exchange,
        )
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "hk_hold", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "hk_hold", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "hk_hold",
                             f"无数据: symbol={symbol} trade_date={trade_date}", "data")

    rows = []
    for _, row in df.iterrows():
        date = str(row.get("trade_date", "")).replace("-", "")
        ts_code = str(row.get("ts_code", ""))
        # ts_code 格式: 600000.SH -> 600000
        symbol = ts_code.split(".")[0] if "." in ts_code else ts_code
        rows.append(NorthStockHold(
            symbol=symbol,
            name=str(row.get("name", "") or ""),
            date=date,
            close_price=0,  # hk_hold 不提供收盘价
            pct_change=0,    # hk_hold 不提供涨跌幅
            hold_volume=float(row.get("vol", 0) or 0),
            hold_market_cap=0,  # hk_hold 不直接提供市值
            hold_float_ratio=float(row.get("ratio", 0) or 0),
            hold_total_ratio=0,  # tushare 不提供占总股本比
        ).to_dict())

    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "symbol": symbol,
                            "trade_date": trade_date, "exchange": exchange})
