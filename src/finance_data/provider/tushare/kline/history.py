"""K线历史数据 - tushare 实现"""
from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_DAILY_FUNC = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
_MIN_FREQ = {"1min": "1min", "5min": "5min", "15min": "15min",
             "30min": "30min", "60min": "60min"}


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


class TushareKlineHistory:
    def get_kline_history(self, symbol: str, period: str, start: str, end: str,
                          adj: str = "qfq") -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            if period in _DAILY_FUNC:
                fn = getattr(pro, _DAILY_FUNC[period])
                df = fn(ts_code=ts_code, start_date=start, end_date=end,
                        fields="trade_date,open,high,low,close,vol,amount,pct_chg")
            elif period in _MIN_FREQ:
                df = pro.stk_mins(ts_code=ts_code, freq=_MIN_FREQ[period],
                                  start_date=start + " 09:00:00",
                                  end_date=end + " 15:30:00")
            else:
                raise DataFetchError("tushare", "get_kline_history",
                                     f"不支持的 period: {period}", "data")
        except DataFetchError:
            raise
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "get_kline_history", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "get_kline_history", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "get_kline_history",
                                 f"无数据: {symbol} {period} {start}-{end}", "data")

        date_col = "trade_time" if period in _MIN_FREQ else "trade_date"
        bars = []
        for _, row in df.iterrows():
            s = str(row.get(date_col, "")).replace("-", "").replace(" ", "")[:8]
            bars.append(KlineBar(
                symbol=symbol, date=s if s.isdigit() else "", period=period,
                open=float(row.get("open", 0)), high=float(row.get("high", 0)),
                low=float(row.get("low", 0)), close=float(row.get("close", 0)),
                volume=float(row.get("vol", 0)) * 100,
                amount=float(row.get("amount", 0)) * 1000,
                pct_chg=float(row.get("pct_chg", 0)), adj=adj,
            ).to_dict())

        return DataResult(data=bars, source="tushare",
                          meta={"rows": len(bars), "symbol": symbol, "period": period})
