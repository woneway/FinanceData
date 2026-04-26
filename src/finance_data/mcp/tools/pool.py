"""MCP tools — pool domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.pool import (
    zt_pool, strong_stocks, previous_zt, zbgc_pool,
    limit_list, kpl_list, limit_step,
)


@mcp.tool()
async def tool_get_zt_pool_daily(date: str) -> str:
    """
    获取涨停股池（首板/连板检测）。

    数据源: 仅 akshare（东财）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_chg(涨跌幅%)、price(最新价)、
        amount(成交额元)、float_mv/total_mv(流通/总市值元)、turnover(换手率%)、
        seal_amount(封板资金元)、first_seal_time/last_seal_time(首末封板时间HHMMSS)、
        open_times(炸板次数)、continuous_days(连板数)、industry(行业)
    """
    return _invoke_tool_json("tool_get_zt_pool_daily", {"date": date})


@mcp.tool()
async def tool_get_strong_stocks_daily(date: str) -> str:
    """
    获取强势股池（60日新高/量比放大的龙头股）。

    数据源: 仅 akshare（东财）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_chg(涨跌幅%)、price、
        limit_price(涨停价)、amount(成交额元)、float_mv/total_mv(流通/总市值元)、
        turnover(换手率%)、volume_ratio(量比)、is_new_high(是否创新高)、
        reason(入选理由)、industry(行业)
    """
    return _invoke_tool_json("tool_get_strong_stocks_daily", {"date": date})


@mcp.tool()
async def tool_get_previous_zt_daily(date: str) -> str:
    """
    获取昨日涨停今日数据（低吸检测：昨日涨停股的今日表现）。

    数据源: 仅 akshare（东财）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 今日交易日期 YYYYMMDD，接口自动返回昨日涨停股今日数据

    Returns:
        JSON 列表，每条包含：symbol、name、pct_chg(今日涨跌幅%)、price(今日最新价)、
        limit_price(昨日涨停价)、amount(今日成交额元)、float_mv/total_mv、turnover、
        prev_seal_time(昨日封板时间HHMMSS)、prev_continuous_days(昨日连板数)、industry
    """
    return _invoke_tool_json("tool_get_previous_zt_daily", {"date": date})


@mcp.tool()
async def tool_get_zbgc_pool_daily(date: str) -> str:
    """
    获取炸板股池（今日冲板后开板，补充低吸候选）。

    数据源: 仅 akshare（东财）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_chg(涨跌幅%)、price、
        limit_price(涨停价)、amount(成交额元)、float_mv/total_mv、turnover、
        first_seal_time(首次封板时间)、open_times(炸板次数)、amplitude(振幅%)、industry
    """
    return _invoke_tool_json("tool_get_zbgc_pool_daily", {"date": date})


@mcp.tool()
async def tool_get_limit_list_history(
    trade_date: str = "",
    limit_type: str = "涨停池",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取同花顺涨跌停榜单，支持日期范围查询。

    数据源: tushare(limit_list_ths)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（20231101至今）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        limit_type: 涨停池/连扳池/炸板池/跌停池/冲刺涨停
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条记录包含：symbol(代码)、name(名称)、price(收盘价元)、
        pct_chg(涨跌幅%)、limit_type(板单类别)、open_num(打开次数)、
        lu_desc(涨停原因)、tag(涨停标签)、status(涨停状态)、
        limit_order(封单量元)、limit_amount(封单额元)、turnover_rate(换手率%)、
        limit_up_suc_rate(近一年封板率)、first_lu_time(首次涨停时间)、
        last_lu_time(最后涨停时间)、first_ld_time(首次跌停时间)、
        last_ld_time(最后跌停时间)、lu_limit_order(最大封单元)、
        turnover(成交额元)、sum_float(总市值亿元)、free_float(实际流通元)、
        rise_rate(涨速)、market_type(股票类型HS/GEM/STAR)

    Note:
        first_lu_time/last_lu_time 仅涨停池有值；first_ld_time/last_ld_time 仅跌停池有值。
        单次最大4000条，跨多日查询时注意限量。
    """
    return _invoke_tool_json(
        "tool_get_limit_list_history",
        {
            "trade_date": trade_date,
            "limit_type": limit_type,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@mcp.tool()
async def tool_get_kpl_list_history(
    trade_date: str = "", tag: str = "涨停",
    start_date: str = "", end_date: str = "",
) -> str:
    """
    获取开盘啦榜单数据，支持日期范围查询。

    数据源: tushare(kpl_list)
    实时性: 日频
    历史查询: 支持（start_date/end_date）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        tag: 涨停/跌停/炸板/自然涨停/竞价
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    return _invoke_tool_json(
        "tool_get_kpl_list_history",
        {
            "trade_date": trade_date,
            "tag": tag,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@mcp.tool()
async def tool_get_limit_step_history(
    trade_date: str = "", start_date: str = "", end_date: str = "",
) -> str:
    """
    获取涨停连板天梯，支持日期范围查询。

    数据源: tushare(limit_step)
    实时性: 日频
    历史查询: 支持（start_date/end_date）

    Args:
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    return _invoke_tool_json(
        "tool_get_limit_step_history",
        {"trade_date": trade_date, "start_date": start_date, "end_date": end_date},
    )
