"""实时行情 - akshare 实现（新浪源）"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.interface.realtime.realtime import RealtimeQuote
from finance_data.interface.types import DataResult, DataFetchError

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


class AkshareRealtimeQuote:
    def get_realtime_quote(self, symbol: str) -> DataResult:
        from finance_data.provider.symbol import to_sina
        sina_code = to_sina(symbol)
        try:
            with _no_proxy():
                df = ak.stock_zh_a_spot()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_zh_a_spot", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_zh_a_spot", str(e), "data") from e

        row_df = df[df["代码"] == sina_code]
        if row_df.empty:
            raise DataFetchError("akshare", "stock_zh_a_spot",
                                 f"未找到股票: {symbol}", "data")

        row = row_df.iloc[0]
        quote = RealtimeQuote(
            symbol=symbol,
            name=str(row.get("名称", "")),
            price=float(row.get("最新价", 0)),
            pct_chg=float(row.get("涨跌幅", 0)),
            volume=float(row.get("成交量", 0)),
            amount=float(row.get("成交额", 0)),
            market_cap=None,  # 新浪源不含总市值
            pe=None,          # 新浪源不含市盈率
            pb=None,          # 新浪源不含市净率
            turnover_rate=None,  # 新浪源不含换手率
            timestamp=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=8))
            ).isoformat(timespec="seconds"),
        )
        return DataResult(
            data=[quote.to_dict()], source="akshare",
            meta={"rows": 1, "symbol": symbol, "upstream": "sina"},
        )
