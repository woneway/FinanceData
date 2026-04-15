"""东财板块日行情 - tushare 实现"""
from finance_data.interface.board.daily import BoardDailyRow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.board.index import TushareBoardIndex
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _classify_error(func: str, exc: Exception) -> DataFetchError:
    reason = str(exc)
    kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
    return DataFetchError("tushare", func, reason, kind)


class TushareBoardDaily:
    def __init__(self, index_provider: TushareBoardIndex | None = None):
        self._index_provider = index_provider or TushareBoardIndex()

    def _resolve_board(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> dict:
        index_result = self._index_provider.get_board_index(
            idx_type=idx_type,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        matches = [row for row in index_result.data if row.get("board_name") == board_name]
        if not matches:
            raise DataFetchError(
                "tushare",
                "dc_index",
                f"未找到板块: {board_name} ({idx_type})",
                "data",
            )
        return matches[0]

    def get_board_daily(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        board = self._resolve_board(
            board_name=board_name,
            idx_type=idx_type,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        pro = get_pro()
        kwargs = {"ts_code": board["board_code"], "idx_type": idx_type}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        try:
            df = pro.dc_daily(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "dc_daily", str(e), "network") from e
        except Exception as e:
            raise _classify_error("dc_daily", e) from e

        if df is None or df.empty:
            raise DataFetchError(
                "tushare",
                "dc_daily",
                f"无数据: {board_name} ({board['board_code']})",
                "data",
            )

        rows = [
            BoardDailyRow(
                board_code=board["board_code"],
                board_name=board_name,
                idx_type=idx_type,
                trade_date=str(row.get("trade_date", "")),
                open=_flt(row.get("open")),
                high=_flt(row.get("high")),
                low=_flt(row.get("low")),
                close=_flt(row.get("close")),
                change=_flt(row.get("change")),
                pct_chg=_flt(row.get("pct_change")),
                volume=_flt(row.get("vol")),
                amount=_flt(row.get("amount")),
                swing=_flt(row.get("swing")),
                turnover_rate=_flt(row.get("turnover_rate")),
                level=board.get("level"),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        rows.sort(key=lambda row: row["trade_date"])
        return DataResult(
            data=rows,
            source="tushare",
            meta={
                "rows": len(rows),
                "board_code": board["board_code"],
                "board_name": board_name,
                "idx_type": idx_type,
            },
        )
