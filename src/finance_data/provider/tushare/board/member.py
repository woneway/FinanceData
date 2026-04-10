"""东财板块成分 - tushare 实现"""
from finance_data.interface.board.member import BoardMemberRow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.board.index import TushareBoardIndex
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _classify_error(func: str, exc: Exception) -> DataFetchError:
    reason = str(exc)
    kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
    return DataFetchError("tushare", func, reason, kind)


class TushareBoardMember:
    def __init__(self, index_provider: TushareBoardIndex | None = None):
        self._index_provider = index_provider or TushareBoardIndex()

    def _resolve_board(self, board_name: str, idx_type: str) -> dict:
        # 不传日期，让 board_index 默认取最新交易日
        index_result = self._index_provider.get_board_index(idx_type=idx_type)
        matches = [row for row in index_result.data if row.get("board_name") == board_name]
        if not matches:
            raise DataFetchError(
                "tushare",
                "dc_index",
                f"未找到板块: {board_name} ({idx_type})",
                "data",
            )
        return matches[0]

    def get_board_member(
        self,
        board_name: str,
        idx_type: str,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        board = self._resolve_board(board_name=board_name, idx_type=idx_type)
        pro = get_pro()
        has_date_param = bool(trade_date or start_date or end_date)
        kwargs: dict[str, str] = {"ts_code": board["board_code"]}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        try:
            df = pro.dc_member(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "dc_member", str(e), "network") from e
        except Exception as e:
            raise _classify_error("dc_member", e) from e

        if df is None or df.empty:
            raise DataFetchError(
                "tushare",
                "dc_member",
                f"无数据: {board_name} ({board['board_code']})",
                "data",
            )

        # 默认不传日期时上游返回多日数据，只保留最新交易日
        if not has_date_param:
            latest = df["trade_date"].max()
            df = df[df["trade_date"] == latest]

        rows = [
            BoardMemberRow(
                board_code=board["board_code"],
                board_name=board_name,
                idx_type=idx_type,
                trade_date=str(row.get("trade_date", "")),
                symbol=str(row.get("con_code", "")),
                name=str(row.get("name", "")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
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
