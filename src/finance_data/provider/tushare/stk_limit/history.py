"""全市场涨跌停价 - tushare 实现"""
from finance_data.interface.stk_limit.history import StkLimitEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.cache.resolver import fetch_cached
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_FIELDS = ",".join([
    "ts_code", "trade_date", "pre_close", "up_limit", "down_limit",
])


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


class TushareStkLimit:
    def get_stk_limit(self, trade_date: str) -> DataResult:
        pro = get_pro()
        try:
            df = fetch_cached("stk_limit", trade_date)
            if df is None:
                df = pro.stk_limit(trade_date=trade_date, fields=_FIELDS)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stk_limit", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stk_limit", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "stk_limit", f"无数据: {trade_date}", "data")

        rows = [
            StkLimitEntry(
                symbol=str(row.get("ts_code", "")),
                trade_date=str(row.get("trade_date", "")),
                pre_close=_flt(row.get("pre_close")),
                up_limit=_flt(row.get("up_limit")),
                down_limit=_flt(row.get("down_limit")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "trade_date": trade_date})
