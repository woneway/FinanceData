"""全市场股票列表 - tushare 实现"""
from finance_data.interface.stock.history import StockBasicEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_FIELDS = ",".join([
    "ts_code", "name", "industry", "market", "list_date",
])


def _str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s in ("nan", "None") else s


class TushareStockBasicList:
    def get_stock_basic_list(self, list_status: str = "L") -> DataResult:
        pro = get_pro()
        try:
            df = pro.stock_basic(list_status=list_status, fields=_FIELDS)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stock_basic", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stock_basic", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "stock_basic", f"无数据: list_status={list_status}", "data")

        rows = [
            StockBasicEntry(
                symbol=str(row.get("ts_code", "")),
                name=_str(row.get("name")),
                industry=_str(row.get("industry")),
                market=_str(row.get("market")),
                list_date=_str(row.get("list_date")),
                is_st="ST" in str(row.get("name", "")).upper(),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "list_status": list_status})
