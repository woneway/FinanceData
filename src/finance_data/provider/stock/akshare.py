"""
股票基础信息接口
数据源: akshare (雪球)
"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.stock.models import StockInfo
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


@contextlib.contextmanager
def _no_proxy():
    """临时禁用 requests 代理（含 macOS 系统代理），akshare 国内数据源直连更稳定。"""
    orig_init = requests.Session.__init__

    def _init_no_proxy(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.trust_env = False

    requests.Session.__init__ = _init_no_proxy
    try:
        yield
    finally:
        requests.Session.__init__ = orig_init


def _to_xq_symbol(symbol: str) -> str:
    """将纯数字代码转换为雪球格式（SZ000001 / SH600519）。"""
    if symbol.startswith(("SH", "SZ")):
        return symbol
    if symbol.startswith("6"):
        return f"SH{symbol}"
    return f"SZ{symbol}"


def _ms_to_date(ms) -> str:
    """Unix 毫秒时间戳转 YYYYMMDD 字符串。"""
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000).strftime("%Y%m%d")
    except Exception:
        return str(ms)


def _str(val) -> str:
    """安全转字符串，过滤 None/nan。"""
    import math
    if val is None:
        return ""
    try:
        if math.isnan(float(val)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val).strip()


def _parse_stock_info(symbol: str, df) -> StockInfo:
    """将雪球 DataFrame 解析为 StockInfo。"""
    rows = {row["item"]: row["value"] for _, row in df.iterrows()}

    industry_raw = rows.get("affiliate_industry") or {}
    industry = industry_raw.get("ind_name", "") if isinstance(industry_raw, dict) else ""

    listed_ms = rows.get("listed_date")
    list_date = _ms_to_date(listed_ms) if listed_ms else ""

    established_ms = rows.get("established_date")
    established_date = _ms_to_date(established_ms) if established_ms else ""

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

    # exchange 从 symbol 推导（雪球接口不直接提供）
    exchange = "SSE" if symbol.startswith("6") else "SZSE"

    return StockInfo(
        symbol=symbol,
        name=_str(rows.get("org_short_name_cn")),
        industry=industry,
        list_date=list_date,
        area=_str(rows.get("provincial_name")),
        market="",          # 雪球无市场分类
        city="",            # 雪球无独立城市字段
        exchange=exchange,
        ts_code="",         # 雪球无 ts_code
        full_name=_str(rows.get("org_name_cn")),
        established_date=established_date,
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


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        DataResult，data 为 [StockInfo.to_dict()]

    Raises:
        DataFetchError: 网络错误或数据错误
    """
    xq_symbol = _to_xq_symbol(symbol)

    try:
        with _no_proxy():
            df = ak.stock_individual_basic_info_xq(symbol=xq_symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_basic_info_xq",
            reason=str(e),
            kind="network",
        ) from e
    except Exception as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_basic_info_xq",
            reason=str(e),
            kind="data",
        ) from e

    info = _parse_stock_info(symbol, df)
    return DataResult(
        data=[info.to_dict()],
        source="akshare",
        meta={"rows": 1, "symbol": symbol},
    )
