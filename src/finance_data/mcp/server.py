"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.provider.akshare.stock import get_stock_info as akshare_get_stock_info
from finance_data.provider.tushare.stock import get_stock_info as tushare_get_stock_info
from finance_data.provider.types import DataFetchError

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")


def _to_json(result) -> str:
    return json.dumps(
        {"data": result.data, "source": result.source, "meta": result.meta},
        ensure_ascii=False,
        indent=2,
    )


def _error_json(e: Exception) -> str:
    if isinstance(e, DataFetchError):
        return json.dumps({"error": str(e), "kind": e.kind}, ensure_ascii=False)
    return json.dumps({"error": f"未知错误: {e}"}, ensure_ascii=False)


@mcp.tool()
async def tool_get_stock_info(symbol: str) -> str:
    """
    获取个股基本信息（akshare 数据源）。

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含股票代码、名称、行业、上市时间等
    """
    try:
        return _to_json(akshare_get_stock_info(symbol))
    except Exception as e:
        logger.error(f"akshare get_stock_info 失败: {e}")
        return _error_json(e)


@mcp.tool()
async def tool_get_stock_info_tushare(symbol: str) -> str:
    """
    获取个股基本信息（tushare 数据源，需设置 TUSHARE_TOKEN）。

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含 ts_code、名称、行业、上市日期、地区、市场等
    """
    try:
        return _to_json(tushare_get_stock_info(symbol))
    except Exception as e:
        logger.error(f"tushare get_stock_info 失败: {e}")
        return _error_json(e)
