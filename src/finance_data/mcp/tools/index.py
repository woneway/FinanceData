"""MCP tools — index domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.index import index_quote, index_history


@mcp.tool()
async def tool_get_index_quote_realtime(symbol: str = "000001.SH") -> str:
    """
    获取大盘指数实时行情。

    数据源: akshare(新浪) 优先，xueqiu fallback
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）

    Returns:
        JSON 列表，每条包含 symbol、name、price(点)、pct_chg(%)、
        volume(股)、amount(元)、timestamp(ISO 8601)
    """
    return _invoke_tool_json("tool_get_index_quote_realtime", {"symbol": symbol})


@mcp.tool()
async def tool_get_index_kline_history(
    symbol: str = "000001.SH",
    start: str = "20240101",
    end: str = "",
) -> str:
    """
    获取大盘指数历史 K线。

    数据源: tushare 优先，xueqiu fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume、amount、pct_chg
    """
    return _invoke_tool_json(
        "tool_get_index_kline_history",
        {"symbol": symbol, "start": start, "end": end},
    )
