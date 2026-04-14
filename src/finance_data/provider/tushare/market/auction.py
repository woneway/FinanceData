"""开盘集合竞价 - tushare 实现"""
from finance_data.interface.market.auction import AuctionEntry
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


class TushareAuction:
    def get_auction(
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
            df = pro.stk_auction(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stk_auction", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stk_auction", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "stk_auction", f"无数据: {trade_date}", "data")

        rows = [
            AuctionEntry(
                symbol=str(row.get("ts_code", "")),
                trade_date=str(row.get("trade_date", "")),
                price=_flt(row.get("price")),
                volume=_flt(row.get("vol")),
                amount=_flt(row.get("amount")),
                pre_close=_flt(row.get("pre_close")),
                turnover_rate=_opt_flt(row.get("turnover_rate")),
                volume_ratio=_opt_flt(row.get("volume_ratio")),
                float_share=_opt_flt(row.get("float_share")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows)})
