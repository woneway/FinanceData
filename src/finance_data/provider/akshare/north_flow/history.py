"""北向资金 - akshare 实现（东财源，需绕过代理）"""
import contextlib
import requests
import akshare as ak
from typing import Optional

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.north_flow.history import NorthFlow, NorthStockHold
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


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


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


class AkshareNorthStockHold:
    def get_north_stock_hold_history(
        self,
        market: str = "沪股通",
        indicator: str = "5日排行",
        symbol: str = "",
        trade_date: str = "",
    ) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_hsgt_hold_stock_em(market=market, indicator=indicator)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_hsgt_hold_stock_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_hsgt_hold_stock_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_hsgt_hold_stock_em", "无数据", "data")

        rows = []
        for _, row in df.iterrows():
            sym = str(row.get("代码", ""))
            if not sym.isdigit():
                continue
            rows.append(NorthStockHold(
                symbol=sym,
                name=str(row.get("名称", "") or ""),
                date=str(row.get("日期", "")).replace("-", ""),
                close_price=float(row.get("今日收盘价", 0) or 0),
                pct_change=float(row.get("今日涨跌幅", 0) or 0),
                hold_volume=float(row.get("今日持股-股数", 0) or 0),
                hold_market_cap=float(row.get("今日持股-市值", 0) or 0),
                hold_float_ratio=float(row.get("今日持股-占流通股比", 0) or 0),
                hold_total_ratio=float(row.get("今日持股-占总股本比", 0) or 0),
                increase_5d_volume=_safe_float(row.get("5日增持估计-股数")),
                increase_5d_cap=_safe_float(row.get("5日增持估计-市值")),
                increase_5d_cap_pct=_safe_float(row.get("5日增持估计-市值增幅")),
                increase_5d_float_ratio=_safe_float(row.get("5日增持估计-占流通股比")),
                increase_5d_total_ratio=_safe_float(row.get("5日增持估计-占总股本比")),
                board=str(row.get("所属板块", "") or ""),
            ).to_dict())

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "market": market, "indicator": indicator})
