"""北向资金 - akshare 实现（东财源，需绕过代理）"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.north_flow.history import NorthFlow
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


class AkshareNorthFlow:
    def get_north_flow_history(self) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_hsgt_fund_flow_summary_em()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_hsgt_fund_flow_summary_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_hsgt_fund_flow_summary_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_hsgt_fund_flow_summary_em", "无数据", "data")

        rows = []
        for _, row in df.iterrows():
            direction = str(row.get("资金方向", ""))
            if direction != "北向":
                continue
            rows.append(NorthFlow(
                date=str(row.get("交易日", "")).replace("-", ""),
                market=str(row.get("板块", "")),
                direction=direction,
                net_buy=float(row.get("成交净买额", 0) or 0),
                net_inflow=float(row.get("资金净流入", 0) or 0),
                balance=float(row.get("当日资金余额", 0) or 0),
                up_count=int(row.get("上涨数", 0) or 0),
                flat_count=int(row.get("持平数", 0) or 0),
                down_count=int(row.get("下跌数", 0) or 0),
                index_name=str(row.get("相关指数", "") or ""),
                index_pct=float(row.get("指数涨跌幅", 0) or 0),
            ).to_dict())

        return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})
