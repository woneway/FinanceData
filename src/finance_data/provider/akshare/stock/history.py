"""股票基础信息 - akshare 实现"""
import contextlib
import datetime
import math
import requests
import akshare as ak

from finance_data.interface.stock.history import StockInfo
from finance_data.interface.types import DataResult, DataFetchError

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


def _to_xq_symbol(symbol: str) -> str:
    if symbol.startswith(("SH", "SZ")):
        return symbol
    return f"SH{symbol}" if symbol.startswith("6") else f"SZ{symbol}"


def _ms_to_date(ms) -> str:
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000).strftime("%Y%m%d")
    except Exception:
        return str(ms)


def _str(val) -> str:
    if val is None:
        return ""
    try:
        if math.isnan(float(val)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val).strip()


class AkshareStockHistory:
    def get_stock_info_history(self, symbol: str) -> DataResult:
        xq_symbol = _to_xq_symbol(symbol)
        try:
            with _no_proxy():
                df = ak.stock_individual_basic_info_xq(symbol=xq_symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_individual_basic_info_xq", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_individual_basic_info_xq", str(e), "data") from e

        rows = {row["item"]: row["value"] for _, row in df.iterrows()}
        industry_raw = rows.get("affiliate_industry") or {}
        industry = industry_raw.get("ind_name", "") if isinstance(industry_raw, dict) else ""
        listed_ms = rows.get("listed_date")
        established_ms = rows.get("established_date")
        reg_asset = rows.get("reg_asset")
        try:
            reg_capital = float(reg_asset) if reg_asset is not None else None
        except (TypeError, ValueError):
            reg_capital = None
        staff_raw = rows.get("staff_num")
        try:
            staff_num = int(staff_raw) if staff_raw is not None else None
        except (TypeError, ValueError):
            staff_num = None

        info = StockInfo(
            symbol=symbol,
            name=_str(rows.get("org_short_name_cn")),
            industry=industry,
            list_date=_ms_to_date(listed_ms) if listed_ms else "",
            area=_str(rows.get("provincial_name")),
            market="",
            city="",
            exchange="SSE" if symbol.startswith("6") else "SZSE",
            ts_code="",
            full_name=_str(rows.get("org_name_cn")),
            established_date=_ms_to_date(established_ms) if established_ms else "",
            main_business=_str(rows.get("main_operation_business")),
            introduction=_str(rows.get("org_cn_introduction")),
            chairman=_str(rows.get("chairman")),
            legal_representative=_str(rows.get("legal_representative")),
            general_manager=_str(rows.get("general_manager")),
            secretary=_str(rows.get("secretary")),
            reg_capital=reg_capital,
            staff_num=staff_num,
            website=_str(rows.get("org_website")),
            email=_str(rows.get("email")),
            reg_address=_str(rows.get("reg_address_cn")),
            actual_controller=_str(rows.get("actual_controller")),
        )
        return DataResult(data=[info.to_dict()], source="akshare", meta={"rows": 1, "symbol": symbol})
