"""MCP tools — fundamental domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.chip import chip_history
from finance_data.service.fundamental import financial_summary, dividend


@mcp.tool()
async def tool_get_chip_distribution_history(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取个股筹码分布（获利比例、平均成本、集中度）。

    数据源: tushare
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（start_date/end_date 日期范围）
    """
    return _invoke_tool_json(
        "tool_get_chip_distribution_history",
        {"symbol": symbol, "start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_financial_summary_history(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取个股财务摘要（营收、净利润、ROE）。

    数据源: akshare 优先，tushare fallback，xueqiu 第三源
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持（start_date/end_date 按报告期筛选）
    """
    return _invoke_tool_json(
        "tool_get_financial_summary_history",
        {"symbol": symbol, "start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_dividend_history(symbol: str) -> str:
    """
    获取个股历史分红记录。

    数据源: akshare 优先，tushare fallback，xueqiu 第三源
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 ex_date(除权除息日)、per_share(每股分红元)、record_date(股权登记日)
    """
    return _invoke_tool_json("tool_get_dividend_history", {"symbol": symbol})
