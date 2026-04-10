"""K线历史 - baostock 实现

稳定的免费数据源，作为 akshare/tushare 的最终 fallback。
支持日/周/月/5min/15min/30min/60min。
"""
from datetime import datetime, timedelta

from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.baostock.client import (
    baostock_session, to_baostock, _format_date, _parse_date, rs_to_list,
)

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_PERIOD_MAP = {
    "daily": "d",
    "weekly": "w",
    "monthly": "m",
    "5min": "5",
    "15min": "15",
    "30min": "30",
    "60min": "60",
}

_ADJ_MAP = {
    "qfq": "2",   # 前复权
    "hfq": "1",   # 后复权
    "none": "3",   # 不复权
}

_LOOKBACK_DAYS = {
    "daily": 10,
    "weekly": 20,
    "monthly": 40,
    "5min": 7,
    "15min": 7,
    "30min": 7,
    "60min": 7,
}


def _safe_float(val: str, default: float = 0.0) -> float:
    if not val or val.strip() == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _extend_start(start: str, period: str) -> str:
    dt = datetime.strptime(start.replace("-", ""), "%Y%m%d")
    lookback_days = _LOOKBACK_DAYS.get(period, 10)
    return (dt - timedelta(days=lookback_days)).strftime("%Y%m%d")


class BaostockKlineHistory:
    def get_kline_history(
        self, symbol: str, period: str, start: str, end: str, adj: str = "qfq",
    ) -> DataResult:
        bs_code = to_baostock(symbol)
        frequency = _PERIOD_MAP.get(period)
        if not frequency:
            raise DataFetchError("baostock", "query_history_k_data_plus",
                                 f"不支持的周期: {period}", "data")
        adjustflag = _ADJ_MAP.get(adj, "2")

        fields = "date,code,open,high,low,close,volume,amount"

        try:
            with baostock_session() as bs:
                rs = bs.query_history_k_data_plus(
                    bs_code, fields,
                    start_date=_format_date(_extend_start(start, period)),
                    end_date=_format_date(end),
                    frequency=frequency,
                    adjustflag=adjustflag,
                )
                if rs.error_code != "0":
                    raise DataFetchError("baostock", "query_history_k_data_plus",
                                         rs.error_msg, "data")
                data = rs_to_list(rs)
        except DataFetchError:
            raise
        except _NETWORK_ERRORS as e:
            raise DataFetchError("baostock", "query_history_k_data_plus",
                                 str(e), "network") from e
        except Exception as e:
            raise DataFetchError("baostock", "query_history_k_data_plus",
                                 str(e), "data") from e

        if not data:
            raise DataFetchError("baostock", "query_history_k_data_plus",
                                 f"无数据: {symbol} {start}~{end}", "data")

        # fields: date,code,open,high,low,close,volume,amount
        prev_close = 0.0
        rows = []
        start_date = start.replace("-", "")
        end_date = end.replace("-", "")
        for row in data:
            date = _parse_date(row[0])
            close = _safe_float(row[5])
            pct_chg = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0.0
            if start_date <= date <= end_date:
                rows.append(KlineBar(
                    symbol=symbol,
                    date=date,
                    period=period,
                    open=_safe_float(row[2]),
                    high=_safe_float(row[3]),
                    low=_safe_float(row[4]),
                    close=close,
                    volume=_safe_float(row[6]),   # baostock volume 已经是股
                    amount=_safe_float(row[7]),   # baostock amount 已经是元
                    pct_chg=round(pct_chg, 2),
                    adj=adj,
                ).to_dict())
            prev_close = close

        return DataResult(data=rows, source="baostock",
                          meta={"rows": len(rows), "symbol": symbol, "period": period})
