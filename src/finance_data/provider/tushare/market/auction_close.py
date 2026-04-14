"""收盘集合竞价 - tushare 实现"""
from finance_data.interface.market.auction_close import AuctionCloseEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


class TushareAuctionClose:
    def get_auction_close(
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
            df = pro.stk_auction_c(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stk_auction_c", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stk_auction_c", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "stk_auction_c", f"无数据: {trade_date}", "data")

        rows = [
            AuctionCloseEntry(
                symbol=str(row.get("ts_code", "")),
                trade_date=str(row.get("trade_date", "")),
                close=_flt(row.get("close")),
                open=_flt(row.get("open")),
                high=_flt(row.get("high")),
                low=_flt(row.get("low")),
                volume=_flt(row.get("vol")),
                amount=_flt(row.get("amount")),
                vwap=_flt(row.get("vwap")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows)})
