"""ToolSpec 注册：north_flow domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_north_hold_history",
        description="获取北向资金持股明细",
        domain="north_flow",
        params=(
            _param("symbol", required=False, default="", description="股票代码", example="600519.SH"),
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20240408"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20240401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20240408"),
            _param("exchange", required=False, default="", description="市场筛选（沪股通/深股通/SH/SZ）", example="SH"),
        ),
        return_fields=("symbol", "name", "date", "hold_volume", "hold_ratio", "exchange"),
        service=_service("finance_data.service.north_flow", "north_stock_hold", "get_north_stock_hold_history"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.north_flow.history:TushareNorthStockHold", "get_north_stock_hold_history", available_if="tushare_token"),
        ),
        probe=_probe({"symbol": "", "trade_date": "$RECENT-3", "start_date": "", "end_date": "", "exchange": ""}, required_fields=("symbol",)),
        metadata=_meta(entity="stock", scope="history", data_freshness="end_of_day", update_timing="T+1_15:30", supports_history=True, source="tushare", source_priority="tushare", api_name="hk_hold", limitations=("交易所自2024年8月20日起停止发布日度数据，改为季度披露",), primary_key="symbol"),
        display_name="北向持股",
    ),
    ToolSpec(
        name="tool_get_north_capital_snapshot",
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
        display_name="北向资金流",
    ),
]
