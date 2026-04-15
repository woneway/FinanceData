"""全市场日线行情 - tushare 实现"""
from finance_data.interface.daily_market.history import DailyMarketBar
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_FIELDS = ",".join([
    "ts_code", "trade_date", "open", "high", "low", "close",
    "pre_close", "change", "pct_chg", "vol", "amount",
])


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


class TushareDailyMarket:
    def get_daily_market(self, trade_date: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.daily(trade_date=trade_date, fields=_FIELDS)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "daily", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "daily", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "daily", f"无数据: {trade_date}", "data")

        rows = [
            DailyMarketBar(
                symbol=str(row.get("ts_code", "")),
                trade_date=str(row.get("trade_date", "")),
                open=_flt(row.get("open")),
                high=_flt(row.get("high")),
                low=_flt(row.get("low")),
                close=_flt(row.get("close")),
                pre_close=_flt(row.get("pre_close")),
                change=_flt(row.get("change")),
                pct_chg=_flt(row.get("pct_chg")),
                volume=_flt(row.get("vol")) * 100,
                amount=_flt(row.get("amount")) * 1000,
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "trade_date": trade_date})
