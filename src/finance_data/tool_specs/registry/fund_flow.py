"""ToolSpec 注册：fund_flow domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_dc_board_moneyflow_history",
        description="获取东财概念及行业板块资金流向",
        domain="fund_flow",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260414"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260414"),
            _param("ts_code", required=False, default="", description="板块代码", example="BK1032"),
            _param("content_type", required=False, default="", description="类型：概念/行业/地域", example="概念", choices=(("概念", "概念板块"), ("行业", "行业板块"), ("地域", "地域板块"))),
        ),
        return_fields=("trade_date", "ts_code", "name", "content_type", "pct_chg", "close", "net_amount", "net_amount_rate", "buy_elg_amount", "buy_lg_amount", "buy_md_amount", "buy_sm_amount", "buy_sm_amount_stock", "rank"),
        service=_service("finance_data.service.fund_flow", "board_moneyflow", "get_board_moneyflow"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.fund_flow.board:TushareBoardMoneyflow", "get_board_moneyflow", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT", "start_date": "", "end_date": "", "ts_code": "", "content_type": ""}, required_fields=("trade_date", "name")),
        metadata=_meta(entity="board", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="moneyflow_ind_dc", primary_key="trade_date"),
        display_name="板块资金流",
    ),
    ToolSpec(
        name="tool_get_dc_market_moneyflow_history",
        description="获取大盘资金流向（沪深整体）",
        domain="fund_flow",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260414"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260414"),
        ),
        return_fields=("trade_date", "close_sh", "pct_change_sh", "close_sz", "pct_change_sz", "net_amount", "net_amount_rate", "buy_lg_amount", "buy_elg_amount"),
        service=_service("finance_data.service.fund_flow", "market_moneyflow", "get_market_moneyflow"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.fund_flow.market:TushareMarketMoneyflow", "get_market_moneyflow", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT", "start_date": "", "end_date": ""}, required_fields=("trade_date",)),
        metadata=_meta(entity="market", scope="daily", data_freshness="end_of_day", update_timing="T+1_17:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="moneyflow_mkt_dc", primary_key="trade_date"),
        display_name="大盘资金流",
    ),
]
