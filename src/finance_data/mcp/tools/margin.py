"""MCP tools — margin domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.margin import margin, margin_detail


@mcp.tool()
async def tool_get_margin_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    exchange_id: str = "",
) -> str:
    """
    获取融资融券汇总数据（按交易所）。

    数据源: tushare
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2010年至今）

    Args:
        trade_date: 交易日期 YYYYMMDD（如 "20250110"，与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        exchange_id: choice of {"SSE", "SZSE", "BSE"}，空则返回全部

    Returns:
        JSON 列表，每条包含：date(YYYYMMDD)、exchange(SSE上交所/SZSE深交所/BSE北交所)、
        rzye(融资余额元)、rzmre(融资买入额元)、rzche(融资偿还额元)、
        rqye(融券余额元)、rqmcl(融券卖出量股)、rzrqye(融资融券余额元)、rqyl(融券余量股)

    Note:
        仅 tushare 源，支持日期范围+交易所过滤。
    """
    return _invoke_tool_json(
        "tool_get_margin_history",
        {
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
            "exchange_id": exchange_id,
        },
    )


@mcp.tool()
async def tool_get_margin_detail_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    ts_code: str = "",
) -> str:
    """
    获取融资融券个股明细。

    数据源: tushare 优先，akshare fallback
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2010年至今）

    Args:
        trade_date: 交易日期 YYYYMMDD（如 "20250110"）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        ts_code: 股票代码（如 "000001.SZ"，tushare 专用）

    Returns:
        JSON 列表，每条包含：date(YYYYMMDD)、symbol(不带后缀)、name、
        rzye(融资余额元)、rqye(融券余额元)、rzmre(融资买入额元)、
        rqyl(融券余量)、rzche(融资偿还额元)、rqchl(融券偿还量)、
        rqmcl(融券卖出量)、rzrqye(融资融券余额元)

    Note:
        akshare 只支持单日查询；tushare 支持日期范围+个股查询。
    """
    return _invoke_tool_json(
        "tool_get_margin_detail_history",
        {
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
            "ts_code": ts_code,
        },
    )
