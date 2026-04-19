"""K线历史数据 - tushare 实现"""
from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_DAILY_FUNC = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
_PERIOD_FACTORS = {
    "daily": {"volume": 100, "amount": 1000, "pct_chg": 1},
    "weekly": {"volume": 1, "amount": 1, "pct_chg": 100},
    "monthly": {"volume": 1, "amount": 1, "pct_chg": 100},
}


def _ts_code(symbol: str) -> str:
    from finance_data.provider.symbol import to_tushare
    return to_tushare(symbol)


def _fetch_kline(symbol: str, period: str, start: str, end: str,
                 adj: str, func_name: str) -> DataResult:
    """tushare 日/周/月线统一获取逻辑。"""
    pro = get_pro()
    ts_code = _ts_code(symbol)
    factors = _PERIOD_FACTORS[period]
    try:
        fn = getattr(pro, _DAILY_FUNC[period])
        df = fn(ts_code=ts_code, start_date=start, end_date=end,
                fields="trade_date,open,high,low,close,vol,amount,pct_chg")
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", func_name, str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", func_name, reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", func_name,
                             f"无数据: {symbol} {period} {start}-{end}", "data")

    bars = []
    for _, row in df.iterrows():
        s = str(row.get("trade_date", "")).replace("-", "").replace(" ", "")[:8]
        bars.append(KlineBar(
            symbol=symbol, date=s if s.isdigit() else "", period=period,
            open=float(row.get("open", 0)), high=float(row.get("high", 0)),
            low=float(row.get("low", 0)), close=float(row.get("close", 0)),
            volume=float(row.get("vol", 0)) * factors["volume"],
            amount=float(row.get("amount", 0)) * factors["amount"],
            pct_chg=float(row.get("pct_chg", 0)) * factors["pct_chg"],
            adj=adj,
        ).to_dict())

    bars.sort(key=lambda b: b["date"])

    return DataResult(data=bars, source="tushare",
                      meta={"rows": len(bars), "symbol": symbol, "period": period})


class TushareKlineHistory:
    def get_daily_kline_history(self, symbol: str, start: str, end: str,
                                adj: str = "qfq") -> DataResult:
        return _fetch_kline(symbol, "daily", start, end, adj, "get_daily_kline_history")

    def get_weekly_kline_history(self, symbol: str, start: str, end: str,
                                 adj: str = "qfq") -> DataResult:
        return _fetch_kline(symbol, "weekly", start, end, adj, "get_weekly_kline_history")

    def get_monthly_kline_history(self, symbol: str, start: str, end: str,
                                  adj: str = "qfq") -> DataResult:
        return _fetch_kline(symbol, "monthly", start, end, adj, "get_monthly_kline_history")
