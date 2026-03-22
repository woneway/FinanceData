"""市场统计 - akshare"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.market.models import MarketStats
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


def get_market_stats() -> DataResult:
    """获取当日市场涨跌统计。"""
    try:
        with _no_proxy():
            df = ak.stock_zh_a_spot_em()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", "无数据", "data")

    pct = df["涨跌幅"].fillna(0)
    up = int((pct > 0).sum())
    down = int((pct < 0).sum())
    flat = int((pct == 0).sum())
    total_amount = float(df["成交额"].sum()) if "成交额" in df.columns else None

    stats = MarketStats(
        date=datetime.date.today().strftime("%Y%m%d"),
        total_count=len(df),
        up_count=up,
        down_count=down,
        flat_count=flat,
        total_amount=total_amount,
    )
    return DataResult(data=[stats.to_dict()], source="akshare", meta={"rows": 1})
