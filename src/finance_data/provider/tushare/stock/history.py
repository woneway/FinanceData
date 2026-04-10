"""股票基础信息 - tushare 实现"""
from finance_data.interface.stock.history import StockInfo
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_BASIC_FIELDS = "ts_code,symbol,name,area,industry,market,list_date,act_name"
_COMPANY_FIELDS = (
    "ts_code,com_name,chairman,manager,secretary,reg_capital,"
    "setup_date,province,city,introduction,website,email,"
    "office,main_business,exchange,employees"
)


def _str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s in ("nan", "None") else s


def _resolve_ts_code(symbol: str) -> str:
    from finance_data.provider.symbol import to_tushare
    return to_tushare(symbol)


class TushareStockHistory:
    def get_stock_info_history(self, symbol: str) -> DataResult:
        pro = get_pro()
        ts_code = _resolve_ts_code(symbol)

        try:
            df_basic = pro.stock_basic(ts_code=ts_code, fields=_BASIC_FIELDS)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stock_basic", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stock_basic", reason, kind) from e

        if df_basic.empty:
            raise DataFetchError("tushare", "stock_basic", f"未找到股票: {symbol}", "data")

        try:
            df_co = pro.stock_company(ts_code=ts_code, fields=_COMPANY_FIELDS)
        except Exception:
            df_co = None

        b = df_basic.iloc[0]
        c = df_co.iloc[0] if df_co is not None and not df_co.empty else None

        def _co(field):
            return _str(c[field]) if c is not None and field in c.index else ""

        def _co_num(field):
            if c is None or field not in c.index:
                return None
            try:
                v = c[field]
                return None if v is None or str(v) in ("nan", "None") else float(v)
            except (TypeError, ValueError):
                return None

        def _co_int(field):
            v = _co_num(field)
            return int(v) if v is not None else None

        info = StockInfo(
            symbol=symbol, name=_str(b.get("name")), industry=_str(b.get("industry")),
            list_date=_str(b.get("list_date")), exchange=_co("exchange"),
            full_name=_co("com_name"),
            established_date=_co("setup_date"), chairman=_co("chairman"),
            general_manager=_co("manager"), secretary=_co("secretary"),
            reg_capital=_co_num("reg_capital") * 10000 if _co_num("reg_capital") is not None else None,  # tushare 返回万元，统一转元
            staff_num=_co_int("employees"), website=_co("website"),
            email=_co("email"),
        )
        return DataResult(data=[info.to_dict()], source="tushare", meta={"rows": 1, "symbol": symbol})
