"""停牌信息 - tushare 实现"""
from finance_data.interface.suspend.history import SuspendInfo
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s in ("nan", "None") else s


class TushareSuspend:
    def get_suspend_history(self, date: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.suspend_d(trade_date=date, suspend_type="S")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "suspend_d", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "suspend_d", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "suspend_d", f"无数据: {date}", "data")

        rows = [
            SuspendInfo(
                symbol=str(row.get("ts_code", "")),
                name="",
                suspend_date=_str(row.get("trade_date")),
                resume_date="",
                suspend_duration="",
                suspend_reason=_str(row.get("suspend_type")),
                market="",
                expected_resume_date="",
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "trade_date": date})
