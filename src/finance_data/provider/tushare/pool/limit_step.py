"""连板天梯 - tushare 实现"""
from finance_data.interface.pool.limit_step import LimitStepEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareLimitStep:
    def get_limit_step(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        kwargs: dict = {}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        try:
            df = pro.limit_step(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "limit_step", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "limit_step", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "limit_step", f"无数据: {trade_date}", "data")

        rows = [
            LimitStepEntry(
                symbol=str(row.get("ts_code", "")),
                name=str(row.get("name", "")),
                trade_date=str(row.get("trade_date", "")),
                nums=int(row.get("nums", 0)),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        rows.sort(key=lambda r: r["nums"], reverse=True)
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows)})
