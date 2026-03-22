"""行业板块排名 - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.sector.models import SectorRank
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


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def get_sector_rank() -> DataResult:
    """获取行业板块涨跌排名（同花顺数据源）。"""
    try:
        with _no_proxy():
            df = ak.stock_board_industry_summary_ths()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_board_industry_summary_ths", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_board_industry_summary_ths", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_board_industry_summary_ths", "无数据", "data")

    rows = [SectorRank(
        name=str(r.get("板块", "")),
        pct_chg=float(r.get("涨跌幅", 0)),
        leader_stock=str(r.get("领涨股", "")),
        leader_pct_chg=float(r.get("领涨股-涨跌幅", 0)),
        up_count=_opt_int(r.get("上涨家数")),
        down_count=_opt_int(r.get("下跌家数")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})
