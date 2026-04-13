"""同花顺涨跌停榜单 - tushare 实现"""
from finance_data.interface.pool.limit_list import LimitListEntry
from finance_data.interface.types import DataFetchError, DataResult
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


class TushareLimitList:
    def get_limit_list(self, trade_date: str, limit_type: str = "涨停池") -> DataResult:
        pro = get_pro()
        try:
            df = pro.limit_list_ths(trade_date=trade_date, limit_type=limit_type)
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
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "limit_type": limit_type})
