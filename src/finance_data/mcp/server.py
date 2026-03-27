"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import datetime
import json
import logging

from fastmcp import FastMCP

from finance_data.service.stock import stock_history
from finance_data.service.kline import kline_history
from finance_data.service.realtime import realtime_quote
from finance_data.service.index import index_quote, index_history
from finance_data.service.sector import sector_rank
from finance_data.service.chip import chip_history
from finance_data.service.fundamental import financial_summary, dividend
from finance_data.service.cashflow import stock_capital_flow
from finance_data.service.calendar import trade_calendar
from finance_data.service.market import market_realtime
from finance_data.service.lhb import (
    lhb_detail, lhb_stock_stat, lhb_active_traders, lhb_trader_stat, lhb_stock_detail,
)
from finance_data.service.north_flow import north_stock_hold
from finance_data.service.margin import margin, margin_detail
from finance_data.interface.types import DataFetchError

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")

def _to_json(result) -> str:
    return json.dumps(
        {"data": result.data, "source": result.source, "meta": result.meta},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def tool_get_stock_info_history(symbol: str) -> str:
    """
    获取个股基本信息。

    数据源: akshare 优先，tushare fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 不支持

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含股票代码、名称、行业、上市时间等
    """
    try:
        return _to_json(stock_history.get_stock_info_history(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_kline_history(
    symbol: str,
    period: str = "daily",
    start: str = "20240101",
    end: str = "",
    adj: str = "qfq",
) -> str:
    """
    获取 K线历史数据。

    数据源: akshare 优先，tushare fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 股票代码，如 "000001"
        period: daily/weekly/monthly/1min/5min/15min/30min/60min
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume、amount
    """
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = kline_history.get_kline_history(symbol, period=period, start=start, end=end, adj=adj)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_realtime_quote(symbol: str) -> str:
    """
    获取股票实时行情（含 20 分钟缓存）。

    数据源: akshare 优先，tushare fallback
    实时性: 盘中实时（T+0）
    历史查询: 不支持
    缓存: 有（20 分钟）

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，每条包含 symbol、name、price、pct_chg、volume、amount
    """
    try:
        result = realtime_quote.get_realtime_quote(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_index_quote_realtime(symbol: str = "000001.SH") -> str:
    """
    获取大盘指数实时行情。

    数据源: akshare 优先，tushare fallback
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）

    Returns:
        JSON 列表，每条包含 symbol、name、price、pct_chg、volume
    """
    try:
        result = index_quote.get_index_quote_realtime(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_index_history(
    symbol: str = "000001.SH",
    start: str = "20240101",
    end: str = "",
) -> str:
    """
    获取大盘指数历史 K线。

    数据源: akshare 优先，tushare fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD（默认当天）

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume、amount、pct_chg
    """
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = index_history.get_index_history(symbol, start=start, end=end)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_sector_rank_realtime() -> str:
    """
    获取行业板块涨跌排名（按涨跌幅排序）。

    数据源: akshare 优先，tushare fallback
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Args:
        无参数

    Returns:
        JSON 列表，每条包含 rank、name、pct_chg、volume、amount
    """
    try:
        result = sector_rank.get_sector_rank_realtime()
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_chip_distribution_history(symbol: str) -> str:
    """
    获取个股筹码分布（获利比例、平均成本、集中度）。

    数据源: akshare 优先，tushare fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 不支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 date、cost_profit_ratio(获利比例)、avg_cost(平均成本)、concentration(集中度)
    """
    try:
        result = chip_history.get_chip_distribution_history(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_financial_summary_history(symbol: str) -> str:
    """
    获取个股财务摘要（营收、净利润、ROE、毛利率）。

    数据源: akshare 优先，tushare fallback
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 period(报告期YYYYMMDD)、revenue(营收元)、net_profit(净利润元)、
        roe(净资产收益率%)、gross_margin(毛利率%)、cash_flow(经营现金流元)
    """
    try:
        result = financial_summary.get_financial_summary_history(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_dividend_history(symbol: str) -> str:
    """
    获取个股历史分红记录。

    数据源: akshare 优先，tushare fallback
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 ex_date(除权除息日)、per_share(每股分红元)、record_date(股权登记日)
    """
    try:
        result = dividend.get_dividend_history(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_stock_capital_flow_realtime(symbol: str) -> str:
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
    try:
        result = stock_capital_flow.get_stock_capital_flow_realtime(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_trade_calendar_history(start: str, end: str) -> str:
    """
    获取交易日历（is_open=true 为交易日）。

    数据源: tushare 优先，akshare fallback
    实时性: T+1_17:00 后更新
    历史查询: 支持（1990年至今）

    Args:
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含 cal_date(YYYYMMDD)、is_open(0/1)、pretrade_date
    """
    result = trade_calendar.get_trade_calendar_history(start, end)
    return _to_json(result)


@mcp.tool()
async def tool_get_lhb_detail(
    start_date: str,
    end_date: str,
) -> str:
    """
    获取龙虎榜每日上榜详情。

    数据源: akshare 优先，tushare fallback
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
        akshare 支持完整日期范围；tushare fallback 仅查询 start_date 单日。
    """
    try:
        return _to_json(lhb_detail.get_lhb_detail_history(start_date, end_date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_stock_stat(
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
    try:
        return _to_json(lhb_stock_stat.get_lhb_stock_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_active_traders(
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
    try:
        return _to_json(lhb_active_traders.get_lhb_active_traders_history(start_date, end_date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_trader_stat(
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
    try:
        return _to_json(lhb_trader_stat.get_lhb_trader_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_stock_detail(
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
    try:
        return _to_json(lhb_stock_detail.get_lhb_stock_detail_history(symbol, date, flag))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_north_stock_hold(
    market: str = "沪股通",
    indicator: str = "5日排行",
    symbol: str = "",
    trade_date: str = "",
) -> str:
    """
    获取北向资金持股明细（选股参考）。

    数据源: akshare 优先，tushare fallback
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: akshare 支持，tushare 自 2024年8月20日起改为季度披露

    Args:
        market: choice of {"沪股通", "深股通"}（akshare 专用）
        indicator: choice of {"5日排行", "10日排行", "月排行", "季排行", "年排行"}（akshare 专用）
        symbol: 股票代码（tushare 专用，如 "600000"）
        trade_date: 交易日期 YYYYMMDD（tushare 专用，如 "20240301"）

    Returns:
        JSON 列表，每条包含：symbol、name、date、close_price、pct_chg、
        hold_volume(持股数量股)、hold_market_cap(持股市值元)、hold_float_ratio(%),
        hold_total_ratio(%)、increase_5d_volume、increase_5d_cap 等（akshare 特有）

    Note:
        tushare hk_hold 自2024年8月20日起交易所停止发布日度数据，改为季度披露。
    """
    try:
        return _to_json(north_stock_hold.get_north_stock_hold_history(
            market=market, indicator=indicator, symbol=symbol, trade_date=trade_date
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_margin(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    exchange_id: str = "",
) -> str:
    """
    获取融资融券汇总数据（按交易所）。

    数据源: tushare 优先，akshare fallback
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
        rqye(融券余额元)、rqmcl(融券卖出量)、rzrqye(融资融券余额元)、rqyl(融券余量)

    Note:
        akshare 只支持单日查询；tushare 支持日期范围。
    """
    try:
        return _to_json(margin.get_margin_history(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            exchange_id=exchange_id,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_margin_detail(
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
    try:
        return _to_json(margin_detail.get_margin_detail_history(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
            ts_code=ts_code,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(market_realtime.get_market_stats_realtime())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)



# tool_get_market_north_capital 已禁用（依赖东财 stock_hsgt_fund_flow_summary_em）
# tool_get_sector_capital_flow 已禁用（依赖东财 stock_sector_fund_flow_rank）
