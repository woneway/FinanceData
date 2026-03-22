"""
股票基础信息接口
数据源: tushare pro（stock_basic + stock_company）
"""
import os

import tushare as ts

from finance_data.provider.models import StockInfo
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_BASIC_FIELDS = "ts_code,symbol,name,area,industry,market,list_date,act_name"
_COMPANY_FIELDS = (
    "ts_code,com_name,chairman,manager,secretary,reg_capital,"
    "setup_date,province,city,introduction,website,email,"
    "office,main_business,exchange,employees"
)


def _get_pro():
    """初始化 tushare pro API，token 和 API URL 从环境变量读取。"""
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError(
            source="tushare",
            func="init",
            reason="TUSHARE_TOKEN 环境变量未设置",
            kind="auth",
        )
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _str(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s in ("nan", "None") else s


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。调用 stock_basic + stock_company 两个接口填充完整字段。

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        DataResult，data 为 [StockInfo.to_dict()]

    Raises:
        DataFetchError: auth / network / data 错误
    """
    pro = _get_pro()
    ts_code = _resolve_ts_code(symbol)

    # --- stock_basic ---
    try:
        df_basic = pro.stock_basic(ts_code=ts_code, fields=_BASIC_FIELDS)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(source="tushare", func="stock_basic",
                             reason=str(e), kind="network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError(source="tushare", func="stock_basic",
                             reason=reason, kind=kind) from e

    if df_basic.empty:
        raise DataFetchError(source="tushare", func="stock_basic",
                             reason=f"未找到股票: {symbol}", kind="data")

    # --- stock_company ---
    try:
        df_co = pro.stock_company(ts_code=ts_code, fields=_COMPANY_FIELDS)
    except Exception:
        df_co = None  # company 接口失败不影响主流程，降级处理

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
        symbol=symbol,
        name=_str(b.get("name")),
        industry=_str(b.get("industry")),
        list_date=_str(b.get("list_date")),
        area=_str(b.get("area")),
        market=_str(b.get("market")),
        city=_co("city"),
        exchange=_co("exchange"),
        ts_code=_str(b.get("ts_code")),
        full_name=_co("com_name"),
        established_date=_co("setup_date"),
        main_business=_co("main_business"),
        introduction=_co("introduction"),
        chairman=_co("chairman"),
        legal_representative="",    # tushare 无此字段
        general_manager=_co("manager"),
        secretary=_co("secretary"),
        reg_capital=_co_num("reg_capital"),
        staff_num=_co_int("employees"),
        website=_co("website"),
        email=_co("email"),
        reg_address=_co("office"),
        actual_controller=_str(b.get("act_name")),
    )

    return DataResult(
        data=[info.to_dict()],
        source="tushare",
        meta={"rows": 1, "symbol": symbol},
    )


def _resolve_ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    if symbol.startswith("6"):
        return f"{symbol}.SH"
    return f"{symbol}.SZ"
