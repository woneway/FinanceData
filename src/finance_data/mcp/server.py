"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.service.stock import stock_history
from finance_data.service.kline import kline_history
from finance_data.service.realtime import realtime_quote
from finance_data.service.index import index_quote, index_history
from finance_data.service.sector import sector_rank
from finance_data.service.chip import chip_history
from finance_data.service.fundamental import financial_summary, dividend, earnings_forecast
from finance_data.service.cashflow import stock_capital_flow
from finance_data.service.calendar import trade_calendar
from finance_data.service.market import market_realtime
from finance_data.service.lhb import (
    lhb_detail, lhb_stock_stat, lhb_active_traders, lhb_trader_stat, lhb_stock_detail,
)
from finance_data.service.pool import zt_pool, strong_stocks, previous_zt, zbgc_pool
from finance_data.service.north_flow import north_flow, north_stock_hold
from finance_data.service.margin import margin, margin_detail
from finance_data.service.sector_fund_flow import sector_capital_flow
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
    end: str = "20241231",
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
        end: 结束日期 YYYYMMDD
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume、amount
    """
    result = kline_history.get_kline_history(symbol, period=period, start=start, end=end, adj=adj)
    return _to_json(result)


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
        JSON 列表，每条包含 symbol、name、price、pct_change、volume、amount
    """
    result = realtime_quote.get_realtime_quote(symbol)
    return _to_json(result)


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
        JSON 列表，每条包含 symbol、name、price、pct_change、volume
    """
    result = index_quote.get_index_quote_realtime(symbol)
    return _to_json(result)


@mcp.tool()
async def tool_get_index_history(
    symbol: str = "000001.SH",
    start: str = "20240101",
    end: str = "20241231",
) -> str:
    """
    获取大盘指数历史 K线。

    数据源: akshare 优先，tushare fallback
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（1990年至今）

    Args:
        symbol: 指数代码，如 000001.SH（上证）/ 399001.SZ（深证）
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含 date、open、high、low、close、volume
    """
    result = index_history.get_index_history(symbol, start=start, end=end)
    return _to_json(result)


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
        JSON 列表，每条包含 rank、name、pct_change、volume、amount
    """
    result = sector_rank.get_sector_rank_realtime()
    return _to_json(result)


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
    result = chip_history.get_chip_distribution_history(symbol)
    return _to_json(result)


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
    result = financial_summary.get_financial_summary_history(symbol)
    return _to_json(result)


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
    result = dividend.get_dividend_history(symbol)
    return _to_json(result)


@mcp.tool()
async def tool_get_earnings_forecast_history(symbol: str) -> str:
    """
    获取个股业绩预告。

    数据源: akshare 优先
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，包含 period(报告期)、forecast_type(预告类型)、
        net_profit_min/net_profit_max(预计净利润区间元)、
        change_low/change_high(变动幅度下限/上限%)、summary(变动原因)
    """
    result = earnings_forecast.get_earnings_forecast_history(symbol)
    return _to_json(result)


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
    result = stock_capital_flow.get_stock_capital_flow_realtime(symbol)
    return _to_json(result)


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
        close(收盘价)、pct_change(涨跌幅%)、lhb_net_buy(净买额元)、
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
async def tool_get_lhb_stock_stat(period: str = "近一月") -> str:
    """
    获取个股上榜统计（哪些股票频繁上龙虎榜）。

    数据源: 仅 akshare
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        period: 统计周期，choice of {"近一月", "近三月", "近六月", "近一年"}

    Returns:
        JSON 列表，每条包含：symbol、name、last_date(最近上榜日)、times(上榜次数)、
        lhb_net_buy/lhb_buy/lhb_sell/lhb_amount(龙虎榜资金)、
        inst_buy_times/inst_sell_times(机构买卖次数)、inst_net_buy(机构净买额)
    """
    try:
        return _to_json(lhb_stock_stat.get_lhb_stock_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_active_traders(
    start_date: str,
    end_date: str,
) -> str:
    """
    获取每日活跃游资营业部（龙虎榜席位追踪）。

    数据源: 仅 akshare
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：branch_name(营业部名称)、date(上榜日)、
        buy_count/sell_count(买入/卖出个股数)、
        buy_amount/sell_amount/net_amount(买入/卖出/净额元)、
        stocks(买入股票列表)
    """
    try:
        return _to_json(lhb_active_traders.get_lhb_active_traders_history(start_date, end_date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_trader_stat(period: str = "近一月") -> str:
    """
    获取营业部统计（游资战绩排行）。

    数据源: 仅 akshare
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        period: 统计周期，choice of {"近一月", "近三月", "近六月", "近一年"}

    Returns:
        JSON 列表，每条包含：branch_name(营业部名称)、lhb_amount(龙虎榜成交金额元)、
        times(上榜次数)、buy_amount/buy_times(买入额元/次数)、
        sell_amount/sell_times(卖出额元/次数)
    """
    try:
        return _to_json(lhb_trader_stat.get_lhb_trader_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_stock_detail(
    symbol: str,
    date: str,
    flag: str = "买入",
) -> str:
    """
    获取个股某日龙虎榜席位明细（具体游资/机构）。

    数据源: 仅 akshare
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        symbol: 股票代码，如 "600077"
        date: 上榜日期 YYYYMMDD，如 "20240320"（必须是该股实际上榜的日期，
              建议先调用 tool_get_lhb_detail 确认有效上榜日）
        flag: "买入" 或 "卖出"

    Returns:
        JSON 列表，每条包含：symbol、date、flag、branch_name(交易营业部)、
        trade_amount(交易金额元，买入方向为买入额/卖出方向为卖出额)、
        buy_rate(买入占总成交%)、sell_rate(卖出占总成交%)、
        net_amount(净额元)、seat_type(席位类型)
    """
    try:
        return _to_json(lhb_stock_detail.get_lhb_stock_detail_history(symbol, date, flag))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_zt_pool(date: str) -> str:
    """
    获取涨停股池（首板/连板检测）。

    数据源: 仅 akshare
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_change(涨跌幅%)、price(最新价)、
        amount(成交额元)、float_mv/total_mv(流通/总市值元)、turnover(换手率%)、
        seal_amount(封板资金元)、first_seal_time/last_seal_time(首末封板时间HHMMSS)、
        open_times(炸板次数)、continuous_days(连板数)、industry(行业)
    """
    try:
        return _to_json(zt_pool.get_zt_pool_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_strong_stocks(date: str) -> str:
    """
    获取强势股池（60日新高/量比放大的龙头股）。

    数据源: 仅 akshare
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_change(涨跌幅%)、price、
        limit_price(涨停价)、amount(成交额元)、float_mv/total_mv(流通/总市值元)、
        turnover(换手率%)、volume_ratio(量比)、is_new_high(是否创新高)、
        reason(入选理由)、industry(行业)
    """
    try:
        return _to_json(strong_stocks.get_strong_stocks_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_previous_zt(date: str) -> str:
    """
    获取昨日涨停今日数据（低吸检测：昨日涨停股的今日表现）。

    数据源: 仅 akshare
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 今日交易日期 YYYYMMDD，接口自动返回昨日涨停股今日数据

    Returns:
        JSON 列表，每条包含：symbol、name、pct_change(今日涨跌幅%)、price(今日最新价)、
        limit_price(昨日涨停价)、amount(今日成交额元)、float_mv/total_mv、turnover、
        prev_seal_time(昨日封板时间HHMMSS)、prev_continuous_days(昨日连板数)、industry
    """
    try:
        return _to_json(previous_zt.get_previous_zt_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_zbgc_pool(date: str) -> str:
    """
    获取炸板股池（今日冲板后开板，补充低吸候选）。

    数据源: 仅 akshare
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260320"

    Returns:
        JSON 列表，每条包含：symbol、name、pct_change(涨跌幅%)、price、
        limit_price(涨停价)、amount(成交额元)、float_mv/total_mv、turnover、
        first_seal_time(首次封板时间)、open_times(炸板次数)、amplitude(振幅%)、industry
    """
    try:
        return _to_json(zbgc_pool.get_zbgc_pool_history(date))
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
        JSON 列表，每条包含：symbol、name、date、close_price、pct_change、
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


@mcp.tool()
async def tool_get_market_north_capital() -> str:
    """
    获取北向资金日频资金流（沪股通+深股通）。

    数据源: 仅 akshare（tushare 无等效接口）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        无参数

    Returns:
        JSON 列表，每条包含 date(YYYYMMDD)、market(沪股通/深股通)、
        direction(北向/南向)、net_buy(成交净买额元)、net_inflow(资金净流入元)、
        balance(当日资金余额元)、up_count、flat_count、down_count
    """
    try:
        return _to_json(north_flow.get_north_flow_history())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_sector_capital_flow(
    indicator: str = "今日",
    sector_type: str = "行业资金流",
) -> str:
    """
    获取行业/概念/地域板块资金流排名（主/超大单/大单/中单/小单净流入）。

    数据源: 仅 akshare（tushare 无等效接口）
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 不支持

    Args:
        indicator: choice of {"今日", "3日", "5日", "10日"}
        sector_type: choice of {"行业资金流", "概念资金流", "地域资金流", "沪股通", "深股通"}

    Returns:
        JSON 列表，每条包含：rank、name、pct_change(涨跌幅%)、
        main_net_inflow/main_net_inflow_pct(主力净流入元/%)、
        super_large_net_inflow/super_large_net_inflow_pct(超大单%)、
        large_net_inflow/large_net_inflow_pct(大单%)、
        medium_net_inflow/medium_net_inflow_pct(中单%)、
        small_net_inflow/small_net_inflow_pct(小单%)、
        top_stock(资金流入最多股票)
    """
    try:
        return _to_json(sector_capital_flow.get_sector_capital_flow_history(
            indicator=indicator, sector_type=sector_type
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
