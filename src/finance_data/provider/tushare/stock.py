"""
股票基础信息接口
数据源: tushare pro
"""
import os

import tushare as ts

from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_FIELDS = "ts_code,name,industry,list_date,area,market"


def _get_pro():
    """初始化 tushare pro API，token 从环境变量读取。"""
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError(
            source="tushare",
            func="init",
            reason="TUSHARE_TOKEN 环境变量未设置",
            kind="auth",
        )
    return ts.pro_api(token=token)


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

    records = df.to_dict(orient="records")
    return DataResult(
        data=records,
        source="tushare",
        meta={"rows": len(records), "symbol": symbol},
    )


def _resolve_ts_code(symbol: str) -> str:
    """将纯数字代码转换为 tushare ts_code 格式。"""
    if "." in symbol:
        return symbol
    # 深交所：000/001/002/003/300 开头；上交所：600/601/603/605/688 开头
    if symbol.startswith(("6",)):
        return f"{symbol}.SH"
    return f"{symbol}.SZ"
