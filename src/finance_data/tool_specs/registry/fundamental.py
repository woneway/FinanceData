"""ToolSpec 注册：fundamental domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_chip_distribution_history",
        description="获取个股筹码分布",
        domain="fundamental",
        params=(
            _param("symbol", required=True, description="股票代码", example="000001"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260101"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "date", "avg_cost", "concentration", "cost_profit_ratio", "cost_90", "cost_10"),
        service=_service("finance_data.service.chip", "chip_history", "get_chip_distribution_history"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.chip.history:TushareChipHistory", "get_chip_distribution_history", available_if="tushare_token"),
        ),
        probe=_probe({"symbol": "000001"}, required_fields=("date",)),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, source="tushare", source_priority="tushare", api_name="cyq_perf", limitations=("筹码数据基于历史交易计算", "concentration 字段不可用"),  examples=({"symbol": "000001"},)),
        display_name="筹码分布",
    ),
    ToolSpec(
        name="tool_get_financial_summary_history",
        description="获取个股财务摘要",
        domain="fundamental",
        params=(
            _param("symbol", required=True, description="股票代码", example="000001"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD（报告期）", example="20240101"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD（报告期）", example="20251231"),
        ),
        return_fields=("symbol", "period", "revenue", "net_profit", "roe"),
        service=_service("finance_data.service.fundamental", "financial_summary", "get_financial_summary_history"),
        providers=(
            _provider("akshare", "finance_data.provider.akshare.fundamental.history:AkshareFinancialSummary", "get_financial_summary_history"),
            _provider("tushare", "finance_data.provider.tushare.fundamental.history:TushareFinancialSummary", "get_financial_summary_history", available_if="tushare_token"),
            _provider("xueqiu", "finance_data.provider.xueqiu.fundamental.history:XueqiuFinancialSummary", "get_financial_summary_history", available_if="xueqiu_cookie"),
        ),
        probe=_probe({"symbol": "000001"}, required_fields=("period",)),
        metadata=_meta(entity="stock", scope="quarterly", data_freshness="quarterly", update_timing="quarterly", supports_history=True, history_start="19900101", source="multi", source_priority="akshare", api_name="stock_financial_abstract,income/fina_indicator,indicator.json", limitations=("财报季披露，延迟较大",), primary_key="period", examples=({"symbol": "000001"},)),
        display_name="财务摘要",
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
        metadata=_meta(entity="stock", scope="historical", data_freshness="historical", update_timing="quarterly", supports_history=True, source="multi", source_priority="akshare", api_name="stock_fhps_detail_ths,dividend,bonus.json", primary_key="ex_date", examples=({"symbol": "000001"},)),
        display_name="分红记录",
    ),
]
