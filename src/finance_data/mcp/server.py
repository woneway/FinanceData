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


@mcp.tool()
async def tool_get_stock_info(symbol: str) -> str:
    """
    获取个股基本信息。依次尝试 akshare、tushare，返回第一个成功的结果。

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含股票代码、名称、行业、上市时间等
    """
    # provider 优先级：akshare 优先，失败时 fallback 到 tushare
    providers = [
        ("akshare", akshare_get_stock_info),
        ("tushare", tushare_get_stock_info),
    ]
    errors = []
    for name, provider in providers:
        try:
            return _to_json(provider(symbol))
        except Exception as e:
            logger.warning(f"{name} get_stock_info 失败: {e}")
            errors.append(str(e))

    logger.error(f"所有 provider 均失败: {errors}")
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
