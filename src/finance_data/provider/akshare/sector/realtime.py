"""行业板块排名 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.sector.realtime import SectorRank
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


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class AkshareSectorRank:
    def get_sector_rank_realtime(self) -> DataResult:
        # Try EastMoney first (more reliable), fallback to THS
        result = self._try_eastmoney()
        if result is None:
            result = self._try_ths()
        if result is None:
            raise DataFetchError("akshare", "stock_board_industry", "无数据", "data")
        return result

    def _try_eastmoney(self) -> DataResult | None:
        try:
            with _no_proxy():
                df = ak.stock_board_industry_name_em()
        except Exception:
            return None
        if df is None or df.empty:
            return None
        rows = [SectorRank(
            name=str(r.get("板块名称", "")),
            pct_chg=float(r.get("涨跌幅", 0)),
            leader_stock=str(r.get("领涨股票", "")),
            leader_pct_chg=float(r.get("领涨股票-涨跌幅", 0)),
            up_count=_opt_int(r.get("上涨家数")),
            down_count=_opt_int(r.get("下跌家数")),
        ).to_dict() for _, r in df.iterrows()]
        return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})

    def _try_ths(self) -> DataResult | None:
        try:
            with _no_proxy():
                df = ak.stock_board_industry_summary_ths()
        except Exception:
            return None
        if df is None or df.empty:
            return None
        rows = [SectorRank(
            name=str(r.get("板块", "")),
            pct_chg=float(r.get("涨跌幅", 0)),
            leader_stock=str(r.get("领涨股", "")),
            leader_pct_chg=float(r.get("领涨股-涨跌幅", 0)),
            up_count=_opt_int(r.get("上涨家数")),
            down_count=_opt_int(r.get("下跌家数")),
        ).to_dict() for _, r in df.iterrows()]
        return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})
