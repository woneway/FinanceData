"""板块资金流 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.sector_fund_flow.history import SectorFundFlow
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


def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


class AkshareSectorCapitalFlow:
    def get_sector_capital_flow_history(
        self,
        indicator: str = "今日",
        sector_type: str = "行业资金流",
    ) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_sector_fund_flow_rank(
                    indicator=indicator,
                    sector_type=sector_type,
                )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_sector_fund_flow_rank", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_sector_fund_flow_rank", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_sector_fund_flow_rank",
                                 f"无数据: indicator={indicator}, sector_type={sector_type}", "data")

        p = "今日" if indicator == "今日" else indicator

        rows = []
        for _, row in df.iterrows():
            name = str(row.get("名称", "") or "")
            if not name:
                continue
            rows.append(SectorFundFlow(
                rank=int(row.get("序号", 0) or 0),
                name=name,
                pct_change=_safe_float(row.get(f"{p}涨跌幅", 0)),
                main_net_inflow=_safe_float(row.get(f"{p}主力净流入-净额", 0)),
                main_net_inflow_pct=_safe_float(row.get(f"{p}主力净流入-净占比", 0)),
                super_large_net_inflow=_safe_float(row.get(f"{p}超大单净流入-净额", 0)),
                super_large_net_inflow_pct=_safe_float(row.get(f"{p}超大单净流入-净占比", 0)),
                large_net_inflow=_safe_float(row.get(f"{p}大单净流入-净额", 0)),
                large_net_inflow_pct=_safe_float(row.get(f"{p}大单净流入-净占比", 0)),
                medium_net_inflow=_safe_float(row.get(f"{p}中单净流入-净额", 0)),
                medium_net_inflow_pct=_safe_float(row.get(f"{p}中单净流入-净占比", 0)),
                small_net_inflow=_safe_float(row.get(f"{p}小单净流入-净额", 0)),
                small_net_inflow_pct=_safe_float(row.get(f"{p}小单净流入-净占比", 0)),
                top_stock=str(row.get(f"{p}主力净流入最大股", "") or ""),
            ).to_dict())

        return DataResult(
            data=rows, source="akshare",
            meta={"rows": len(rows), "indicator": indicator, "sector_type": sector_type},
        )
