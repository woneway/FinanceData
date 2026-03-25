"""接口元数据注册表"""
from typing import Dict, List, Optional
from finance_data.provider.metadata.models import (
    ToolMeta, DataFreshness, UpdateTiming, DataSource
)

TOOL_REGISTRY: Dict[str, ToolMeta] = {
    # === Stock ===
    "tool_get_stock_info_history": ToolMeta(
        name="tool_get_stock_info_history",
        description="获取个股基本信息",
        domain="stock",
        entity="stock_info",
        scope="history",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_16_00,
        supports_history=False,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_individual_basic_info_xq",
        limitations=["tushare 提供更完整的财务数据"],
        return_fields=["symbol", "name", "industry", "list_date"],
    ),

    # === Kline ===
    "tool_get_kline_history": ToolMeta(
        name="tool_get_kline_history",
        description="获取K线历史数据",
        domain="kline",
        entity="stock",
        scope="historical",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_16_00,
        supports_history=True,
        history_start="19900101",
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_zh_a_hist",
        return_fields=["date", "open", "high", "low", "close", "volume", "amount"],
    ),

    # === Realtime ===
    "tool_get_realtime_quote": ToolMeta(
        name="tool_get_realtime_quote",
        description="获取股票实时行情",
        domain="realtime",
        entity="stock",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        cache_ttl=20,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_zh_a_spot",
        return_fields=["symbol", "name", "price", "pct_chg", "volume", "amount"],
    ),

    # === Index ===
    "tool_get_index_quote_realtime": ToolMeta(
        name="tool_get_index_quote_realtime",
        description="获取大盘指数实时行情",
        domain="index",
        entity="index",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        cache_ttl=20,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_zh_index_spot_sina",
        return_fields=["symbol", "name", "price", "pct_chg", "volume"],
    ),

    "tool_get_index_history": ToolMeta(
        name="tool_get_index_history",
        description="获取大盘指数历史K线",
        domain="index",
        entity="index",
        scope="historical",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_16_00,
        supports_history=True,
        history_start="19900101",
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_zh_index_daily_tx",
        return_fields=["date", "open", "high", "low", "close", "volume"],
    ),

    # === Sector ===
    "tool_get_sector_rank_realtime": ToolMeta(
        name="tool_get_sector_rank_realtime",
        description="获取行业板块涨跌排名",
        domain="sector",
        entity="sector",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_board_industry_name_em",
        limitations=["tushare 无此接口"],
        return_fields=["rank", "name", "pct_chg", "volume", "amount"],
    ),

    # === Chip ===
    "tool_get_chip_distribution_history": ToolMeta(
        name="tool_get_chip_distribution_history",
        description="获取个股筹码分布",
        domain="chip",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_16_00,
        supports_history=False,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_gpzy_plate_em",
        limitations=["筹码数据基于历史交易计算"],
        return_fields=["date", "cost_profit_ratio", "avg_cost", "concentration"],
    ),

    # === Fundamental ===
    "tool_get_financial_summary_history": ToolMeta(
        name="tool_get_financial_summary_history",
        description="获取个股财务摘要",
        domain="fundamental",
        entity="stock",
        scope="quarterly",
        data_freshness=DataFreshness.QUARTERLY,
        update_timing=UpdateTiming.QUARTERLY_DISCLOSURE,
        supports_history=True,
        history_start="19900101",
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_financial_analysis_indicator",
        limitations=["财报季披露，延迟较大"],
        return_fields=["period", "revenue", "net_profit", "roe", "gross_margin"],
    ),

    "tool_get_dividend_history": ToolMeta(
        name="tool_get_dividend_history",
        description="获取个股历史分红记录",
        domain="fundamental",
        entity="stock",
        scope="historical",
        data_freshness=DataFreshness.HISTORICAL,
        update_timing=UpdateTiming.QUARTERLY_DISCLOSURE,
        supports_history=True,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock分红",
        return_fields=["ex_date", "per_share", "record_date"],
    ),

    "tool_get_earnings_forecast_history": ToolMeta(
        name="tool_get_earnings_forecast_history",
        description="获取个股业绩预告",
        domain="fundamental",
        entity="stock",
        scope="quarterly",
        data_freshness=DataFreshness.QUARTERLY,
        update_timing=UpdateTiming.QUARTERLY_DISCLOSURE,
        supports_history=True,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_yjyg_em",
        limitations=["tushare 业绩预告需较高权限"],
        return_fields=["period", "forecast_type", "net_profit_min", "net_profit_max", "change_low", "change_high", "summary"],
    ),

    # === Cashflow ===
    "tool_get_stock_capital_flow_realtime": ToolMeta(
        name="tool_get_stock_capital_flow_realtime",
        description="获取个股资金流向",
        domain="cashflow",
        entity="stock",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_individual_fund_flow",
        limitations=["tushare 无个股资金流向接口", "盘中实时更新，收盘后数据更准确"],
        return_fields=["date", "net_inflow", "main_net_inflow", "super_large_net_inflow"],
    ),

    # === Calendar ===
    "tool_get_trade_calendar_history": ToolMeta(
        name="tool_get_trade_calendar_history",
        description="获取交易日历",
        domain="calendar",
        entity="market",
        scope="historical",
        data_freshness=DataFreshness.HISTORICAL,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="19900101",
        source=DataSource.BOTH,
        source_priority="tushare",
        api_name="trade_cal",
        return_fields=["cal_date", "is_open", "pretrade_date"],
    ),

    # === Market ===
    # === LHB ===
    "tool_get_lhb_detail": ToolMeta(
        name="tool_get_lhb_detail",
        description="获取龙虎榜每日上榜详情",
        domain="lhb",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20200101",
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_lhb_detail_em",
        return_fields=["date", "symbol", "name", "close", "pct_chg", "reason"],
    ),

    "tool_get_lhb_stock_stat": ToolMeta(
        name="tool_get_lhb_stock_stat",
        description="获取个股上榜统计",
        domain="lhb",
        entity="stock",
        scope="monthly",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20200101",
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_lhb_stock_stat_em",
        limitations=["tushare 无个股上榜统计接口"],
        return_fields=["symbol", "name", "last_date", "times", "net_buy"],
    ),

    "tool_get_lhb_active_traders": ToolMeta(
        name="tool_get_lhb_active_traders",
        description="获取每日活跃游资营业部",
        domain="lhb",
        entity="broker",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20200101",
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_lhb_jgmm_em",
        limitations=["tushare 无每日活跃营业部接口"],
        return_fields=["branch_name", "date", "buy_count", "sell_count", "net_amount"],
    ),

    "tool_get_lhb_trader_stat": ToolMeta(
        name="tool_get_lhb_trader_stat",
        description="获取营业部统计（游资战绩排行）",
        domain="lhb",
        entity="broker",
        scope="monthly",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20200101",
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_lhb_trader_stat_em",
        limitations=["tushare 无营业部统计接口"],
        return_fields=["branch_name", "lhb_amount", "times", "buy_amount", "sell_amount"],
    ),

    "tool_get_lhb_stock_detail": ToolMeta(
        name="tool_get_lhb_stock_detail",
        description="获取个股某日龙虎榜席位明细",
        domain="lhb",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20200101",
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_lhb_detail_data_em",
        limitations=["tushare 无个股席位明细接口"],
        return_fields=["symbol", "date", "branch_name", "trade_amount", "seat_type"],
    ),

    # === Pool ===
    "tool_get_zt_pool": ToolMeta(
        name="tool_get_zt_pool",
        description="获取涨停股池",
        domain="pool",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_zt_pool_em",
        limitations=["tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"],
        return_fields=["symbol", "name", "pct_chg", "continuous_days", "seal_amount"],
    ),

    "tool_get_strong_stocks": ToolMeta(
        name="tool_get_strong_stocks",
        description="获取强势股池",
        domain="pool",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_strong_list_em",
        limitations=["tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"],
        return_fields=["symbol", "name", "pct_chg", "is_new_high", "volume_ratio"],
    ),

    "tool_get_previous_zt": ToolMeta(
        name="tool_get_previous_zt",
        description="获取昨日涨停今日数据",
        domain="pool",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_zt_pool_previous_em",
        limitations=["tushare 不支持此接口", "非实时；无历史查询"],
        return_fields=["symbol", "name", "pct_chg", "prev_seal_time", "prev_continuous_days"],
    ),

    "tool_get_zbgc_pool": ToolMeta(
        name="tool_get_zbgc_pool",
        description="获取炸板股池",
        domain="pool",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_zbgc_em",
        limitations=["tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"],
        return_fields=["symbol", "name", "pct_chg", "open_times", "amplitude"],
    ),

    # === North Flow ===
    "tool_get_north_stock_hold": ToolMeta(
        name="tool_get_north_stock_hold",
        description="获取北向资金持股明细",
        domain="north_flow",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=True,
        source=DataSource.BOTH,
        source_priority="akshare",
        api_name="stock_hsgt_hold_stock_em",
        limitations=["tushare hk_hold 自2024年8月20日起改为季度披露"],
        return_fields=["symbol", "name", "date", "hold_volume", "hold_market_cap"],
    ),

    # === Margin ===
    "tool_get_margin": ToolMeta(
        name="tool_get_margin",
        description="获取融资融券汇总数据",
        domain="margin",
        entity="market",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20100101",
        source=DataSource.BOTH,
        source_priority="tushare",
        api_name="margin",
        return_fields=["date", "exchange", "rzye", "rzmre", "rqye", "rzrqye"],
    ),

    "tool_get_margin_detail": ToolMeta(
        name="tool_get_margin_detail",
        description="获取融资融券个股明细",
        domain="margin",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_17_00,
        supports_history=True,
        history_start="20100101",
        source=DataSource.BOTH,
        source_priority="tushare",
        api_name="margin_detail",
        return_fields=["date", "symbol", "name", "rzye", "rqye", "rzmre", "rqyl"],
    ),

    # === Market ===
    "tool_get_market_stats_realtime": ToolMeta(
        name="tool_get_market_stats_realtime",
        description="获取当日市场涨跌家数统计（盘中实时）",
        domain="market",
        entity="market_stats",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_market_activity_legu",
        limitations=["tushare 无等效接口"],
        return_fields=["date", "up_count", "down_count", "flat_count", "total_count", "total_amount"],
    ),

    "tool_get_market_north_capital": ToolMeta(
        name="tool_get_market_north_capital",
        description="获取北向资金日频资金流（沪股通+深股通）",
        domain="north_flow",
        entity="market",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_hsgt_fund_flow_summary_em",
        limitations=["tushare 无等效接口"],
        return_fields=["date", "market", "direction", "net_buy", "net_inflow", "balance"],
    ),

    "tool_get_sector_capital_flow": ToolMeta(
        name="tool_get_sector_capital_flow",
        description="获取行业/概念/地域板块资金流排名",
        domain="sector_fund_flow",
        entity="sector",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_15_30,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_sector_fund_flow_rank",
        limitations=["非实时，收盘后约15:30更新；tushare 无等效接口"],
        return_fields=["rank", "name", "pct_chg", "main_net_inflow", "top_stock"],
    ),
}


def get_tool_meta(tool_name: str) -> Optional[ToolMeta]:
    """获取指定工具的元数据"""
    return TOOL_REGISTRY.get(tool_name)


def validate_all_tools() -> Dict[str, List[str]]:
    """
    校验所有工具的元数据完整性

    Returns:
        Dict[str, List[str]]: {tool_name: [error_messages]}
        空 dict 表示全部通过
    """
    errors = {}

    for name, meta in TOOL_REGISTRY.items():
        tool_errors = []

        if not meta.description:
            tool_errors.append("缺少 description")

        if not meta.api_name:
            tool_errors.append("缺少 api_name")

        if not meta.return_fields:
            tool_errors.append("缺少 return_fields")

        if not meta.domain:
            tool_errors.append("缺少 domain")

        if tool_errors:
            errors[name] = tool_errors

    return errors
