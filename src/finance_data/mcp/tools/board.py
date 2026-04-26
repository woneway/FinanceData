"""MCP tools — board domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.board import board_index, board_member, board_daily


@mcp.tool()
async def tool_get_board_index_history(
    idx_type: str = "行业板块",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取东财板块索引/快照。

    数据源: tushare(dc_index)
    实时性: 日频
    历史查询: 支持（trade_date 单日快照，或 start_date/end_date 日期范围）
    """
    return _invoke_tool_json(
        "tool_get_board_index_history",
        {
            "idx_type": idx_type,
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@mcp.tool()
async def tool_get_board_member_history(
    board_name: str,
    idx_type: str = "行业板块",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取东财板块成分股列表。

    数据源: tushare(dc_index + dc_member)
    实时性: 日频
    历史查询: 支持（trade_date 单日成分，或 start_date/end_date 日期范围）
    """
    return _invoke_tool_json(
        "tool_get_board_member_history",
        {
            "board_name": board_name,
            "idx_type": idx_type,
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@mcp.tool()
async def tool_get_board_kline_history(
    board_name: str,
    idx_type: str = "行业板块",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取东财板块日行情。

    数据源: tushare(dc_index + dc_daily)
    实时性: 日频
    历史查询: 支持
    """
    return _invoke_tool_json(
        "tool_get_board_kline_history",
        {
            "board_name": board_name,
            "idx_type": idx_type,
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
