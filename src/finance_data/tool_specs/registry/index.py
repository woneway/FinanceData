"""ToolSpec 注册：index domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
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
        display_name="指数实时",
    ),
    ToolSpec(
        name="tool_get_index_kline_history",
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
        display_name="指数K线",
    ),
]
