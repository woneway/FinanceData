"""K线历史数据 - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.kline.models import KlineBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_PERIODS_DAILY = {"daily", "weekly", "monthly"}
_PERIODS_MIN = {"1min", "5min", "15min", "30min", "60min"}
_MIN_MAP = {"1min": "1", "5min": "5", "15min": "15", "30min": "30", "60min": "60"}


@contextlib.contextmanager
def _no_proxy():
    orig = requests.Session.__init__

    def _init(self, *a, **kw):
        orig(self, *a, **kw)
        self.trust_env = False

    requests.Session.__init__ = _init
    try:
        yield
    finally:
        requests.Session.__init__ = orig


def _parse_date(val) -> str:
    s = str(val).strip()
    return s.replace("-", "").replace(" ", "")[:8]


def get_kline(symbol: str, period: str, start: str, end: str,
              adj: str = "qfq") -> DataResult:
    """
    获取 K线历史数据。

    Args:
        symbol: 股票代码，如 "000001"
        period: daily/weekly/monthly/1min/5min/15min/30min/60min
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        DataResult，data 为 [KlineBar.to_dict(), ...]
    """
    try:
        with _no_proxy():
            if period in _PERIODS_DAILY:
                df = ak.stock_zh_a_hist(
                    symbol=symbol, period=period,
                    start_date=start, end_date=end, adjust=adj,
                )
            elif period in _PERIODS_MIN:
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol, period=_MIN_MAP[period],
                    start_date=start, end_date=end, adjust=adj,
                )
            else:
                raise DataFetchError("akshare", "get_kline",
                                     f"不支持的 period: {period}", "data")
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "get_kline", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "get_kline", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "get_kline",
                             f"无数据: {symbol} {period} {start}-{end}", "data")

    bars = []
    for _, row in df.iterrows():
        date_col = "时间" if period in _PERIODS_MIN else "日期"
        bars.append(KlineBar(
            symbol=symbol,
            date=_parse_date(row.get(date_col, "")),
            period=period,
            open=float(row.get("开盘", 0)),
            high=float(row.get("最高", 0)),
            low=float(row.get("最低", 0)),
            close=float(row.get("收盘", 0)),
            volume=float(row.get("成交量", 0)),
            amount=float(row.get("成交额", 0)),
            pct_chg=float(row.get("涨跌幅", 0)),
            adj=adj,
        ).to_dict())

    return DataResult(
        data=bars, source="akshare",
        meta={"rows": len(bars), "symbol": symbol, "period": period},
    )
