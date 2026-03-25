"""筹码分布 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.chip.history import ChipDistribution
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


class AkshareChipHistory:
    def get_chip_distribution_history(self, symbol: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_cyq_em(symbol=symbol, adjust="")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_cyq_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_cyq_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_cyq_em", f"无数据: {symbol}", "data")

        rows = [ChipDistribution(
            symbol=symbol,
            date=str(r.get("日期", "")).replace("-", ""),
            avg_cost=float(r.get("平均成本", 0)),
            concentration=float(r.get("集中度", 0)),
            profit_ratio=float(r.get("获利比例", 0)),
            cost_90=float(r.get("90成本-高", 0)),
            cost_10=float(r.get("90成本-低", 0)),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol})
