"""东财板块索引/快照 - tushare 实现"""
from finance_data.interface.board.index import BoardIndexRow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _opt_str(val):
    if val is None:
        return None
    text = str(val)
    return text if text and text.lower() != "nan" else None


def _classify_error(exc: Exception) -> DataFetchError:
    reason = str(exc)
    kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
    return DataFetchError("tushare", "dc_index", reason, kind)


class TushareBoardIndex:
    def get_board_index(self, idx_type: str, trade_date: str = "") -> DataResult:
        pro = get_pro()
        kwargs = {"idx_type": idx_type}
        if trade_date:
            kwargs["trade_date"] = trade_date
        try:
            df = pro.dc_index(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "dc_index", str(e), "network") from e
        except Exception as e:
            raise _classify_error(e) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "dc_index", f"无数据: {idx_type}", "data")

        rows = [
            BoardIndexRow(
                board_code=str(row.get("ts_code", "")),
                board_name=str(row.get("name", "")),
                idx_type=str(row.get("idx_type", "")),
                trade_date=str(row.get("trade_date", "")),
                level=_opt_str(row.get("level")),
                leading_stock=str(row.get("leading", "")),
                leading_stock_code=str(row.get("leading_code", "")),
                pct_change=_flt(row.get("pct_change")),
                leading_pct=_flt(row.get("leading_pct")),
                total_mv=_flt(row.get("total_mv")),
                turnover_rate=_flt(row.get("turnover_rate")),
                up_num=_opt_int(row.get("up_num")),
                down_num=_opt_int(row.get("down_num")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(
            data=rows,
            source="tushare",
            meta={"rows": len(rows), "idx_type": idx_type},
        )
