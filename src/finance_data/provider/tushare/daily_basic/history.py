"""全市场日频基本面 - tushare 实现"""
from finance_data.interface.daily_basic.history import DailyBasicMarket
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_FIELDS = ",".join([
    "ts_code", "trade_date", "close", "turnover_rate", "turnover_rate_f",
    "volume_ratio", "pe_ttm", "pb", "total_mv", "circ_mv",
])


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


class TushareDailyBasicMarket:
    def get_daily_basic_market(self, trade_date: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.daily_basic(trade_date=trade_date, fields=_FIELDS)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "daily_basic", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "daily_basic", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "daily_basic", f"无数据: {trade_date}", "data")

        rows = [
            DailyBasicMarket(
                symbol=str(row.get("ts_code", "")),
                trade_date=str(row.get("trade_date", "")),
                close=_flt(row.get("close")),
                turnover_rate=_flt(row.get("turnover_rate")),
                turnover_rate_f=_flt(row.get("turnover_rate_f")),
                volume_ratio=_flt(row.get("volume_ratio")),
                pe_ttm=_flt(row.get("pe_ttm")),
                pb=_flt(row.get("pb")),
                total_mv=_flt(row.get("total_mv")) * 10000,
                circ_mv=_flt(row.get("circ_mv")) * 10000,
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "trade_date": trade_date})
