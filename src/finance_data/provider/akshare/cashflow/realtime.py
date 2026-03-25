"""个股资金流向 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.cashflow.realtime import FundFlow
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


class AkshareStockCapitalFlow:
    def get_stock_capital_flow_realtime(self, symbol: str) -> DataResult:
        from finance_data.provider.symbol import normalize
        code, exchange = normalize(symbol)
        market = exchange.lower()  # "sh" or "sz"
        try:
            with _no_proxy():
                df = ak.stock_individual_fund_flow(stock=code, market=market)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_individual_fund_flow",
                                 f"无数据: {symbol}", "data")

        rows = [FundFlow(
            symbol=symbol,
            date=str(r.get("日期", "")).replace("-", ""),
            net_inflow=float(r.get("主力净流入-净额", 0) or 0),
            net_inflow_pct=float(r.get("主力净流入-净占比", 0) or 0),
            main_net_inflow=float(r.get("主力净流入-净额", 0) or 0),
            main_net_inflow_pct=float(r.get("主力净流入-净占比", 0) or 0),
            super_large_net_inflow=float(r.get("超大单净流入-净额", 0) or 0),
            super_large_net_inflow_pct=float(r.get("超大单净流入-净占比", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol})
