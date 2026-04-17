"""同花顺涨跌停榜单 - tushare 实现"""
from finance_data.interface.pool.limit_list import LimitListEntry
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


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _opt_str(val):
    if val is None or (isinstance(val, float) and val != val):
        return None
    s = str(val).strip()
    return s if s else None


_FIELDS = ",".join([
    "trade_date", "ts_code", "name", "price", "pct_chg", "open_num",
    "lu_desc", "limit_type", "tag", "status",
    "first_lu_time", "last_lu_time", "first_ld_time", "last_ld_time",
    "limit_order", "limit_amount", "lu_limit_order", "limit_up_suc_rate",
    "turnover_rate", "turnover", "free_float", "sum_float",
    "rise_rate", "market_type",
])


class TushareLimitList:
    def get_limit_list(
        self,
        trade_date: str = "",
        limit_type: str = "涨停池",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        kwargs: dict = {"limit_type": limit_type, "fields": _FIELDS}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        try:
            df = resolve("limit_list_ths", trade_date, start_date, end_date, extra_where=f"limit_type = '{limit_type}'")
            if df is None:
                df = pro.limit_list_ths(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "limit_list_ths", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "limit_list_ths", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "limit_list_ths", f"无数据: {trade_date} {limit_type}", "data")

        rows = [
            LimitListEntry(
                symbol=str(row.get("ts_code", "")),
                name=str(row.get("name", "")),
                trade_date=str(row.get("trade_date", "")),
                price=_flt(row.get("price")),
                pct_chg=_flt(row.get("pct_chg")),
                limit_type=str(row.get("limit_type", limit_type)),
                open_num=_opt_int(row.get("open_num")),
                lu_desc=str(row.get("lu_desc", "") or ""),
                tag=str(row.get("tag", "") or ""),
                status=str(row.get("status", "") or ""),
                limit_order=_opt_flt(row.get("limit_order")),
                limit_amount=_opt_flt(row.get("limit_amount")),
                turnover_rate=_opt_flt(row.get("turnover_rate")),
                limit_up_suc_rate=_opt_flt(row.get("limit_up_suc_rate")),
                first_lu_time=_opt_str(row.get("first_lu_time")),
                last_lu_time=_opt_str(row.get("last_lu_time")),
                first_ld_time=_opt_str(row.get("first_ld_time")),
                last_ld_time=_opt_str(row.get("last_ld_time")),
                lu_limit_order=_opt_flt(row.get("lu_limit_order")),
                turnover=_opt_flt(row.get("turnover")),
                sum_float=_opt_flt(row.get("sum_float")),
                free_float=_opt_flt(row.get("free_float")),
                rise_rate=_opt_flt(row.get("rise_rate")),
                market_type=_opt_str(row.get("market_type")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "limit_type": limit_type})
