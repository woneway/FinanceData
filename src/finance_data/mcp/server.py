"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.types import DataFetchError

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")


@mcp.tool()
async def tool_get_stock_info(symbol: str) -> str:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含股票代码、名称、行业、上市时间等
    """
    try:
        result = get_stock_info(symbol)
        return json.dumps(
            {"data": result.data, "source": result.source, "meta": result.meta},
            ensure_ascii=False,
            indent=2,
        )
    except DataFetchError as e:
        logger.error(f"get_stock_info 失败: {e}")
        return json.dumps({"error": str(e), "kind": e.kind}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"get_stock_info 未知错误: {e}", exc_info=True)
        return json.dumps({"error": f"未知错误: {e}"}, ensure_ascii=False)
