"""ToolSpec 注册：margin domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_margin_history",
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
        ),
        probe=_probe({"trade_date": "$RECENT-2", "start_date": "", "end_date": "", "exchange_id": ""}, required_fields=("date",)),
        metadata=_meta(entity="market", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20100101", source="tushare", source_priority="tushare", api_name="margin", primary_key="date", limitations=("akshare 源 rzche=0（融资偿还额缺失），仅 tushare 可用",)),
        display_name="两融汇总",
    ),
    ToolSpec(
        name="tool_get_margin_detail_history",
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
        display_name="两融明细",
    ),
]
