"""ToolSpec 注册：kline domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_kline_daily_history",
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
        display_name="日线行情",
    ),
    ToolSpec(
        name="tool_get_kline_weekly_history",
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
        display_name="周线行情",
    ),
    ToolSpec(
        name="tool_get_kline_monthly_history",
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
        display_name="月线行情",
    ),
    ToolSpec(
        name="tool_get_kline_minute_history",
        description="获取个股历史分钟K线（5/15/30/60分钟）",
        domain="kline",
        params=(
            _param("symbol", required=True, description="股票代码", example="000001"),
            _param("period", required=False, default="5min", description="K线周期", example="5min",
                   choices=(("5min", "5分钟"), ("15min", "15分钟"), ("30min", "30分钟"), ("60min", "60分钟"))),
            _param("start", required=False, default="20260101", description="开始日期 YYYYMMDD", example="20260414"),
            _param("end", required=False, default="", description="结束日期 YYYYMMDD", example="20260417"),
            _param("adj", required=False, default="qfq", description="复权类型", example="qfq"),
        ),
        return_fields=("date", "time", "period", "open", "high", "low", "close", "volume", "amount"),
        service=_service("finance_data.service.kline", "minute_kline_history", "get_minute_kline_history"),
        providers=(
            _provider("baostock", "finance_data.provider.baostock.kline.minute:BaostockMinuteKline", "get_minute_kline_history"),
        ),
        probe=_probe({"symbol": "000001", "period": "60min", "start": "$RECENT-7", "end": "$RECENT", "adj": "qfq"}, required_fields=("date", "time", "close")),
        metadata=_meta(entity="stock", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="multi", source_priority="baostock", api_name="query_history_k_data_plus", examples=({"symbol": "000001", "period": "5min", "start": "20260414"},)),
        display_name="分钟K线",
    ),
]
