"""ToolSpec 注册：pool domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_zt_pool_daily",
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
        display_name="涨停股池",
    ),
    ToolSpec(
        name="tool_get_strong_stocks_daily",
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
        display_name="强势股池",
    ),
    ToolSpec(
        name="tool_get_previous_zt_daily",
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
        display_name="昨日涨停",
    ),
    ToolSpec(
        name="tool_get_zbgc_pool_daily",
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
        display_name="炸板股池",
    ),
    ToolSpec(
        name="tool_get_limit_list_history",
        description="获取同花顺涨跌停榜单（支持日期范围）",
        domain="pool",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD（与 start_date/end_date 二选一）", example="20260410"),
            _param("limit_type", required=False, default="涨停池", description="榜单类型", example="涨停池", choices=(("涨停池", "涨停池"), ("连扳池", "连扳池"), ("炸板池", "炸板池"), ("跌停池", "跌停池"), ("冲刺涨停", "冲刺涨停"))),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "name", "pct_chg", "lu_desc", "tag", "status", "limit_amount", "first_lu_time", "last_lu_time", "turnover", "free_float", "market_type"),
        service=_service("finance_data.service.pool", "limit_list", "get_limit_list"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.pool.limit_list:TushareLimitList", "get_limit_list", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT", "limit_type": "涨停池"}, required_fields=("symbol", "name")),
        metadata=_meta(entity="stock", scope="history", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20231101", source="tushare", source_priority="tushare", api_name="limit_list_ths", primary_key="symbol"),
        display_name="涨跌停榜单",
    ),
    ToolSpec(
        name="tool_get_kpl_list_history",
        description="获取开盘啦榜单数据",
        domain="pool",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("tag", required=False, default="涨停", description="榜单类型", example="涨停", choices=(("涨停", "涨停"), ("跌停", "跌停"), ("炸板", "炸板"), ("自然涨停", "自然涨停"), ("竞价", "竞价"))),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "name", "pct_chg", "tag", "theme", "status", "lu_desc"),
        service=_service("finance_data.service.pool", "kpl_list", "get_kpl_list"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.pool.kpl_list:TushareKplList", "get_kpl_list", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT-2", "tag": "涨停"}, required_fields=("symbol", "name")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+0", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="kpl_list", primary_key="symbol"),
        display_name="开盘啦榜单",
    ),
    ToolSpec(
        name="tool_get_limit_step_history",
        description="获取涨停连板天梯",
        domain="pool",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "name", "trade_date", "nums"),
        service=_service("finance_data.service.pool", "limit_step", "get_limit_step"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.pool.limit_step:TushareLimitStep", "get_limit_step", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "nums")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="limit_step", primary_key="symbol"),
        display_name="连板天梯",
    ),
]
