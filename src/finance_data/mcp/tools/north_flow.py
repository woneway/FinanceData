"""MCP tools — north_flow domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.north_flow import north_flow, north_stock_hold


@mcp.tool()
async def tool_get_north_hold_history(
    symbol: str = "",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    exchange: str = "",
) -> str:
    """
    获取北向资金持股明细，支持日期范围查询。

    数据源: tushare(hk_hold)
    实时性: 非实时，收盘后更新
    历史查询: 支持（start_date/end_date）

    Args:
        symbol: 股票代码，如 "600519.SH"
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        exchange: 市场筛选，如 "沪股通"、"深股通"、"SH"、"SZ"

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、date(日期)、
        hold_volume(持股数量股)、hold_ratio(持股占比%)、exchange(市场)

    Note:
        交易所自2024年8月20日起停止发布日度数据，改为季度披露。
    """
    return _invoke_tool_json(
        "tool_get_north_hold_history",
        {
            "symbol": symbol,
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
            "exchange": exchange,
        },
    )


@mcp.tool()
async def tool_get_north_capital_snapshot() -> str:
    """
    获取北向资金日频资金流（沪股通+深股通）。

    数据源: 仅 akshare（东财）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        无参数

    Returns:
        JSON 列表，每条包含 date(YYYYMMDD)、market(沪股通/深股通)、
        direction(北向/南向)、net_buy(成交净买额元)、net_inflow(资金净流入元)、
        balance(当日资金余额元)、up_count、flat_count、down_count
    """
    return _invoke_tool_json("tool_get_north_capital_snapshot", {})
