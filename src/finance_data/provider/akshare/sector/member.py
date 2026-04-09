"""行业板块成分股 - akshare 实现（东财源，需绕过代理）"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.sector.member import SectorMember
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


def _opt_flt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


class AkshareSectorMember:
    def get_sector_member(self, symbol: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_board_industry_cons_em(symbol=symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_cons_em", str(e), "network"
            ) from e
        except Exception as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_cons_em", str(e), "data"
            ) from e

        if df is None or df.empty:
            raise DataFetchError(
                "akshare", "stock_board_industry_cons_em", "无数据", "data"
            )

        rows = [
            SectorMember(
                symbol=str(r.get("代码", "")),
                name=str(r.get("名称", "")),
                price=_flt(r.get("最新价")),
                pct_chg=_flt(r.get("涨跌幅")),
                pct_chg_amount=_flt(r.get("涨跌额")),
                volume=_flt(r.get("成交量")),
                amount=_flt(r.get("成交额")),
                amplitude=_flt(r.get("振幅")),
                high=_flt(r.get("最高")),
                low=_flt(r.get("最低")),
                open=_flt(r.get("今开")),
                prev_close=_flt(r.get("昨收")),
                turnover=_flt(r.get("换手率")),
                pe_ratio=_opt_flt(r.get("市盈率-动态")),
                pb_ratio=_opt_flt(r.get("市净率")),
            ).to_dict()
            for _, r in df.iterrows()
        ]

        return DataResult(
            data=rows,
            source="akshare",
            meta={"rows": len(rows), "symbol": symbol, "upstream": "em"},
        )
