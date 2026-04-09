"""交易日历 - baostock 实现"""
from finance_data.interface.calendar.history import TradeDate
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.baostock.client import (
    baostock_session, _format_date, _parse_date, rs_to_list,
)

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class BaostockTradeCalendar:
    def get_trade_calendar_history(self, start: str, end: str) -> DataResult:
        try:
            with baostock_session() as bs:
                rs = bs.query_trade_dates(
                    start_date=_format_date(start),
                    end_date=_format_date(end),
                )
                if rs.error_code != "0":
                    raise DataFetchError("baostock", "query_trade_dates",
                                         rs.error_msg, "data")
                data = rs_to_list(rs)
        except DataFetchError:
            raise
        except _NETWORK_ERRORS as e:
            raise DataFetchError("baostock", "query_trade_dates",
                                 str(e), "network") from e
        except Exception as e:
            raise DataFetchError("baostock", "query_trade_dates",
                                 str(e), "data") from e

        if not data:
            raise DataFetchError("baostock", "query_trade_dates",
                                 f"无数据: {start}~{end}", "data")

        # fields: calendar_date, is_trading_day
        rows = [TradeDate(
            date=_parse_date(row[0]),
            is_open=row[1] == "1",
        ).to_dict() for row in data]

        return DataResult(data=rows, source="baostock",
                          meta={"rows": len(rows)})
