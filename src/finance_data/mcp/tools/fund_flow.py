"""MCP tools — fund_flow domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.fund_flow import board_moneyflow, market_moneyflow


@mcp.tool()
async def tool_get_dc_board_moneyflow_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    ts_code: str = "",
    content_type: str = "",
) -> str:
    """
    获取东财概念及行业板块资金流向。

    数据源: tushare(moneyflow_ind_dc)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        ts_code: 板块代码，如 "BK1032"
        content_type: 概念/行业/地域

    Returns:
        JSON 列表，每条包含：trade_date、ts_code(板块代码)、name(板块名)、
        content_type(概念/行业/地域)、pct_chg(涨跌幅%)、close(收盘点位)、
        net_amount(主力净流入)、net_amount_rate(净流入占比)、
        buy_lg_amount(大单买入)、buy_elg_amount(超大单买入)、rank(排名)
    """
    return _invoke_tool_json(
        "tool_get_dc_board_moneyflow_history",
        {"trade_date": trade_date, "start_date": start_date,
         "end_date": end_date, "ts_code": ts_code,
         "content_type": content_type},
    )


@mcp.tool()
async def tool_get_dc_market_moneyflow_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取大盘资金流向（沪深整体主力/散户资金流向）。

    数据源: tushare(moneyflow_mkt_dc)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：trade_date、close_sh(沪指收盘)、pct_change_sh(沪指涨跌%)、
        close_sz(深指收盘)、pct_change_sz(深指涨跌%)、net_amount(主力净流入)、
        net_amount_rate(净流入占比)、buy_lg_amount(大单)、buy_elg_amount(超大单)
    """
    return _invoke_tool_json(
        "tool_get_dc_market_moneyflow_history",
        {"trade_date": trade_date, "start_date": start_date,
         "end_date": end_date},
    )
