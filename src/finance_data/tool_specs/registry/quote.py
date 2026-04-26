"""ToolSpec 注册：quote domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_stock_quote_realtime",
        description="获取股票实时行情（价格/涨跌/量能/PE/PB/市值/换手率/量比/涨跌停价）",
        domain="quote",
        params=(
            _param("symbol", required=True, description="股票代码", example="000001"),
        ),
        return_fields=("symbol", "name", "price", "pct_chg", "volume", "amount", "market_cap", "pe", "pb", "turnover_rate", "timestamp", "circ_market_cap", "volume_ratio", "limit_up", "limit_down", "prev_close"),
        service=_service("finance_data.service.realtime", "realtime_quote", "get_realtime_quote"),
        providers=(
            _provider("xueqiu", "finance_data.provider.xueqiu.realtime.realtime:XueqiuRealtimeQuote", "get_realtime_quote"),
        ),
        probe=_probe({"symbol": "000001"}, required_fields=("symbol", "price")),
        metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, cache_ttl=20, source="multi", source_priority="xueqiu", api_name="quotec.json", primary_key="symbol", examples=({"symbol": "000001"},)),
        display_name="实时行情",
    ),
]
