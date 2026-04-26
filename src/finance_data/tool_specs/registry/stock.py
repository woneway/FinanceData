"""ToolSpec 注册：stock domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_stock_info_snapshot",
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
        display_name="个股基本信息",
    ),
    ToolSpec(
        name="tool_get_stock_basic_list_snapshot",
        description="获取全市场股票列表（名称/行业/ST标记）",
        domain="stock",
        params=(
            _param("list_status", required=False, default="L", description="上市状态 L=在市 D=退市 P=暂停", example="L", choices=(("L", "在市"), ("D", "退市"), ("P", "暂停上市"))),
        ),
        return_fields=("symbol", "name", "industry", "market", "list_date", "is_st"),
        service=_service("finance_data.service.stock", "stock_basic_list", "get_stock_basic_list"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.stock.basic_list:TushareStockBasicList", "get_stock_basic_list", available_if="tushare_token"),
        ),
        probe=_probe({"list_status": "L"}, required_fields=("symbol", "name")),
        metadata=_meta(entity="stock_info", scope="snapshot", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="tushare", source_priority="tushare", api_name="stock_basic", primary_key="symbol"),
        display_name="股票列表",
    ),
]
