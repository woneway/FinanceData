"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import datetime
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
    try:
        return _to_json(stock_history.get_stock_info_history(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = daily_kline_history.get_daily_kline_history(symbol, start=start, end=end, adj=adj)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = weekly_kline_history.get_weekly_kline_history(symbol, start=start, end=end, adj=adj)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = monthly_kline_history.get_monthly_kline_history(symbol, start=start, end=end, adj=adj)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        result = realtime_quote.get_realtime_quote(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        result = index_quote.get_index_quote_realtime(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    if not end:
        end = datetime.date.today().strftime("%Y%m%d")
    try:
        result = index_history.get_index_history(symbol, start=start, end=end)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        result = board_index.get_board_index(
            idx_type=idx_type,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        result = chip_history.get_chip_distribution_history(
            symbol, start_date=start_date, end_date=end_date,
        )
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_financial_summary_history(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取个股财务摘要（营收、净利润、ROE、毛利率）。

    数据源: akshare 优先，tushare fallback
    实时性: 季度披露（T+1_17:00 后）
    历史查询: 支持（start_date/end_date 按报告期筛选）
    """
    try:
        result = financial_summary.get_financial_summary_history(
            symbol, start_date=start_date, end_date=end_date,
        )
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
    try:
        result = stock_capital_flow.get_stock_capital_flow_realtime(symbol)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        result = trade_calendar.get_trade_calendar_history(start, end)
        return _to_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_lhb_detail_history(
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
    try:
        return _to_json(lhb_stock_stat.get_lhb_stock_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(lhb_active_traders.get_lhb_active_traders_history(start_date, end_date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(lhb_trader_stat.get_lhb_trader_stat_history(period))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(lhb_stock_detail.get_lhb_stock_detail_history(symbol, date, flag))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_north_hold_history(
    market: str = "沪股通",
    indicator: str = "5日排行",
    symbol: str = "",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取北向资金持股明细，支持日期范围查询。

    数据源: akshare 优先，tushare fallback
    实时性: 非实时，收盘后约 15:30 更新
    历史查询: 支持（start_date/end_date，tushare 专用）

    Args:
        market: choice of {"沪股通", "深股通"}（akshare 专用）
        indicator: choice of {"5日排行", "10日排行", "月排行", "季排行", "年排行"}（akshare 专用）
        symbol: 股票代码（tushare 专用，如 "600000"）
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD（tushare 专用）
        end_date: 结束日期 YYYYMMDD（tushare 专用）

    Returns:
        JSON 列表，每条包含：symbol、name、date、close_price、pct_chg、
        hold_volume(持股数量股)、hold_market_cap(持股市值元)、hold_float_ratio(%),
        hold_total_ratio(%)、increase_5d_volume、increase_5d_cap 等（akshare 特有）

    Note:
        tushare hk_hold 自2024年8月20日起交易所停止发布日度数据，改为季度披露。
    """
    try:
        return _to_json(north_stock_hold.get_north_stock_hold_history(
            market=market, indicator=indicator, symbol=symbol,
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_margin_history(
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
    try:
        return _to_json(zt_pool.get_zt_pool_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(strong_stocks.get_strong_stocks_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(previous_zt.get_previous_zt_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(zbgc_pool.get_zbgc_pool_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(north_flow.get_north_flow_history())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_suspend_daily(date: str) -> str:
    """
    获取停牌股票信息。

    数据源: akshare(东财)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 不支持

    Args:
        date: 交易日期 YYYYMMDD，如 "20260408"

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、
        suspend_date(停牌起始日)、resume_date(复牌日期)、reason(停牌原因)
    """
    try:
        return _to_json(suspend.get_suspend_history(date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(
            board_member.get_board_member(
                board_name=board_name,
                idx_type=idx_type,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            )
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(
            board_daily.get_board_daily(
                board_name=board_name,
                idx_type=idx_type,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date,
            )
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(hot_rank.get_hot_rank_realtime())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(ths_hot.get_ths_hot(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(lhb_inst_detail.get_lhb_inst_detail_history(start_date, end_date))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)



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
    try:
        return _to_json(limit_list.get_limit_list(
            trade_date=trade_date, limit_type=limit_type,
            start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_hm_list_snapshot() -> str:
    """
    获取市场游资名录。

    数据源: tushare(hm_list)
    实时性: 不定期更新
    """
    try:
        return _to_json(hm_list.get_hm_list())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(hm_detail.get_hm_detail(
            trade_date=trade_date, start_date=start_date,
            end_date=end_date, hm_name=hm_name,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(auction.get_auction(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(kpl_list.get_kpl_list(
            trade_date=trade_date, tag=tag,
            start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(limit_step.get_limit_step(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
    try:
        return _to_json(auction_close.get_auction_close(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        ))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# tool_get_sector_capital_flow 已禁用（push2.eastmoney.com 域名不可达）
