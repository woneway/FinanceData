"""交易日历 - akshare"""
from datetime import datetime, timedelta

import akshare as ak

from finance_data.provider.calendar.models import TradeDate
from finance_data.provider.types import DataResult, DataFetchError


def get_trade_calendar(start: str, end: str, exchange: str = "SSE") -> DataResult:
    """获取交易日历（akshare 新浪财经历史交易日历）。

    akshare 接口只返回交易日（无 is_open 字段），因此会补充
    start~end 范围内所有日期，非交易日标记 is_open=False。
    """
    try:
        df = ak.tool_trade_date_hist_sina()
    except Exception as e:
        raise DataFetchError("akshare", "tool_trade_date_hist_sina", str(e), "network") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "tool_trade_date_hist_sina", f"无数据", "data")

    # 将 trade_date 列转为 YYYYMMDD 字符串集合（仅交易日）
    trade_date_set = {
        d.strftime("%Y%m%d") if hasattr(d, "strftime") else str(d).replace("-", "")
        for d in df["trade_date"]
    }

    # 生成 start~end 范围内所有日期，标记 is_open
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    rows = []
    cur = start_dt
    while cur <= end_dt:
        date_str = cur.strftime("%Y%m%d")
        rows.append(TradeDate(date=date_str, is_open=date_str in trade_date_set).to_dict())
        cur += timedelta(days=1)

    return DataResult(data=rows, source="akshare",
                      meta={"rows": len(rows), "start": start, "end": end})
