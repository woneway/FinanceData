"""开盘啦榜单 - tushare 实现"""
from finance_data.interface.pool.kpl_list import KplListEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.cache.resolver import resolve
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _opt_flt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


class TushareKplList:
    def get_kpl_list(
        self, trade_date: str = "", tag: str = "涨停",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        kwargs: dict = {"tag": tag}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        try:
            df = resolve("kpl_list", trade_date, start_date, end_date, extra_where=f"tag = '{tag}'")
            if df is None:
                df = pro.kpl_list(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "kpl_list", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "kpl_list", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "kpl_list", f"无数据: {trade_date} {tag}", "data")

        rows = [
            KplListEntry(
                symbol=str(row.get("ts_code", "")),
                name=str(row.get("name", "")),
                trade_date=str(row.get("trade_date", "")),
                pct_chg=_flt(row.get("pct_chg")),
                tag=str(row.get("tag", "") or ""),
                theme=str(row.get("theme", "") or ""),
                status=str(row.get("status", "") or ""),
                lu_time=str(row.get("lu_time", "") or ""),
                lu_desc=str(row.get("lu_desc", "") or ""),
                amount=_opt_flt(row.get("amount")),
                turnover_rate=_opt_flt(row.get("turnover_rate")),
                limit_order=_opt_flt(row.get("limit_order")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "tag": tag})
