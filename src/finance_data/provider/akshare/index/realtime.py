"""大盘指数实时行情 - akshare 实现"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.interface.index.realtime import IndexQuote
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


class AkshareIndexQuote:
    def get_index_quote_realtime(self, symbol: str) -> DataResult:
        from finance_data.provider.symbol import to_sina
        sina_code = to_sina(symbol)
        try:
            with _no_proxy():
                df = ak.stock_zh_index_spot_sina()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "data") from e

        row_df = df[df["代码"] == sina_code]
        if row_df.empty:
            raise DataFetchError("akshare", "stock_zh_index_spot_sina",
                                 f"未找到指数: {symbol}", "data")
        row = row_df.iloc[0]
        quote = IndexQuote(
            symbol=symbol,
            name=str(row.get("名称", "")),
            price=float(row.get("最新价", 0)),
            pct_chg=float(row.get("涨跌幅", 0)),
            volume=float(row.get("成交量", 0)) * 100,  # 手→股
            amount=float(row.get("成交额", 0)),
            timestamp=datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=8))
            ).isoformat(timespec="seconds"),
        )
        return DataResult(data=[quote.to_dict()], source="akshare",
                          meta={"rows": 1, "symbol": symbol})
