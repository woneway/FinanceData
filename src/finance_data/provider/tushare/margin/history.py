"""融资融券 - tushare 实现"""
from finance_data.interface.margin.history import MarginSummary, MarginDetail
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
class TushareMargin:
    def get_margin_history(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        exchange_id: str = "",
    ) -> DataResult:
        pro = get_pro()
        try:
            df = pro.margin(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                exchange_id=exchange_id,
            )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "margin", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "margin", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "margin",
                                 f"无数据: trade_date={trade_date}", "data")

        rows = []
        for _, row in df.iterrows():
            rows.append(MarginSummary(
                date=str(row.get("trade_date", "")).replace("-", ""),
                exchange=str(row.get("exchange_id", "")),
                rzye=float(row.get("rzye", 0) or 0),
                rzmre=float(row.get("rzmre", 0) or 0),
                rzche=float(row.get("rzche", 0) or 0),
                rqye=float(row.get("rqye", 0) or 0),
                rqmcl=float(row.get("rqmcl", 0) or 0),
                rzrqye=float(row.get("rzrqye", 0) or 0),
                rqyl=float(row.get("rqyl", 0) or 0),
            ).to_dict())

        rows.sort(key=lambda x: x["date"], reverse=True)
        return DataResult(data=rows, source="tushare",
                          meta={"rows": len(rows), "trade_date": trade_date,
                                "start_date": start_date, "end_date": end_date})


class TushareMarginDetail:
    def get_margin_detail_history(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        ts_code: str = "",
    ) -> DataResult:
        pro = get_pro()
        try:
            df = pro.margin_detail(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
                ts_code=ts_code,
            )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "margin_detail", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "margin_detail", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "margin_detail",
                                 f"无数据: trade_date={trade_date}", "data")

        rows = []
        for _, row in df.iterrows():
            ts_code_val = str(row.get("ts_code", ""))
            symbol = ts_code_val.split(".")[0] if "." in ts_code_val else ts_code_val
            rows.append(MarginDetail(
                date=str(row.get("trade_date", "")).replace("-", ""),
                symbol=symbol,
                name=str(row.get("name", "") or ""),
                rzye=float(row.get("rzye", 0) or 0),
                rqye=float(row.get("rqye", 0) or 0),
                rzmre=float(row.get("rzmre", 0) or 0),
                rqyl=float(row.get("rqyl", 0) or 0),
                rzche=float(row.get("rzche", 0) or 0),
                rqchl=float(row.get("rqchl", 0) or 0),
                rqmcl=float(row.get("rqmcl", 0) or 0),
                rzrqye=float(row.get("rzrqye", 0) or 0),
            ).to_dict())

        return DataResult(data=rows, source="tushare",
                          meta={"rows": len(rows), "trade_date": trade_date,
                                "start_date": start_date, "end_date": end_date,
                                "ts_code": ts_code})
