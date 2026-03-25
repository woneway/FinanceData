"""交易日历 - akshare 实现"""
from datetime import datetime, timedelta
import akshare as ak

from finance_data.interface.calendar.history import TradeDate
from finance_data.interface.types import DataResult, DataFetchError


class AkshareTradeCalendar:
    def get_trade_calendar_history(self, start: str, end: str) -> DataResult:
        try:
            df = ak.tool_trade_date_hist_sina()
        except Exception as e:
            raise DataFetchError("akshare", "tool_trade_date_hist_sina", str(e), "network") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "tool_trade_date_hist_sina", "无数据", "data")

        trade_date_set = {
            d.strftime("%Y%m%d") if hasattr(d, "strftime") else str(d).replace("-", "")
            for d in df["trade_date"]
        }

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
