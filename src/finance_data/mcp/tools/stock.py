"""MCP tools — stock domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.stock import stock_history, stock_basic_list


@mcp.tool()
async def tool_get_stock_info_snapshot(symbol: str) -> str:
    """
    获取个股基本信息。

    数据源: tushare 优先，xueqiu fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 不支持

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含 symbol、name、industry、list_date、
        area、reg_capital(注册资本元)、staff_num(员工数) 等
    """
    return _invoke_tool_json("tool_get_stock_info_snapshot", {"symbol": symbol})


@mcp.tool()
async def tool_get_stock_basic_list_snapshot(list_status: str = "L") -> str:
    """
    获取全市场股票列表（名称/行业/市场/ST标记）。

    数据源: tushare(stock_basic)
    实时性: 低频更新
    历史查询: 不支持（快照）

    Args:
        list_status: 上市状态，L=在市 D=退市 P=暂停上市（默认 L）

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、industry(行业)、
        market(主板/创业板/科创板)、list_date(上市日期)、is_st(是否ST)
    """
    return _invoke_tool_json("tool_get_stock_basic_list_snapshot", {"list_status": list_status})
