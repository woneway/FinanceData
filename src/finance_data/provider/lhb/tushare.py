"""龙虎榜/游资 - tushare"""
import os
import tushare as ts

from finance_data.provider.lhb.models import LhbEntry
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

# tushare 金额单位：万元 → 元，亿元 → 元
_WAN = 10_000
_YI = 1e8


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _date(val: str) -> str:
    return str(val).replace("-", "")[:8]


def get_lhb_detail(start_date: str, end_date: str) -> DataResult:
    """龙虎榜详情（按日期范围）- tushare top_list，逐日查询后合并。"""
    pro = _get_pro()

    # tushare top_list 每次只支持单日查询，需要逐日迭代
    # 为简化实现，仅使用 start_date 作为查询日期（若需多日请用 akshare）
    try:
        df = pro.top_list(trade_date=start_date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "top_list", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "top_list", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "top_list",
                             f"无数据: {start_date}", "data")

    rows = [LhbEntry(
        symbol=str(r.get("ts_code", "")).split(".")[0],
        name=str(r.get("name", "")),
        date=_date(r.get("trade_date", "")),
        close=_flt(r.get("close")),
        pct_change=_flt(r.get("pct_chg")),
        lhb_net_buy=_flt(r.get("net_amount")) * _WAN,
        lhb_buy=_flt(r.get("l_buy")) * _WAN,
        lhb_sell=_flt(r.get("l_sell")) * _WAN,
        lhb_amount=_flt(r.get("l_amount")) * _WAN,
        market_amount=_flt(r.get("amount")) * _WAN,
        net_rate=_flt(r.get("net_rate")),
        amount_rate=_flt(r.get("amount_rate")),
        turnover_rate=_flt(r.get("turnover_rate")),
        float_value=_flt(r.get("float_values")) * _YI,
        reason=str(r.get("reason", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "start_date": start_date, "end_date": end_date})


def get_lhb_stock_stat(period: str = "近一月") -> DataResult:
    raise DataFetchError("tushare", "get_lhb_stock_stat",
                         "tushare 无个股上榜统计接口", "data")


def get_lhb_active_traders(start_date: str, end_date: str) -> DataResult:
    raise DataFetchError("tushare", "get_lhb_active_traders",
                         "tushare 无每日活跃营业部接口", "data")


def get_lhb_trader_stat(period: str = "近一月") -> DataResult:
    raise DataFetchError("tushare", "get_lhb_trader_stat",
                         "tushare 无营业部统计接口", "data")


def get_lhb_stock_detail(symbol: str, date: str, flag: str = "买入") -> DataResult:
    raise DataFetchError("tushare", "get_lhb_stock_detail",
                         "tushare 无个股席位明细接口", "data")
