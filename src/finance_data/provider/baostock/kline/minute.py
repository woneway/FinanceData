"""分钟K线 - baostock 实现

支持 5min/15min/30min/60min，免费无限流。
volume 已经是股，amount 已经是元，无需转换。
"""
from finance_data.interface.kline.minute import MinuteKlineBar
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.baostock.client import (
    _format_date, _parse_date, baostock_session, rs_to_list, to_baostock,
)

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_VALID_PERIODS = {"5min": "5", "15min": "15", "30min": "30", "60min": "60"}
_ADJ_MAP = {"qfq": "2", "hfq": "1", "none": "3"}
_FIELDS = "date,time,code,open,high,low,close,volume,amount"


def _safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class BaostockMinuteKline:
    def get_minute_kline_history(
        self,
        symbol: str,
        period: str,
        start: str,
        end: str,
        adj: str = "qfq",
    ) -> DataResult:
        freq = _VALID_PERIODS.get(period)
        if freq is None:
            raise DataFetchError(
                "baostock", "minute_kline",
                f"不支持的 period: {period}，可选: {', '.join(_VALID_PERIODS)}",
                "data",
            )

        adj_flag = _ADJ_MAP.get(adj, "2")
        bs_code = to_baostock(symbol)

        try:
            with baostock_session() as bs:
                rs = bs.query_history_k_data_plus(
                    bs_code, _FIELDS,
                    start_date=_format_date(start),
                    end_date=_format_date(end),
                    frequency=freq,
                    adjustflag=adj_flag,
                )
                if rs.error_code != "0":
                    raise DataFetchError(
                        "baostock", "minute_kline", rs.error_msg, "data",
                    )
                rows = rs_to_list(rs)
        except DataFetchError:
            raise
        except _NETWORK_ERRORS as e:
            raise DataFetchError(
                "baostock", "minute_kline", str(e), "network",
            ) from e
        except Exception as e:
            raise DataFetchError(
                "baostock", "minute_kline", str(e), "data",
            ) from e

        if not rows:
            raise DataFetchError(
                "baostock", "minute_kline",
                f"无数据: {symbol} {period} {start}-{end}", "data",
            )

        code_clean = symbol.split(".")[0].lstrip("shsz.")
        bars = []
        for r in rows:
            # r: [date, time, code, open, high, low, close, volume, amount]
            # time 格式: YYYYMMDDHHmmssmmm → 截取 HHmmss
            raw_time = r[1]
            time_str = raw_time[8:14] if len(raw_time) >= 14 else raw_time

            bars.append(MinuteKlineBar(
                symbol=code_clean,
                date=_parse_date(r[0]),
                time=time_str,
                period=period,
                open=_safe_float(r[3]),
                high=_safe_float(r[4]),
                low=_safe_float(r[5]),
                close=_safe_float(r[6]),
                volume=_safe_float(r[7]),
                amount=_safe_float(r[8]),
                adj=adj,
            ).to_dict())

        return DataResult(
            data=bars,
            source="baostock",
            meta={"rows": len(bars), "symbol": symbol, "period": period},
        )
