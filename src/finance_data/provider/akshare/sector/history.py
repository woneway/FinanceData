"""行业板块历史行情 - akshare 实现（东财源，需绕过代理）"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.sector.history import SectorBar
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


class AkshareSectorHistory:
    def get_sector_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        period: str = "日k",
        adjust: str = "",
    ) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_board_industry_hist_em(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                )
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_hist_em", str(e), "network"
            ) from e
        except Exception as e:
            raise DataFetchError(
                "akshare", "stock_board_industry_hist_em", str(e), "data"
            ) from e

        if df is None or df.empty:
            raise DataFetchError(
                "akshare", "stock_board_industry_hist_em", "无数据", "data"
            )

        rows = [
            SectorBar(
                date=str(r.get("日期", "")),
                open=_flt(r.get("开盘")),
                close=_flt(r.get("收盘")),
                high=_flt(r.get("最高")),
                low=_flt(r.get("最低")),
                volume=_flt(r.get("成交量")),
                amount=_flt(r.get("成交额")),
                amplitude=_flt(r.get("振幅")),
                pct_chg=_flt(r.get("涨跌幅")),
                pct_chg_amount=_flt(r.get("涨跌额")),
                turnover=_flt(r.get("换手率")),
            ).to_dict()
            for _, r in df.iterrows()
        ]

        return DataResult(
            data=rows,
            source="akshare",
            meta={
                "rows": len(rows),
                "symbol": symbol,
                "period": period,
                "upstream": "em",
            },
        )
