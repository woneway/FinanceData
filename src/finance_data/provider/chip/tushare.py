"""筹码分布 - tushare (cyq_perf)"""
import os
import tushare as ts

from finance_data.provider.chip.models import ChipDistribution
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


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


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def get_chip_distribution(symbol: str, **kwargs) -> DataResult:
    """获取筹码分布（tushare cyq_perf 接口）。"""
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    try:
        df = pro.cyq_perf(
            ts_code=ts_code,
            fields="ts_code,trade_date,weight_avg,winner_rate,cost_5pct,cost_95pct",
        )
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "cyq_perf", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "cyq_perf", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "cyq_perf", f"无数据: {symbol}", "data")

    rows = [ChipDistribution(
        symbol=symbol,
        date=str(r.get("trade_date", "")).replace("-", ""),
        avg_cost=float(r.get("weight_avg", 0) or 0),
        concentration=None,  # tushare cyq_perf 无集中度字段
        profit_ratio=float(r.get("winner_rate", 0) or 0),
        cost_90=float(r.get("cost_95pct", 0) or 0),   # 95th percentile ≈ 上沿
        cost_10=float(r.get("cost_5pct", 0) or 0),    # 5th percentile ≈ 下沿
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "symbol": symbol})
