"""MCP tools — market domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.calendar import trade_calendar
from finance_data.service.market import market_realtime, auction, auction_close
from finance_data.service.suspend import suspend
from finance_data.service.hot_rank import hot_rank, ths_hot
from finance_data.service.daily_market import daily_market
from finance_data.service.daily_basic import daily_basic_market
from finance_data.service.stk_limit import stk_limit


@mcp.tool()
async def tool_get_trade_calendar_history(start: str, end: str) -> str:
    """
    获取交易日历（is_open=true 为交易日）。

    数据源: tushare 优先，akshare(新浪) fallback，baostock 兜底
    实时性: T+1_17:00 后更新
    历史查询: 支持（1990年至今）

    Args:
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：date(日期YYYYMMDD)、is_open(是否交易日)
    """
    return _invoke_tool_json("tool_get_trade_calendar_history", {"start": start, "end": end})


@mcp.tool()
async def tool_get_market_stats_realtime() -> str:
    """
    获取当日市场涨跌家数统计（盘中实时）。

    数据源: 仅 akshare（tushare 无等效接口）
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        无参数

    Returns:
        JSON 列表，包含 date、up_count、down_count、flat_count、total_count、total_amount
    """
    return _invoke_tool_json("tool_get_market_stats_realtime", {})


@mcp.tool()
async def tool_get_suspend_daily(date: str) -> str:
    """
    获取停牌股票信息。

    数据源: akshare(东财) 优先，tushare(suspend_d) fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260408"

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、
        suspend_date(停牌起始日)、resume_date(复牌日期)、reason(停牌原因)
    """
    return _invoke_tool_json("tool_get_suspend_daily", {"date": date})


@mcp.tool()
async def tool_get_hot_rank_realtime() -> str:
    """
    获取热股排行（东财人气榜）。

    数据源: akshare(东财)
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        无参数

    Returns:
        JSON 列表，每条包含：rank(排名)、symbol(代码)、name(名称)、
        current(最新价)、pct_chg(涨跌幅%)、hot_rank_chg(排名变化)
    """
    return _invoke_tool_json("tool_get_hot_rank_realtime", {})


@mcp.tool()
async def tool_get_ths_hot_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取同花顺热股排行，支持日期范围查询。

    数据源: tushare(ths_hot)
    实时性: 日频（每半小时更新，取最新一期）
    历史查询: 支持（start_date/end_date）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    return _invoke_tool_json(
        "tool_get_ths_hot_history",
        {"trade_date": trade_date, "start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_auction_history(
    trade_date: str = "", start_date: str = "", end_date: str = "",
) -> str:
    """
    获取开盘集合竞价成交数据，支持日期范围查询。

    数据源: tushare(stk_auction)
    实时性: 日频（盘前更新）
    历史查询: 支持（start_date/end_date）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    return _invoke_tool_json(
        "tool_get_auction_history",
        {"trade_date": trade_date, "start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_auction_close_history(
    trade_date: str = "", start_date: str = "", end_date: str = "",
) -> str:
    """
    获取收盘集合竞价成交数据，支持日期范围查询。

    数据源: tushare(stk_auction_c)
    实时性: 日频
    历史查询: 支持（start_date/end_date）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    return _invoke_tool_json(
        "tool_get_auction_close_history",
        {"trade_date": trade_date, "start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_daily_market_history(trade_date: str) -> str:
    """
    获取全市场日线行情（OHLCV），单日返回约5000只股票。

    数据源: tushare(daily)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（单日 trade_date）

    Args:
        trade_date: 交易日期 YYYYMMDD，如 "20260414"

    Returns:
        JSON 列表，每条包含：symbol(代码)、trade_date(日期)、
        open(开盘价元)、high(最高价元)、low(最低价元)、close(收盘价元)、
        pre_close(昨收元)、change(涨跌额元)、pct_chg(涨跌幅%)、
        volume(成交量股)、amount(成交额元)
    """
    return _invoke_tool_json("tool_get_daily_market_history", {"trade_date": trade_date})


@mcp.tool()
async def tool_get_daily_basic_market_history(trade_date: str) -> str:
    """
    获取全市场日频基本面数据（换手率/量比/PE/PB/市值），单日返回约5000只股票。

    数据源: tushare(daily_basic)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（单日 trade_date）

    Args:
        trade_date: 交易日期 YYYYMMDD，如 "20260414"

    Returns:
        JSON 列表，每条包含：symbol(代码)、trade_date(日期)、close(收盘价元)、
        turnover_rate(换手率%)、turnover_rate_f(自由流通换手率%)、volume_ratio(量比)、
        pe_ttm(市盈率TTM)、pb(市净率)、total_mv(总市值元)、circ_mv(流通市值元)
    """
    return _invoke_tool_json("tool_get_daily_basic_market_history", {"trade_date": trade_date})


@mcp.tool()
async def tool_get_stk_limit_daily(trade_date: str) -> str:
    """
    获取全市场涨跌停价，单日返回约5000~7500只股票（含退市整理期）。

    数据源: tushare(stk_limit)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（单日 trade_date）

    Args:
        trade_date: 交易日期 YYYYMMDD，如 "20260414"

    Returns:
        JSON 列表，每条包含：symbol(代码)、trade_date(日期)、
        pre_close(昨收价元)、up_limit(涨停价元)、down_limit(跌停价元)
    """
    return _invoke_tool_json("tool_get_stk_limit_daily", {"trade_date": trade_date})
