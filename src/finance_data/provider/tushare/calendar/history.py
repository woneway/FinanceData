"""交易日历 - tushare 实现"""
from finance_data.interface.calendar.history import TradeDate
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareTradeCalendar:
    def get_trade_calendar_history(self, start: str, end: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.trade_cal(exchange="SSE", start_date=start, end_date=end,
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
