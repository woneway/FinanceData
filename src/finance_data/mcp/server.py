"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.service.stock import stock_history
from finance_data.service.kline import daily_kline_history, weekly_kline_history, monthly_kline_history
from finance_data.service.realtime import realtime_quote
from finance_data.service.index import index_quote, index_history
from finance_data.service.board import board_index, board_member, board_daily
from finance_data.service.chip import chip_history
from finance_data.service.fundamental import financial_summary, dividend
from finance_data.service.cashflow import stock_capital_flow
from finance_data.service.calendar import trade_calendar
from finance_data.service.market import market_realtime
from finance_data.service.lhb import (
    lhb_detail, lhb_stock_stat, lhb_active_traders, lhb_trader_stat, lhb_stock_detail,
    lhb_inst_detail,
)
from finance_data.service.pool import zt_pool, strong_stocks, previous_zt, zbgc_pool
from finance_data.service.north_flow import north_flow, north_stock_hold
from finance_data.service.margin import margin, margin_detail
from finance_data.service.suspend import suspend
from finance_data.service.hot_rank import hot_rank, ths_hot
from finance_data.service.pool import limit_list, kpl_list, limit_step
from finance_data.service.lhb import hm_list, hm_detail
from finance_data.service.market import auction, auction_close
from finance_data.service.daily_market import daily_market
from finance_data.service.daily_basic import daily_basic_market
from finance_data.service.stk_limit import stk_limit
from finance_data.service.stock import stock_basic_list
from finance_data.service.technical import stock_factor
from finance_data.service.fund_flow import board_moneyflow, market_moneyflow
from finance_data.interface.types import DataFetchError
from finance_data.tool_specs.invoke import invoke_tool_spec

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")

def _to_json(result) -> str:
    return json.dumps(
        {"data": result.data, "source": result.source, "meta": result.meta},
        ensure_ascii=False,
        indent=2,
    )


def _invoke_tool_json(tool: str, params: dict) -> str:
    try:
        return _to_json(invoke_tool_spec(tool, params).result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
async def tool_get_stock_quote_realtime(symbol: str) -> str:
    """
    获取股票实时行情（价格/涨跌/量能/PE/PB/市值/换手率/量比/涨跌停价）。

    数据源: xueqiu(实时价格) + tencent(量比/流通市值/涨跌停价)
    实时性: 盘中实时（T+0）
    历史查询: 不支持
    缓存: 有（20 分钟）

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、price(当前价元)、
        pct_chg(涨跌幅%)、volume(成交量股)、amount(成交额元)、
        market_cap(总市值元)、pe(市盈率)、pb(市净率)、
        turnover_rate(换手率%)、timestamp(ISO 8601)、
        circ_market_cap(流通市值元)、volume_ratio(量比)、
        limit_up(涨停价元)、limit_down(跌停价元)、prev_close(昨收价元)

    Note:
        腾讯补充字段为 best-effort，失败时仅返回雪球核心字段。
    """
    return _invoke_tool_json("tool_get_stock_quote_realtime", {"symbol": symbol})


@mcp.tool()
async def tool_get_index_quote_realtime(symbol: str = "000001.SH") -> str:
    """
    获取大盘指数实时行情。

    数据源: akshare(新浪) 优先，xueqiu fallback
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）

    Returns:
        JSON 列表，每条包含 symbol、name、price(点)、pct_chg(%)、
        volume(股)、amount(元)、timestamp(ISO 8601)
    """
    return _invoke_tool_json("tool_get_index_quote_realtime", {"symbol": symbol})


@mcp.tool()
async def tool_get_index_kline_history(
    symbol: str = "000001.SH",
    start: str = "20240101",
    end: str = "",
) -> str:
    """
    获取大盘指数历史 K线。

    数据源: tushare 优先，xueqiu fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume、amount、pct_chg
    """
    return _invoke_tool_json(
        "tool_get_index_kline_history",
        {"symbol": symbol, "start": start, "end": end},
    )


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


@mcp.tool()
async def tool_get_capital_flow_realtime(symbol: str) -> str:
    """
    获取个股资金流向（主力净流入等）。

    数据源: 仅 akshare（tushare 无等效接口）
    实时性: 盘中实时（T+0），收盘后数据更准确
    历史查询: 不支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 date、net_inflow(主力净流入元)、main_net_inflow(主力净流入元)、
        super_large_net_inflow(超大单净流入元)、net_inflow_pct/main_net_inflow_pct/super_large_net_inflow_pct(占比%)
    """
    return _invoke_tool_json("tool_get_capital_flow_realtime", {"symbol": symbol})


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
async def tool_get_stock_factor_pro_history(
    ts_code: str = "",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取股票技术面因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI + 估值/量价）。

    数据源: tushare(stk_factor_pro)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（2005年至今）

    Args:
        ts_code: 股票代码（tushare格式），如 "000001.SZ"
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：trade_date、symbol、close(元)、volume(股)、amount(元)、
        ma5/10/20/30/60/90/250(不复权)、macd_dif/macd_dea/macd、kdj_k/kdj_d/kdj_j、
        rsi_6/12/24、boll_upper/mid/lower、cci、pe_ttm、pb、turnover_rate(%)、
        pct_chg(涨跌幅%)、total_mv(总市值元)、circ_mv(流通市值元)

    Note:
        需 5000 积分权限，单次最多 10000 条。
    """
    return _invoke_tool_json(
        "tool_get_stock_factor_pro_history",
        {"ts_code": ts_code, "trade_date": trade_date,
         "start_date": start_date, "end_date": end_date},
    )


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
