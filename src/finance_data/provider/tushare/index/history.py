"""大盘指数历史 K线 - tushare 实现"""
from finance_data.interface.index.history import IndexBar
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareIndexHistory:
    def get_index_history(self, symbol: str, start: str, end: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.index_daily(ts_code=symbol, start_date=start, end_date=end)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "index_daily", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "index_daily", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "index_daily",
                                 f"无数据: {symbol} {start}-{end}", "data")

        bars = [IndexBar(
            symbol=symbol,
            date=str(row.get("trade_date", "")),
            open=float(row.get("open", 0)), high=float(row.get("high", 0)),
            low=float(row.get("low", 0)), close=float(row.get("close", 0)),
            volume=float(row.get("vol", 0)),
            amount=float(row.get("amount", 0)) * 1000,
            pct_chg=float(row.get("pct_chg", 0)),
        ).to_dict() for _, row in df.iterrows()]

        bars.sort(key=lambda b: b["date"])

        return DataResult(data=bars, source="tushare",
                          meta={"rows": len(bars), "symbol": symbol})
