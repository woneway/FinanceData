"""大盘指数历史 K线 - akshare 实现（腾讯源）"""
import contextlib
import logging
import requests
import akshare as ak

from finance_data.interface.index.history import IndexBar
from finance_data.interface.types import DataResult, DataFetchError

logger = logging.getLogger(__name__)

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


def _parse_date(val) -> str:
    s = str(val).strip().replace("-", "").replace(" ", "")[:8]
    return s if s.isdigit() else ""


class AkshareIndexHistory:
    def get_index_history(self, symbol: str, start: str, end: str) -> DataResult:
        code = symbol.split(".")[0]
        prefix = "sh" if symbol.endswith(".SH") else "sz"
        tx_symbol = f"{prefix}{code}"

        try:
            with _no_proxy():
                df = ak.stock_zh_index_daily_tx(symbol=tx_symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_zh_index_daily_tx", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_zh_index_daily_tx", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_zh_index_daily_tx",
                                 f"无数据: {symbol}", "data")

        # 腾讯源返回 date/open/close/high/low/amount，需要计算 pct_chg
        bars = []
        prev_close = 0.0
        for _, row in df.iterrows():
            date = _parse_date(row.get("date", ""))
            if not date or date < start or date > end:
                prev_close = float(row.get("close", 0))
                continue

            close = float(row.get("close", 0))
            pct_chg = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0

            open_ = float(row.get("open", 0))
            high = float(row.get("high", 0))
            low = float(row.get("low", 0))
            amount = float(row.get("amount", 0)) * 10000  # 万元→元
            # 从成交额估算成交量
            avg = (open_ + high + low + close) / 4
            volume = round(amount / avg) if avg > 0 else 0.0

            bars.append(IndexBar(
                symbol=symbol,
                date=date,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                amount=amount,
                pct_chg=pct_chg,
            ).to_dict())
            prev_close = close

        if not bars:
            raise DataFetchError("akshare", "stock_zh_index_daily_tx",
                                 f"无数据: {symbol} {start}-{end}", "data")

        return DataResult(data=bars, source="akshare",
                          meta={"rows": len(bars), "symbol": symbol, "upstream": "tencent"})
