"""MCP tools — lhb domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.lhb import (
    lhb_detail, lhb_stock_stat, lhb_active_traders, lhb_trader_stat,
    lhb_stock_detail, lhb_inst_detail, hm_list, hm_detail,
)


@mcp.tool()
async def tool_get_lhb_detail_history(
    start_date: str,
    end_date: str,
) -> str:
    """
    获取龙虎榜每日上榜详情。

    数据源: akshare(东财) 优先，tushare fallback
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        start_date: 开始日期 YYYYMMDD，如 "20240101"
        end_date: 结束日期 YYYYMMDD，如 "20240131"

    Returns:
        JSON 列表，每条记录包含：symbol(代码)、name(名称)、date(上榜日)、
        close(收盘价)、pct_chg(涨跌幅%)、lhb_net_buy(净买额元)、
        lhb_buy/lhb_sell/lhb_amount(买入/卖出/成交额元)、
        market_amount(市场总成交额元)、net_rate/amount_rate(占比%)、
        turnover_rate(换手率%)、float_value(流通市值元)、reason(上榜原因)

    Note:
        akshare 支持完整日期范围查询；tushare 按交易日逐日查询。
    """
    return _invoke_tool_json(
        "tool_get_lhb_detail_history",
        {"start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_lhb_stock_stat_history(
    period: str = "近一月",
) -> str:
    """
    获取个股龙虎榜上榜统计。

    数据源: akshare(新浪)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 不支持（新浪源固定返回近5日统计）

    Args:
        period: 统计周期，如 "近一月"（新浪源固定返回近5日数据）

    Returns:
        JSON 列表，每条记录包含：symbol(代码)、name(名称)、times(上榜次数)、
        lhb_net_buy(净买额万元)、lhb_buy(累计买入万元)、lhb_sell(累计卖出万元)、
        lhb_amount(龙虎榜总成交万元)、inst_buy_times(买入席位数)、inst_sell_times(卖出席位数)
    """
    return _invoke_tool_json("tool_get_lhb_stock_stat_history", {"period": period})


@mcp.tool()
async def tool_get_lhb_active_traders_history(
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取每日活跃游资营业部统计。

    数据源: akshare(新浪)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 不支持（新浪源固定返回近期统计）

    Args:
        start_date: 开始日期（新浪源忽略此参数）
        end_date: 结束日期（新浪源忽略此参数）

    Returns:
        JSON 列表，每条记录包含：branch_name(营业部)、buy_count(上榜次数)、
        buy_amount(累计购买额万元)、sell_amount(累计卖出额万元)、
        net_amount(净额万元)、stocks(买入前三股票)
    """
    return _invoke_tool_json(
        "tool_get_lhb_active_traders_history",
        {"start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_lhb_trader_stat_history(
    period: str = "近一月",
) -> str:
    """
    获取营业部龙虎榜战绩排行。

    数据源: akshare(新浪)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 不支持（新浪源固定返回近期统计）

    Args:
        period: 统计周期（新浪源固定返回近期数据）

    Returns:
        JSON 列表，每条记录包含：branch_name(营业部)、times(上榜次数)、
        lhb_amount(龙虎榜成交金额万元)、buy_amount(买入额万元)、buy_times(买入席位数)、
        sell_amount(卖出额万元)、sell_times(卖出席位数)
    """
    return _invoke_tool_json("tool_get_lhb_trader_stat_history", {"period": period})


@mcp.tool()
async def tool_get_lhb_stock_detail_daily(
    symbol: str = "",
    date: str = "",
    flag: str = "买入",
) -> str:
    """
    获取个股某日龙虎榜席位明细。

    数据源: akshare(新浪)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 不支持（新浪源仅查单日）

    Args:
        symbol: 股票代码，如 "000001"（可选，为空返回当日全部上榜股）
        date: 日期 YYYYMMDD，如 "20260326"
        flag: 买入/卖出（新浪源不区分，统一返回全部）

    Returns:
        JSON 列表，每条记录包含：symbol(代码)、date(日期)、
        trade_amount(成交额万元)、seat_type(上榜指标/原因)
    """
    return _invoke_tool_json(
        "tool_get_lhb_stock_detail_daily",
        {"symbol": symbol, "date": date, "flag": flag},
    )


@mcp.tool()
async def tool_get_lhb_inst_detail_history(
    start_date: str,
    end_date: str,
) -> str:
    """
    获取龙虎榜机构买卖每日统计。

    数据源: akshare(东财)
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持

    Args:
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、date(日期)、
        close(收盘价)、pct_chg(涨跌幅%)、
        inst_buy(机构买入额元)、inst_sell(机构卖出额元)、inst_net(机构净买额元)
    """
    return _invoke_tool_json(
        "tool_get_lhb_inst_detail_history",
        {"start_date": start_date, "end_date": end_date},
    )


@mcp.tool()
async def tool_get_hm_list_snapshot() -> str:
    """
    获取市场游资名录。

    数据源: tushare(hm_list)
    实时性: 不定期更新
    """
    return _invoke_tool_json("tool_get_hm_list_snapshot", {})


@mcp.tool()
async def tool_get_hm_detail_history(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    hm_name: str = "",
) -> str:
    """
    获取游资每日交易明细。

    数据源: tushare(hm_detail)
    实时性: 日频
    历史查询: 支持（trade_date 或 start_date/end_date）
    """
    return _invoke_tool_json(
        "tool_get_hm_detail_history",
        {
            "trade_date": trade_date,
            "start_date": start_date,
            "end_date": end_date,
            "hm_name": hm_name,
        },
    )
