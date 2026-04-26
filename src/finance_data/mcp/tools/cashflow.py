"""MCP tools — cashflow domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.cashflow import stock_capital_flow


@mcp.tool()
async def tool_get_capital_flow_realtime(symbol: str) -> str:
    """
    获取个股资金流向（主力净流入等）。

    数据源: 仅 akshare（tushare 无等效接口）
    实时性: 盘中实时（T+0），收盘后数据更准确
    历史查询: 不支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 date、net_inflow(主力净流入元)、main_net_inflow(主力净流入元)、
        super_large_net_inflow(超大单净流入元)、net_inflow_pct/main_net_inflow_pct/super_large_net_inflow_pct(占比%)
    """
    return _invoke_tool_json("tool_get_capital_flow_realtime", {"symbol": symbol})
