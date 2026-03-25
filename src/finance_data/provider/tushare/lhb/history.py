"""龙虎榜 - tushare 实现"""
import datetime

from finance_data.interface.lhb.history import LhbEntry
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_WAN = 10_000
_YI = 1e8


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _date(val: str) -> str:
    return str(val).replace("-", "")[:8]


def _iter_dates(start: str, end: str):
    """生成 start~end 之间的工作日 (跳过周末) yyyymmdd 字符串"""
    dt = datetime.datetime.strptime(start[:8], "%Y%m%d")
    dt_end = datetime.datetime.strptime(end[:8], "%Y%m%d")
    while dt <= dt_end:
        if dt.weekday() < 5:  # Mon-Fri
            yield dt.strftime("%Y%m%d")
        dt += datetime.timedelta(days=1)


class TushareLhbDetail:
    def get_lhb_detail_history(self, start_date: str, end_date: str) -> DataResult:
        pro = get_pro()
        all_rows = []
        last_error = None

        for trade_date in _iter_dates(start_date, end_date):
            try:
                df = pro.top_list(trade_date=trade_date)
            except _NETWORK_ERRORS as e:
                raise DataFetchError("tushare", "top_list", str(e), "network") from e
            except Exception as e:
                reason = str(e)
                kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
                raise DataFetchError("tushare", "top_list", reason, kind) from e

            if df is None or df.empty:
                last_error = f"无数据: {trade_date}"
                continue

            for _, r in df.iterrows():
                all_rows.append(LhbEntry(
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
                ).to_dict())

        if not all_rows:
            raise DataFetchError("tushare", "top_list",
                                 last_error or f"无数据: {start_date}-{end_date}", "data")

        return DataResult(data=all_rows, source="tushare",
                          meta={"rows": len(all_rows), "start_date": start_date,
                                "end_date": end_date})
