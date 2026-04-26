"""ToolSpec 注册：board domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_board_index_history",
        description="获取东财板块索引/快照",
        domain="board",
        params=(
            _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD（单日快照）", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("board_code", "board_name", "idx_type", "trade_date", "pct_chg", "leading_stock"),
        service=_service("finance_data.service.board", "board_index", "get_board_index"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.board.index:TushareBoardIndex", "get_board_index", available_if="tushare_token"),
        ),
        probe=_probe({"idx_type": "行业板块"}, required_fields=("board_code", "board_name")),
        metadata=_meta(entity="board", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index", primary_key="board_code"),
        display_name="板块索引",
    ),
    ToolSpec(
        name="tool_get_board_member_history",
        description="获取东财板块成分股列表",
        domain="board",
        params=(
            _param("board_name", required=True, description="板块名称", example="银行"),
            _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD（单日成分）", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("board_code", "board_name", "idx_type", "trade_date", "symbol", "name"),
        service=_service("finance_data.service.board", "board_member", "get_board_member"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.board.member:TushareBoardMember", "get_board_member", available_if="tushare_token"),
        ),
        probe=_probe({"board_name": "银行", "idx_type": "行业板块"}, required_fields=("symbol", "name")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index,dc_member", primary_key="symbol"),
        display_name="板块成分",
    ),
    ToolSpec(
        name="tool_get_board_kline_history",
        description="获取东财板块日行情",
        domain="board",
        params=(
            _param("board_name", required=True, description="板块名称", example="银行"),
            _param("idx_type", required=False, default="行业板块", description="板块类型", example="行业板块", choices=(("行业板块", "行业板块"), ("概念板块", "概念板块"), ("地域板块", "地域板块"))),
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("board_code", "board_name", "idx_type", "trade_date", "open", "close", "pct_chg"),
        service=_service("finance_data.service.board", "board_daily", "get_board_daily"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.board.daily:TushareBoardDaily", "get_board_daily", available_if="tushare_token"),
        ),
        probe=_probe({"board_name": "银行", "idx_type": "行业板块", "start_date": "$RECENT-30", "end_date": "$RECENT"}, required_fields=("trade_date", "close")),
        metadata=_meta(entity="board", scope="historical", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="dc_index,dc_daily", primary_key="trade_date"),
        display_name="板块行情",
    ),
]
