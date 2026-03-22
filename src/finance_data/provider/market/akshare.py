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
    """获取当日市场涨跌统计（乐估数据源）。"""
    try:
        with _no_proxy():
            df = ak.stock_market_activity_legu()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_market_activity_legu", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_market_activity_legu", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_market_activity_legu", "无数据", "data")

    item_map = dict(zip(df["item"], df["value"]))
    up = int(item_map.get("上涨", 0) or 0)
    down = int(item_map.get("下跌", 0) or 0)
    flat = int(item_map.get("平盘", 0) or 0)

    # 统计日期由接口返回，格式如 "2026-03-20 15:00:00"
    date_str = str(item_map.get("统计日期", ""))
    date = date_str[:10].replace("-", "") if date_str else datetime.date.today().strftime("%Y%m%d")

    stats = MarketStats(
        date=date,
        total_count=up + down + flat,
        up_count=up,
        down_count=down,
        flat_count=flat,
        total_amount=None,
    )
    return DataResult(data=[stats.to_dict()], source="akshare", meta={"rows": 1})
