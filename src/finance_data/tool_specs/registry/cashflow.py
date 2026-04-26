"""ToolSpec 注册：cashflow domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_capital_flow_realtime",
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
        display_name="资金流向",
    ),
]
