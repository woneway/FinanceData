"""股票池 - akshare（涨停池/强势股/昨日涨停/炸板）"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.pool.models import (
    ZtPoolEntry, StrongStockEntry, PreviousZtEntry, ZbgcEntry,
)
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


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v  # NaN → default
    except (TypeError, ValueError):
        return default


def _int(val, default: int = 0) -> int:
    try:
        v = float(val)
        if v != v or v == float("inf") or v == float("-inf"):
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def _str(val) -> str:
    """安全字符串转换：NaN/None → 空字符串。"""
    if val is None:
        return ""
    try:
        if float(val) != float(val):  # NaN check
            return ""
    except (TypeError, ValueError):
        pass
    return str(val)


def _bool_from_str(val) -> bool:
    """将'是'/'否'或真值转换为 bool。"""
    if isinstance(val, bool):
        return val
    s = _str(val)
    return s in ("是", "True", "true", "1", "yes", "Yes")


def get_zt_pool(date: str) -> DataResult:
    """涨停股池（首板/连板检测）。date: YYYYMMDD"""
    try:
        with _no_proxy():
            df = ak.stock_zt_pool_em(date=date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zt_pool_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zt_pool_em", str(e), "data") from e

    if df is None or df.empty:
        return DataResult(data=[], source="akshare", meta={"rows": 0, "date": date})

    rows = [ZtPoolEntry(
        symbol=_str(r.get("代码", "")),
        name=_str(r.get("名称", "")),
        pct_change=_flt(r.get("涨跌幅")),
        price=_flt(r.get("最新价")),
        amount=_flt(r.get("成交额")),
        float_mv=_flt(r.get("流通市值")),
        total_mv=_flt(r.get("总市值")),
        turnover=_flt(r.get("换手率")),
        seal_amount=_flt(r.get("封板资金")),
        first_seal_time=_str(r.get("首次封板时间", "")),
        last_seal_time=_str(r.get("最后封板时间", "")),
        open_times=_int(r.get("炸板次数")),
        continuous_days=_int(r.get("连板数"), default=1),
        industry=_str(r.get("所属行业", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "date": date})


def get_strong_stocks(date: str) -> DataResult:
    """强势股池（60日新高/量比放大）。date: YYYYMMDD"""
    try:
        with _no_proxy():
            df = ak.stock_zt_pool_strong_em(date=date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zt_pool_strong_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zt_pool_strong_em", str(e), "data") from e

    if df is None or df.empty:
        return DataResult(data=[], source="akshare", meta={"rows": 0, "date": date})

    rows = [StrongStockEntry(
        symbol=_str(r.get("代码", "")),
        name=_str(r.get("名称", "")),
        pct_change=_flt(r.get("涨跌幅")),
        price=_flt(r.get("最新价")),
        limit_price=_flt(r.get("涨停价")),
        amount=_flt(r.get("成交额")),
        float_mv=_flt(r.get("流通市值")),
        total_mv=_flt(r.get("总市值")),
        turnover=_flt(r.get("换手率")),
        volume_ratio=_flt(r.get("量比")),
        is_new_high=_bool_from_str(r.get("是否新高", "")),
        reason=_str(r.get("入选理由", "")),
        industry=_str(r.get("所属行业", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "date": date})


def get_previous_zt(date: str) -> DataResult:
    """昨日涨停今日数据（低吸检测）。date: 今日 YYYYMMDD"""
    try:
        with _no_proxy():
            df = ak.stock_zt_pool_previous_em(date=date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zt_pool_previous_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zt_pool_previous_em", str(e), "data") from e

    if df is None or df.empty:
        return DataResult(data=[], source="akshare", meta={"rows": 0, "date": date})

    rows = [PreviousZtEntry(
        symbol=_str(r.get("代码", "")),
        name=_str(r.get("名称", "")),
        pct_change=_flt(r.get("涨跌幅")),
        price=_flt(r.get("最新价")),
        limit_price=_flt(r.get("涨停价")),
        amount=_flt(r.get("成交额")),
        float_mv=_flt(r.get("流通市值")),
        total_mv=_flt(r.get("总市值")),
        turnover=_flt(r.get("换手率")),
        prev_seal_time=_str(r.get("昨日封板时间", "")),
        prev_continuous_days=_int(r.get("昨日连板数"), default=1),
        industry=_str(r.get("所属行业", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "date": date})


def get_zbgc_pool(date: str) -> DataResult:
    """炸板股池（冲板后开板，低吸补充）。date: YYYYMMDD"""
    try:
        with _no_proxy():
            df = ak.stock_zt_pool_zbgc_em(date=date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zt_pool_zbgc_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zt_pool_zbgc_em", str(e), "data") from e

    if df is None or df.empty:
        return DataResult(data=[], source="akshare", meta={"rows": 0, "date": date})

    rows = [ZbgcEntry(
        symbol=_str(r.get("代码", "")),
        name=_str(r.get("名称", "")),
        pct_change=_flt(r.get("涨跌幅")),
        price=_flt(r.get("最新价")),
        limit_price=_flt(r.get("涨停价")),
        amount=_flt(r.get("成交额")),
        float_mv=_flt(r.get("流通市值")),
        total_mv=_flt(r.get("总市值")),
        turnover=_flt(r.get("换手率")),
        first_seal_time=_str(r.get("首次封板时间", "")),
        open_times=_int(r.get("炸板次数"), default=1),
        amplitude=_flt(r.get("振幅")),
        industry=_str(r.get("所属行业", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "date": date})
