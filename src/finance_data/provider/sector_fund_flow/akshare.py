"""板块资金流 - akshare

akshare stock_sector_fund_flow_rank:
- indicator: choice of {"今日", "3日", "5日", "10日"}
- sector_type: choice of {"行业资金流", "概念资金流", "地域资金流", "沪股通", "深股通"}
"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.sector_fund_flow.models import SectorFundFlow
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


def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def get_sector_fund_flow(
    indicator: str = "今日",
    sector_type: str = "行业资金流",
) -> DataResult:
    """
    获取板块资金流排名（日频）。

    数据来源：akshare stock_sector_fund_flow_rank
    注意：交易时段数据可能为空，收盘后（约15:30后）数据完整。

    Args:
        indicator: choice of {"今日", "3日", "5日", "10日"}
        sector_type: choice of {"行业资金流", "概念资金流", "地域资金流", "沪股通", "深股通"}

    Returns:
        DataResult，data 为 [SectorFundFlow.to_dict(), ...]
    """
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

    # akshare 列名前缀："今日" 对应 indicator="今日"，其余直接用 indicator 值（"3日"/"5日"/"10日"）
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
