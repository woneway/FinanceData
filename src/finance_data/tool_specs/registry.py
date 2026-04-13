"""Unified ToolSpec registry."""
from __future__ import annotations

from collections import OrderedDict
from typing import Any

from finance_data.tool_specs.models import (
    ProbeSpec,
    ProviderSpec,
    ServiceTargetSpec,
    ToolParamChoice,
    ToolMetadataSpec,
    ToolParamSpec,
    ToolSpec,
)


def _param(
    name: str,
    *,
    required: bool,
    default: Any = None,
    description: str = "",
    example: Any = None,
    aliases: tuple[str, ...] = (),
    choices: tuple[tuple[Any, str], ...] = (),
) -> ToolParamSpec:
    return ToolParamSpec(
        name=name,
        required=required,
        default=default,
        description=description,
        example=example,
        aliases=aliases,
        choices=tuple(ToolParamChoice(value=value, label=label) for value, label in choices),
    )


def _provider(
    name: str,
    class_path: str,
    method_name: str,
    *,
    available_if: str = "",
    notes: str = "",
) -> ProviderSpec:
    return ProviderSpec(
        name=name,
        class_path=class_path,
        method_name=method_name,
        available_if=available_if,
        notes=notes,
    )


def _service(module_path: str, object_name: str, method_name: str) -> ServiceTargetSpec:
    return ServiceTargetSpec(
        module_path=module_path,
        object_name=object_name,
        method_name=method_name,
    )


def _probe(
    default_params: dict[str, Any],
    *,
    timeout_sec: int = 30,
    min_records: int = 0,
    required_fields: tuple[str, ...] = (),
    consistency_enabled: bool = True,
) -> ProbeSpec:
    return ProbeSpec(
        default_params=default_params,
        timeout_sec=timeout_sec,
        min_records=min_records,
        required_fields=required_fields,
        consistency_enabled=consistency_enabled,
    )


def _meta(
    *,
    entity: str,
    scope: str,
    data_freshness: str,
    update_timing: str,
    supports_history: bool,
    history_start: str | None = None,
    cache_ttl: int = 0,
    source: str = "both",
    source_priority: str = "akshare",
    api_name: str = "",
    limitations: tuple[str, ...] = (),
    primary_key: str = "date",
    examples: tuple[dict[str, Any], ...] = (),
) -> ToolMetadataSpec:
    return ToolMetadataSpec(
        entity=entity,
        scope=scope,
        data_freshness=data_freshness,
        update_timing=update_timing,
        supports_history=supports_history,
        history_start=history_start,
        cache_ttl=cache_ttl,
        source=source,
        source_priority=source_priority,
        api_name=api_name,
        limitations=limitations,
        primary_key=primary_key,
        examples=examples,
    )


TOOL_SPEC_REGISTRY: "OrderedDict[str, ToolSpec]" = OrderedDict(
    (
        spec.name,
        spec,
    )
    for spec in [
        ToolSpec(
            name="tool_get_stock_info_history",
            description="获取个股基本信息",
            domain="stock",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("symbol", "name", "industry", "list_date"),
            service=_service("finance_data.service.stock", "stock_history", "get_stock_info_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.stock.history:TushareStockHistory", "get_stock_info_history", available_if="tushare_token"),
                _provider("xueqiu", "finance_data.provider.xueqiu.stock.history:XueqiuStockHistory", "get_stock_info_history"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock_info", scope="history", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="both", source_priority="tushare", api_name="stock_basic,stock_company", limitations=(), primary_key="symbol", examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_daily_kline_history",
            description="获取个股历史日线行情",
            domain="kline",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
                _param("start", required=False, default="20240101", description="开始日期 YYYYMMDD", example="20240301"),
                _param("end", required=False, default="", description="结束日期 YYYYMMDD", example="20240401"),
                _param("adj", required=False, default="qfq", description="复权类型", example="qfq"),
            ),
            return_fields=("date", "open", "high", "low", "close", "volume", "amount", "pct_chg"),
            service=_service("finance_data.service.kline", "daily_kline_history", "get_daily_kline_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.kline.history:TushareKlineHistory", "get_daily_kline_history", available_if="tushare_token"),
                _provider("akshare", "finance_data.provider.akshare.kline.history:AkshareKlineHistory", "get_daily_kline_history"),
            ),
            probe=_probe({"symbol": "000001", "start": "$RECENT-30", "end": "$RECENT", "adj": "qfq"}, required_fields=("date", "close")),
            metadata=_meta(entity="stock", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="19900101", source="both", source_priority="tushare", api_name="daily", examples=({"symbol": "000001", "start": "20240101"},)),
        ),
        ToolSpec(
            name="tool_get_weekly_kline_history",
            description="获取个股历史周线行情（每日更新）",
            domain="kline",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
                _param("start", required=False, default="20240101", description="开始日期 YYYYMMDD", example="20240301"),
                _param("end", required=False, default="", description="结束日期 YYYYMMDD", example="20240401"),
                _param("adj", required=False, default="qfq", description="复权类型", example="qfq"),
            ),
            return_fields=("date", "open", "high", "low", "close", "volume", "amount", "pct_chg"),
            service=_service("finance_data.service.kline", "weekly_kline_history", "get_weekly_kline_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.kline.history:TushareKlineHistory", "get_weekly_kline_history", available_if="tushare_token"),
            ),
            probe=_probe({"symbol": "000001", "start": "$RECENT-90", "end": "$RECENT", "adj": "qfq"}, required_fields=("date", "close")),
            metadata=_meta(entity="stock", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="19900101", source="multi", source_priority="tushare", api_name="weekly", examples=({"symbol": "000001", "start": "20240101"},)),
        ),
        ToolSpec(
            name="tool_get_monthly_kline_history",
            description="获取个股历史月线行情（每日更新）",
            domain="kline",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
                _param("start", required=False, default="20240101", description="开始日期 YYYYMMDD", example="20240301"),
                _param("end", required=False, default="", description="结束日期 YYYYMMDD", example="20240401"),
                _param("adj", required=False, default="qfq", description="复权类型", example="qfq"),
            ),
            return_fields=("date", "open", "high", "low", "close", "volume", "amount", "pct_chg"),
            service=_service("finance_data.service.kline", "monthly_kline_history", "get_monthly_kline_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.kline.history:TushareKlineHistory", "get_monthly_kline_history", available_if="tushare_token"),
            ),
            probe=_probe({"symbol": "000001", "start": "$RECENT-365", "end": "$RECENT", "adj": "qfq"}, required_fields=("date", "close")),
            metadata=_meta(entity="stock", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="19900101", source="multi", source_priority="tushare", api_name="monthly", examples=({"symbol": "000001", "start": "20240101"},)),
        ),
        ToolSpec(
            name="tool_get_realtime_quote",
            description="获取股票实时行情",
            domain="realtime",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("symbol", "name", "price", "pct_chg", "volume", "amount", "market_cap", "pe", "pb", "turnover_rate", "timestamp"),
            service=_service("finance_data.service.realtime", "realtime_quote", "get_realtime_quote"),
            providers=(
                _provider("xueqiu", "finance_data.provider.xueqiu.realtime.realtime:XueqiuRealtimeQuote", "get_realtime_quote"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("symbol", "price")),
            metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, cache_ttl=20, source="multi", source_priority="xueqiu", api_name="quotec.json", primary_key="symbol", examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_index_quote_realtime",
            description="获取大盘指数实时行情",
            domain="index",
            params=(
                _param("symbol", required=False, default="000001.SH", description="指数代码", example="000001.SH"),
            ),
            return_fields=("symbol", "name", "price", "pct_chg", "volume", "amount", "timestamp"),
            service=_service("finance_data.service.index", "index_quote", "get_index_quote_realtime"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.index.realtime:AkshareIndexQuote", "get_index_quote_realtime"),
                _provider("xueqiu", "finance_data.provider.xueqiu.index.realtime:XueqiuIndexQuote", "get_index_quote_realtime"),
            ),
            probe=_probe({"symbol": "000001.SH"}, required_fields=("symbol", "price")),
            metadata=_meta(entity="index", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, cache_ttl=20, source="both", source_priority="akshare", api_name="stock_zh_index_spot_sina", primary_key="symbol", examples=({"symbol": "000001.SH"},)),
        ),
        ToolSpec(
            name="tool_get_index_history",
            description="获取大盘指数历史K线",
            domain="index",
            params=(
                _param("symbol", required=False, default="000001.SH", description="指数代码", example="000001.SH"),
                _param("start", required=False, default="20240101", description="开始日期 YYYYMMDD", example="20240301"),
                _param("end", required=False, default="", description="结束日期 YYYYMMDD", example="20240401"),
            ),
            return_fields=("symbol", "date", "open", "high", "low", "close", "volume", "amount", "pct_chg"),
            service=_service("finance_data.service.index", "index_history", "get_index_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.index.history:TushareIndexHistory", "get_index_history", available_if="tushare_token"),
                _provider("xueqiu", "finance_data.provider.xueqiu.index.history:XueqiuIndexHistory", "get_index_history", available_if="xueqiu_cookie"),
            ),
            probe=_probe({"symbol": "000001.SH", "start": "$RECENT-30", "end": "$RECENT"}, required_fields=("date", "close")),
            metadata=_meta(entity="index", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="19900101", source="both", source_priority="tushare", api_name="index_daily", examples=({"symbol": "000001.SH", "start": "20240101"},)),
        ),
        ToolSpec(
            name="tool_get_board_index",
            description="获取东财板块索引/快照",
            domain="board",
            params=(
                _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
                _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD（单日快照）", example="20260410"),
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
            ),
            return_fields=("board_code", "board_name", "idx_type", "trade_date", "pct_chg", "leading_stock"),
            service=_service("finance_data.service.board", "board_index", "get_board_index"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.board.index:TushareBoardIndex", "get_board_index", available_if="tushare_token"),
            ),
            probe=_probe({"idx_type": "行业板块"}, required_fields=("board_code", "board_name")),
            metadata=_meta(entity="board", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index", primary_key="board_code"),
        ),
        ToolSpec(
            name="tool_get_chip_distribution_history",
            description="获取个股筹码分布",
            domain="chip",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("date", "cost_profit_ratio", "avg_cost", "concentration"),
            service=_service("finance_data.service.chip", "chip_history", "get_chip_distribution_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.chip.history:AkshareChipHistory", "get_chip_distribution_history"),
                _provider("tushare", "finance_data.provider.tushare.chip.history:TushareChipHistory", "get_chip_distribution_history", available_if="tushare_token"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("date",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="both", source_priority="akshare", api_name="stock_gpzy_plate_em", limitations=("筹码数据基于历史交易计算",), examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_financial_summary_history",
            description="获取个股财务摘要",
            domain="fundamental",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("period", "revenue", "net_profit", "roe", "gross_margin"),
            service=_service("finance_data.service.fundamental", "financial_summary", "get_financial_summary_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.fundamental.history:AkshareFinancialSummary", "get_financial_summary_history"),
                _provider("tushare", "finance_data.provider.tushare.fundamental.history:TushareFinancialSummary", "get_financial_summary_history", available_if="tushare_token"),
                _provider("xueqiu", "finance_data.provider.xueqiu.fundamental.history:XueqiuFinancialSummary", "get_financial_summary_history", available_if="xueqiu_cookie"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("period",)),
            metadata=_meta(entity="stock", scope="quarterly", data_freshness="quarterly", update_timing="quarterly", supports_history=True, history_start="19900101", source="both", source_priority="akshare", api_name="stock_financial_analysis_indicator", limitations=("财报季披露，延迟较大",), primary_key="period", examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_dividend_history",
            description="获取个股历史分红记录",
            domain="fundamental",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("ex_date", "per_share", "record_date"),
            service=_service("finance_data.service.fundamental", "dividend", "get_dividend_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.fundamental.history:AkshareDividend", "get_dividend_history"),
                _provider("tushare", "finance_data.provider.tushare.fundamental.history:TushareDividend", "get_dividend_history", available_if="tushare_token"),
                _provider("xueqiu", "finance_data.provider.xueqiu.fundamental.history:XueqiuDividend", "get_dividend_history", available_if="xueqiu_cookie"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("ex_date",)),
            metadata=_meta(entity="stock", scope="historical", data_freshness="historical", update_timing="quarterly", supports_history=True, source="both", source_priority="akshare", api_name="stock分红", primary_key="ex_date", examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_stock_capital_flow_realtime",
            description="获取个股资金流向",
            domain="cashflow",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("date", "net_inflow", "main_net_inflow", "super_large_net_inflow"),
            service=_service("finance_data.service.cashflow", "stock_capital_flow", "get_stock_capital_flow_realtime"),
            providers=(
                _provider("xueqiu", "finance_data.provider.xueqiu.cashflow.realtime:XueqiuStockCapitalFlow", "get_stock_capital_flow_realtime", available_if="xueqiu_cookie"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("date",)),
            metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_individual_fund_flow", limitations=("tushare 无个股资金流向接口", "盘中实时更新，收盘后数据更准确"), examples=({"symbol": "000001"},)),
        ),
        ToolSpec(
            name="tool_get_trade_calendar_history",
            description="获取交易日历",
            domain="calendar",
            params=(
                _param("start", required=True, description="开始日期 YYYYMMDD", example="20240301"),
                _param("end", required=True, description="结束日期 YYYYMMDD", example="20240401"),
            ),
            return_fields=("cal_date", "is_open", "pretrade_date"),
            service=_service("finance_data.service.calendar", "trade_calendar", "get_trade_calendar_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.calendar.history:TushareTradeCalendar", "get_trade_calendar_history", available_if="tushare_token"),
                _provider("akshare", "finance_data.provider.akshare.calendar.history:AkshareTradeCalendar", "get_trade_calendar_history"),
                _provider("baostock", "finance_data.provider.baostock.calendar.history:BaostockTradeCalendar", "get_trade_calendar_history"),
            ),
            probe=_probe({"start": "$RECENT-30", "end": "$RECENT"}, required_fields=("cal_date",)),
            metadata=_meta(entity="market", scope="historical", data_freshness="historical", update_timing="T+1_17:00", supports_history=True, history_start="19900101", source="both", source_priority="tushare", api_name="trade_cal", primary_key="cal_date", examples=({"start": "20240101", "end": "20240401"},)),
        ),
        ToolSpec(
            name="tool_get_lhb_detail",
            description="获取龙虎榜每日上榜详情",
            domain="lhb",
            params=(
                _param("start_date", required=True, description="开始日期 YYYYMMDD", example="20240401"),
                _param("end_date", required=True, description="结束日期 YYYYMMDD", example="20240409"),
            ),
            return_fields=("date", "symbol", "name", "close", "pct_chg", "reason"),
            service=_service("finance_data.service.lhb", "lhb_detail", "get_lhb_detail_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.history:AkshareLhbDetail", "get_lhb_detail_history"),
                _provider("tushare", "finance_data.provider.tushare.lhb.history:TushareLhbDetail", "get_lhb_detail_history", available_if="tushare_token"),
            ),
            probe=_probe({"start_date": "$RECENT-7", "end_date": "$RECENT"}, required_fields=("date", "symbol")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="both", source_priority="akshare", api_name="stock_lhb_detail_em", primary_key="date", examples=({"start_date": "20240401", "end_date": "20240409"},)),
        ),
        ToolSpec(
            name="tool_get_lhb_stock_stat",
            description="获取个股龙虎榜上榜统计",
            domain="lhb",
            params=(
                _param("period", required=False, default="近一月", description="统计周期", example="近一月"),
            ),
            return_fields=("symbol", "name", "times", "lhb_net_buy", "lhb_buy", "lhb_sell"),
            service=_service("finance_data.service.lhb", "lhb_stock_stat", "get_lhb_stock_stat_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.history:AkshareLhbStockStat", "get_lhb_stock_stat_history"),
            ),
            probe=_probe({"period": "近一月"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_lhb_ggtj_sina", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_lhb_active_traders",
            description="获取活跃游资营业部统计",
            domain="lhb",
            params=(
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20240401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20240409"),
            ),
            return_fields=("branch_name", "buy_count", "buy_amount", "sell_amount", "stocks"),
            service=_service("finance_data.service.lhb", "lhb_active_traders", "get_lhb_active_traders_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.history:AkshareLhbActiveTraders", "get_lhb_active_traders_history"),
            ),
            probe=_probe({"start_date": "$RECENT-7", "end_date": "$RECENT"}, required_fields=("branch_name",)),
            metadata=_meta(entity="lhb", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_lhb_yytj_sina", primary_key="branch_name"),
        ),
        ToolSpec(
            name="tool_get_lhb_trader_stat",
            description="获取营业部龙虎榜战绩排行",
            domain="lhb",
            params=(
                _param("period", required=False, default="近一月", description="统计周期", example="近一月"),
            ),
            return_fields=("branch_name", "times", "lhb_amount", "buy_amount", "sell_amount"),
            service=_service("finance_data.service.lhb", "lhb_trader_stat", "get_lhb_trader_stat_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.history:AkshareLhbTraderStat", "get_lhb_trader_stat_history"),
            ),
            probe=_probe({"period": "近一月"}, required_fields=("branch_name",)),
            metadata=_meta(entity="lhb", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_lhb_yytj_sina", primary_key="branch_name"),
        ),
        ToolSpec(
            name="tool_get_lhb_stock_detail",
            description="获取个股龙虎榜席位明细",
            domain="lhb",
            params=(
                _param("symbol", required=False, default="", description="股票代码", example="000001"),
                _param("date", required=False, default="", description="交易日期 YYYYMMDD", example="20240408"),
                _param("flag", required=False, default="买入", description="买入/卖出", example="买入"),
            ),
            return_fields=("symbol", "date", "trade_amount", "seat_type"),
            service=_service("finance_data.service.lhb", "lhb_stock_detail", "get_lhb_stock_detail_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.history:AkshareLhbStockDetail", "get_lhb_stock_detail_history"),
            ),
            probe=_probe({"symbol": "", "date": "$RECENT", "flag": "买入"}, required_fields=("symbol", "date")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_lhb_detail_daily_sina", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_zt_pool",
            description="获取涨停股池",
            domain="pool",
            params=(
                _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "pct_chg", "continuous_days", "seal_amount"),
            service=_service("finance_data.service.pool", "zt_pool", "get_zt_pool_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.pool.history:AkshareZtPool", "get_zt_pool_history"),
            ),
            probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_zt_pool_em", limitations=("tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_strong_stocks",
            description="获取强势股池",
            domain="pool",
            params=(
                _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "pct_chg", "is_new_high", "volume_ratio"),
            service=_service("finance_data.service.pool", "strong_stocks", "get_strong_stocks_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.pool.history:AkshareStrongStocks", "get_strong_stocks_history"),
            ),
            probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_strong_list_em", limitations=("tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_previous_zt",
            description="获取昨日涨停今日数据",
            domain="pool",
            params=(
                _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "pct_chg", "prev_seal_time", "prev_continuous_days"),
            service=_service("finance_data.service.pool", "previous_zt", "get_previous_zt_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.pool.history:AksharePreviousZt", "get_previous_zt_history"),
            ),
            probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_zt_pool_previous_em", limitations=("tushare 不支持此接口", "非实时；无历史查询"), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_zbgc_pool",
            description="获取炸板股池",
            domain="pool",
            params=(
                _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "pct_chg", "open_times", "amplitude"),
            service=_service("finance_data.service.pool", "zbgc_pool", "get_zbgc_pool_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.pool.history:AkshareZbgcPool", "get_zbgc_pool_history"),
            ),
            probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_zbgc_em", limitations=("tushare 不支持此接口", "非实时，收盘后约15:30更新；无历史查询"), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_north_stock_hold",
            description="获取北向资金持股明细",
            domain="north_flow",
            params=(
                _param("market", required=False, default="沪股通", description="市场", example="沪股通"),
                _param("indicator", required=False, default="5日排行", description="榜单指标", example="5日排行"),
                _param("symbol", required=False, default="", description="股票代码", example="600519"),
                _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "date", "hold_volume", "hold_market_cap"),
            service=_service("finance_data.service.north_flow", "north_stock_hold", "get_north_stock_hold_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.north_flow.history:AkshareNorthStockHold", "get_north_stock_hold_history"),
                _provider("tushare", "finance_data.provider.tushare.north_flow.history:TushareNorthStockHold", "get_north_stock_hold_history", available_if="tushare_token"),
            ),
            probe=_probe({"market": "沪股通", "indicator": "5日排行", "symbol": "", "trade_date": ""}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=True, source="both", source_priority="akshare", api_name="stock_hsgt_hold_stock_em", limitations=("tushare hk_hold 自2024年8月20日起改为季度披露", "tushare close_price/pct_change/hold_market_cap/hold_total_ratio 为 0"), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_margin",
            description="获取融资融券汇总数据",
            domain="margin",
            params=(
                _param("trade_date", required=False, default="", description="单日 YYYYMMDD", example="20240408"),
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20240401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20240408"),
                _param("exchange_id", required=False, default="", description="交易所代码", example="SSE"),
            ),
            return_fields=("date", "exchange", "rzye", "rzmre", "rqye", "rzrqye"),
            service=_service("finance_data.service.margin", "margin", "get_margin_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.margin.history:TushareMargin", "get_margin_history", available_if="tushare_token"),
                _provider("akshare", "finance_data.provider.akshare.margin.history:AkshareMargin", "get_margin_history"),
            ),
            probe=_probe({"trade_date": "$RECENT", "start_date": "", "end_date": "", "exchange_id": ""}, required_fields=("date",)),
            metadata=_meta(entity="market", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20100101", source="both", source_priority="tushare", api_name="margin", limitations=("akshare SSE rzche 始终为 0（数据源不提供融资偿还额）",), primary_key="date"),
        ),
        ToolSpec(
            name="tool_get_margin_detail",
            description="获取融资融券个股明细",
            domain="margin",
            params=(
                _param("trade_date", required=False, default="", description="单日 YYYYMMDD", example="20240408"),
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20240401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20240408"),
                _param("ts_code", required=False, default="", description="股票代码", example="000001"),
            ),
            return_fields=("date", "symbol", "name", "rzye", "rqye", "rzmre", "rqyl"),
            service=_service("finance_data.service.margin", "margin_detail", "get_margin_detail_history"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.margin.history:TushareMarginDetail", "get_margin_detail_history", available_if="tushare_token"),
                _provider("akshare", "finance_data.provider.akshare.margin.history:AkshareMarginDetail", "get_margin_detail_history"),
                _provider("xueqiu", "finance_data.provider.xueqiu.margin.history:XueqiuMarginDetail", "get_margin_detail_history", available_if="xueqiu_cookie"),
            ),
            probe=_probe({"trade_date": "", "start_date": "$RECENT-7", "end_date": "$RECENT", "ts_code": "000001"}, required_fields=("date", "symbol")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20100101", source="both", source_priority="tushare", api_name="margin_detail", limitations=("akshare 仅 SSE，rqye/rqyl/rqchl/rzrqye 为 0（不含融券数据）",), primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_market_stats_realtime",
            description="获取当日市场涨跌家数统计（盘中实时）",
            domain="market",
            params=(),
            return_fields=("date", "up_count", "down_count", "flat_count", "total_count", "total_amount"),
            service=_service("finance_data.service.market", "market_realtime", "get_market_stats_realtime"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.market.realtime:AkshareMarketRealtime", "get_market_stats_realtime"),
            ),
            probe=_probe({}, required_fields=("date",)),
            metadata=_meta(entity="market_stats", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_market_activity_legu", limitations=("tushare 无等效接口",), primary_key="date"),
        ),
        ToolSpec(
            name="tool_get_market_north_capital",
            description="获取北向资金日频资金流（沪股通+深股通）",
            domain="north_flow",
            params=(),
            return_fields=("date", "market", "direction", "net_buy", "net_inflow", "balance"),
            service=_service("finance_data.service.north_flow", "north_flow", "get_north_flow_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.north_flow.history:AkshareNorthFlow", "get_north_flow_history"),
            ),
            probe=_probe({}, required_fields=("date",)),
            metadata=_meta(entity="market", scope="daily", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_hsgt_fund_flow_summary_em", limitations=("tushare 无等效接口",), primary_key="date"),
        ),
        ToolSpec(
            name="tool_get_suspend",
            description="获取停牌股票信息",
            domain="suspend",
            params=(
                _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
            ),
            return_fields=("symbol", "name", "suspend_date", "resume_date", "reason"),
            service=_service("finance_data.service.suspend", "suspend", "get_suspend_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.suspend.history:AkshareSuspend", "get_suspend_history"),
            ),
            probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_tfp_em", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_board_member",
            description="获取东财板块成分股列表",
            domain="board",
            params=(
                _param("board_name", required=True, description="板块名称", example="银行"),
                _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
                _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD（单日成分）", example="20260410"),
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
            ),
            return_fields=("board_code", "board_name", "idx_type", "trade_date", "symbol", "name"),
            service=_service("finance_data.service.board", "board_member", "get_board_member"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.board.member:TushareBoardMember", "get_board_member", available_if="tushare_token"),
            ),
            probe=_probe({"board_name": "银行", "idx_type": "行业板块"}, required_fields=("symbol", "name")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index,dc_member", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_board_daily",
            description="获取东财板块日行情",
            domain="board",
            params=(
                _param("board_name", required=True, description="板块名称", example="银行"),
                _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
                _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
                _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
                _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
            ),
            return_fields=("board_code", "board_name", "idx_type", "trade_date", "open", "close", "pct_chg"),
            service=_service("finance_data.service.board", "board_daily", "get_board_daily"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.board.daily:TushareBoardDaily", "get_board_daily", available_if="tushare_token"),
            ),
            probe=_probe({"board_name": "银行", "idx_type": "行业板块", "start_date": "$RECENT-30", "end_date": "$RECENT"}, required_fields=("trade_date", "close")),
            metadata=_meta(entity="board", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index,dc_daily", primary_key="trade_date"),
        ),
        ToolSpec(
            name="tool_get_hot_rank",
            description="获取热股排行（东财人气榜）",
            domain="hot_rank",
            params=(),
            return_fields=("rank", "symbol", "name", "current", "pct_chg"),
            service=_service("finance_data.service.hot_rank", "hot_rank", "get_hot_rank_realtime"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.hot_rank.realtime:AkshareHotRank", "get_hot_rank_realtime"),
            ),
            probe=_probe({}, required_fields=("rank", "symbol")),
            metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_hot_rank_em", primary_key="rank"),
        ),
        ToolSpec(
            name="tool_get_ths_hot",
            description="获取同花顺热股排行",
            domain="hot_rank",
            params=(
                _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            ),
            return_fields=("rank", "symbol", "name", "pct_chg", "current_price", "hot", "concept"),
            service=_service("finance_data.service.hot_rank", "ths_hot", "get_ths_hot"),
            providers=(
                _provider("tushare", "finance_data.provider.tushare.hot_rank.ths_hot:TushareThsHot", "get_ths_hot", available_if="tushare_token"),
            ),
            probe=_probe({}, required_fields=("rank", "symbol")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="ths_hot", primary_key="rank"),
        ),
        ToolSpec(
            name="tool_get_lhb_inst_detail",
            description="获取龙虎榜机构买卖每日统计",
            domain="lhb",
            params=(
                _param("start_date", required=True, description="开始日期 YYYYMMDD", example="20240401"),
                _param("end_date", required=True, description="结束日期 YYYYMMDD", example="20240409"),
            ),
            return_fields=("symbol", "name", "date", "inst_buy", "inst_sell", "inst_net"),
            service=_service("finance_data.service.lhb", "lhb_inst_detail", "get_lhb_inst_detail_history"),
            providers=(
                _provider("akshare", "finance_data.provider.akshare.lhb.inst_detail:AkshareLhbInstDetail", "get_lhb_inst_detail_history"),
            ),
            probe=_probe({"start_date": "$RECENT-7", "end_date": "$RECENT"}, required_fields=("symbol", "date")),
            metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="akshare", source_priority="akshare", api_name="stock_lhb_jgmmtj_em", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_daily_basic",
            description="获取个股日频基本面指标（PE/PB/市值/换手率/量比）",
            domain="daily_basic",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("symbol", "name", "date", "pe", "pb", "market_cap", "turnover_rate", "volume_ratio"),
            service=_service("finance_data.service.daily_basic", "daily_basic", "get_daily_basic"),
            providers=(
                _provider("tencent", "finance_data.provider.tencent.daily_basic:TencentDailyBasic", "get_daily_basic"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("symbol", "date")),
            metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="tencent", source_priority="tencent", api_name="qt.gtimg.cn", primary_key="symbol"),
        ),
        ToolSpec(
            name="tool_get_limit_price",
            description="获取个股涨跌停价格",
            domain="limit_price",
            params=(
                _param("symbol", required=True, description="股票代码", example="000001"),
            ),
            return_fields=("symbol", "name", "date", "limit_up", "limit_down", "prev_close", "current"),
            service=_service("finance_data.service.limit_price", "limit_price", "get_limit_price"),
            providers=(
                _provider("tencent", "finance_data.provider.tencent.limit_price:TencentLimitPrice", "get_limit_price"),
            ),
            probe=_probe({"symbol": "000001"}, required_fields=("symbol", "limit_up", "limit_down")),
            metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="tencent", source_priority="tencent", api_name="qt.gtimg.cn", primary_key="symbol"),
        ),
    ]
)
