"""ToolSpec 注册：lhb domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_lhb_detail_history",
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
        probe=_probe({"start_date": "$RECENT", "end_date": "$RECENT"}, required_fields=("date", "symbol")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="both", source_priority="akshare", api_name="stock_lhb_detail_em,top_list", primary_key="date,symbol,reason", examples=({"start_date": "20260401", "end_date": "20260401"},)),
        display_name="龙虎榜详情",
    ),
    ToolSpec(
        name="tool_get_lhb_stock_stat_history",
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
        display_name="个股统计",
    ),
    ToolSpec(
        name="tool_get_lhb_active_traders_history",
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
        display_name="活跃游资",
    ),
    ToolSpec(
        name="tool_get_lhb_trader_stat_history",
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
        display_name="营业部排行",
    ),
    ToolSpec(
        name="tool_get_lhb_stock_detail_daily",
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
        display_name="席位明细",
    ),
    ToolSpec(
        name="tool_get_lhb_inst_detail_history",
        description="获取龙虎榜机构买卖每日统计",
        domain="lhb",
        params=(
            _param("start_date", required=True, description="开始日期 YYYYMMDD", example="20240401"),
            _param("end_date", required=True, description="结束日期 YYYYMMDD", example="20240409"),
        ),
        return_fields=("symbol", "name", "date", "inst_buy_amount", "inst_sell_amount", "inst_net_buy"),
        service=_service("finance_data.service.lhb", "lhb_inst_detail", "get_lhb_inst_detail_history"),
        providers=(
            _provider("akshare", "finance_data.provider.akshare.lhb.inst_detail:AkshareLhbInstDetail", "get_lhb_inst_detail_history"),
        ),
        probe=_probe({"start_date": "$RECENT-7", "end_date": "$RECENT"}, required_fields=("symbol", "date")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="akshare", source_priority="akshare", api_name="stock_lhb_jgmmtj_em", primary_key="symbol"),
        display_name="机构明细",
    ),
    ToolSpec(
        name="tool_get_hm_list_snapshot",
        description="获取市场游资名录",
        domain="lhb",
        params=(),
        return_fields=("name", "desc", "orgs"),
        service=_service("finance_data.service.lhb", "hm_list", "get_hm_list"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.lhb.hm_list:TushareHmList", "get_hm_list", available_if="tushare_token"),
        ),
        probe=_probe({}, required_fields=("name",)),
        metadata=_meta(entity="hm", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="tushare", source_priority="tushare", api_name="hm_list", primary_key="name"),
        display_name="游资名录",
    ),
    ToolSpec(
        name="tool_get_hm_detail_history",
        description="获取游资每日交易明细",
        domain="lhb",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260408"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
            _param("hm_name", required=False, default="", description="游资名称", example=""),
        ),
        return_fields=("trade_date", "symbol", "name", "buy_amount", "sell_amount", "net_amount", "hm_name"),
        service=_service("finance_data.service.lhb", "hm_detail", "get_hm_detail"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.lhb.hm_detail:TushareHmDetail", "get_hm_detail", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "hm_name")),
        metadata=_meta(entity="hm", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="hm_detail", primary_key="symbol"),
        display_name="游资明细",
    ),
]
