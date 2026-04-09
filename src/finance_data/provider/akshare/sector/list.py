"""行业板块列表 - akshare 实现（东财源，需绕过代理）"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.sector.list import SectorInfo
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


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class AkshareSectorList:
    def get_sector_list(self) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_board_industry_name_em()
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_name_em", str(e), "network"
            ) from e
        except Exception as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_name_em", str(e), "data"
            ) from e

        if df is None or df.empty:
            raise DataFetchError(
                "akshare", "stock_board_industry_name_em", "无数据", "data"
            )

        rows = [
            SectorInfo(
                name=str(r.get("板块名称", "")),
                code=str(r.get("板块代码", "")),
                price=_flt(r.get("最新价")),
                pct_chg=_flt(r.get("涨跌幅")),
                pct_chg_amount=_flt(r.get("涨跌额")),
                market_cap=_flt(r.get("总市值")),
                turnover=_flt(r.get("换手率")),
                up_count=_opt_int(r.get("上涨家数")),
                down_count=_opt_int(r.get("下跌家数")),
                leader_stock=str(r.get("领涨股票", "")),
                leader_pct_chg=_flt(r.get("领涨股票-涨跌幅")),
            ).to_dict()
            for _, r in df.iterrows()
        ]

        return DataResult(
            data=rows, source="akshare", meta={"rows": len(rows), "upstream": "em"}
        )
