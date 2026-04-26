"""MCP tools — kline domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.kline import (
    daily_kline_history, weekly_kline_history,
    monthly_kline_history, minute_kline_history,
)


@mcp.tool()
async def tool_get_kline_daily_history(
    symbol: str,
    start: str = "20240101",
    end: str = "",
    adj: str = "qfq",
) -> str:
    """
    获取个股历史日线行情。

    数据源: tushare 优先，akshare(腾讯) fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 股票代码，如 "000001"
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume(股)、amount(元)、pct_chg(%)
    """
    return _invoke_tool_json(
        "tool_get_kline_daily_history",
        {"symbol": symbol, "start": start, "end": end, "adj": adj},
    )


@mcp.tool()
async def tool_get_kline_weekly_history(
    symbol: str,
    start: str = "20240101",
    end: str = "",
    adj: str = "qfq",
) -> str:
    """
    获取个股历史周线行情（每日更新，含当前未完成周）。

    数据源: tushare
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 股票代码，如 "000001"
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume(股)、amount(元)、pct_chg(%)
    """
    return _invoke_tool_json(
        "tool_get_kline_weekly_history",
        {"symbol": symbol, "start": start, "end": end, "adj": adj},
    )


@mcp.tool()
async def tool_get_kline_monthly_history(
    symbol: str,
    start: str = "20240101",
    end: str = "",
    adj: str = "qfq",
) -> str:
    """
    获取个股历史月线行情（每日更新，含当前未完成月）。

    数据源: tushare
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 股票代码，如 "000001"
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume(股)、amount(元)、pct_chg(%)
    """
    return _invoke_tool_json(
        "tool_get_kline_monthly_history",
        {"symbol": symbol, "start": start, "end": end, "adj": adj},
    )


@mcp.tool()
async def tool_get_kline_minute_history(
    symbol: str,
    period: str = "5min",
    start: str = "20260101",
    end: str = "",
    adj: str = "qfq",
) -> str:
    """
    获取个股历史分钟K线（5/15/30/60分钟）。

    数据源: baostock（免费，无需token）
    实时性: 收盘后更新（T+1）
    历史查询: 支持（2020年至今）

    Args:
        symbol: 股票代码，如 "000001"
        period: K线周期，可选 "5min" / "15min" / "30min" / "60min"
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date(日期)、time(HHmmss)、period、
        open、high、low、close、volume(股)、amount(元)

    Note:
        每日数据量：5min=48条, 15min=16条, 30min=8条, 60min=4条。
        建议控制日期范围避免返回过多数据。
    """
    return _invoke_tool_json(
        "tool_get_kline_minute_history",
        {"symbol": symbol, "period": period, "start": start, "end": end, "adj": adj},
    )
