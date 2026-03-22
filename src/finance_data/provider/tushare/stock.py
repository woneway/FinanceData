"""
股票基础信息接口
数据源: tushare pro
"""
import os

import tushare as ts

from finance_data.provider.models import StockInfo
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_FIELDS = "ts_code,name,industry,list_date,area,market"


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
    # 支持自定义 API 地址（如第三方代理），通过 TUSHARE_API_URL 环境变量配置
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"（不含市场后缀）

    Returns:
        DataResult，data 为 [{"ts_code", "name", "industry", "list_date", "area", "market"}]

    Raises:
        DataFetchError: auth / network / data 错误
    """
    pro = _get_pro()

    # tushare 格式：000001.SZ 或 000001.SH，先尝试 SZ，再尝试 SH
    ts_code = _resolve_ts_code(symbol)

    try:
        df = pro.stock_basic(ts_code=ts_code, fields=_FIELDS)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(
            source="tushare",
            func="stock_basic",
            reason=str(e),
            kind="network",
        ) from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError(
            source="tushare",
            func="stock_basic",
            reason=reason,
            kind=kind,
        ) from e

    if df.empty:
        raise DataFetchError(
            source="tushare",
            func="stock_basic",
            reason=f"未找到股票: {symbol}",
            kind="data",
        )

    row = df.iloc[0]
    info = StockInfo(
        symbol=symbol,
        name=row.get("name", ""),
        industry=row.get("industry", ""),
        list_date=row.get("list_date", ""),
        area=row.get("area", ""),
        market=row.get("market", ""),
        ts_code=row.get("ts_code", ""),
        actual_controller=row.get("act_name", ""),
    )
    return DataResult(
        data=[info.to_dict()],
        source="tushare",
        meta={"rows": 1, "symbol": symbol},
    )


def _resolve_ts_code(symbol: str) -> str:
    """将纯数字代码转换为 tushare ts_code 格式。"""
    if "." in symbol:
        return symbol
    # 深交所：000/001/002/003/300 开头；上交所：600/601/603/605/688 开头
    if symbol.startswith(("6",)):
        return f"{symbol}.SH"
    return f"{symbol}.SZ"
