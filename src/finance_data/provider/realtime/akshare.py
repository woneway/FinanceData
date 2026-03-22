"""实时行情 - akshare（含 TTL 缓存）"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.realtime.models import RealtimeQuote
from finance_data.provider.realtime import cache
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


def _opt_float(val) -> float | None:
    try:
        v = float(val)
        return None if v != v else v  # NaN check
    except (TypeError, ValueError):
        return None


def get_realtime_quote(symbol: str) -> DataResult:
    """获取实时行情（TTL 缓存 20 分钟）。"""
    cache_key = f"akshare:realtime:{symbol}"
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        with _no_proxy():
            df = ak.stock_zh_a_spot_em()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "data") from e

    row_df = df[df["代码"] == symbol]
    if row_df.empty:
        raise DataFetchError("akshare", "stock_zh_a_spot_em",
                             f"未找到股票: {symbol}", "data")

    row = row_df.iloc[0]
    quote = RealtimeQuote(
        symbol=symbol,
        name=str(row.get("名称", "")),
        price=float(row.get("最新价", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        market_cap=_opt_float(row.get("总市值")),
        pe=_opt_float(row.get("市盈率-动态")),
        pb=_opt_float(row.get("市净率")),
        turnover_rate=_opt_float(row.get("换手率")),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    result = DataResult(
        data=[quote.to_dict()], source="akshare",
        meta={"rows": 1, "symbol": symbol},
    )
    cache.set_cached(cache_key, result)
    return result
