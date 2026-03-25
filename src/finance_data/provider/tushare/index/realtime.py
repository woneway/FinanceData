"""大盘指数实时行情 - tushare 实现"""
import datetime

from finance_data.interface.index.realtime import IndexQuote
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareIndexQuote:
    def get_index_quote_realtime(self, symbol: str) -> DataResult:
        pro = get_pro()
        try:
            df = pro.index_daily(ts_code=symbol, limit=1)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "index_daily", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "index_daily", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "index_daily", f"未找到指数: {symbol}", "data")

        row = df.iloc[0]
        quote = IndexQuote(
            symbol=symbol, name="",
            price=float(row.get("close", 0)),
            pct_chg=float(row.get("pct_chg", 0)),
            volume=float(row.get("vol", 0)) * 100,
            amount=float(row.get("amount", 0)) * 1000,
            timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
        )
        return DataResult(data=[quote.to_dict()], source="tushare",
                          meta={"rows": 1, "symbol": symbol})
