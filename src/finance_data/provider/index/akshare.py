"""大盘指数 - akshare"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.index.models import IndexQuote, IndexBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


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


def _strip_code(symbol: str) -> str:
    """000001.SH → 000001"""
    return symbol.split(".")[0]


def get_index_quote(symbol: str) -> DataResult:
    """获取大盘指数实时行情。"""
    code = _strip_code(symbol)
    try:
        with _no_proxy():
            df = ak.stock_zh_index_spot_sina()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "data") from e

    row_df = df[df["代码"] == code]
    if row_df.empty:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina",
                             f"未找到指数: {symbol}", "data")
    row = row_df.iloc[0]
    quote = IndexQuote(
        symbol=symbol,
        name=str(row.get("名称", "")),
        price=float(row.get("最新价", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(data=[quote.to_dict()], source="akshare",
                      meta={"rows": 1, "symbol": symbol})


def get_index_history(symbol: str, start: str, end: str) -> DataResult:
    """获取大盘指数历史 K线。"""
    code = _strip_code(symbol)
    prefix = "sh" if symbol.endswith(".SH") else "sz"
    try:
        with _no_proxy():
            df = ak.stock_zh_index_daily_em(symbol=f"{prefix}{code}")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_index_daily_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_index_daily_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_zh_index_daily_em",
                             f"无数据: {symbol}", "data")

    start_d = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    end_d = f"{end[:4]}-{end[4:6]}-{end[6:]}"
    df = df[(df["日期"] >= start_d) & (df["日期"] <= end_d)]

    bars = [IndexBar(
        symbol=symbol,
        date=str(row["日期"]).replace("-", ""),
        open=float(row.get("开盘", 0)),
        high=float(row.get("最高", 0)),
        low=float(row.get("最低", 0)),
        close=float(row.get("收盘", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
    ).to_dict() for _, row in df.iterrows()]

    return DataResult(data=bars, source="akshare",
                      meta={"rows": len(bars), "symbol": symbol})
