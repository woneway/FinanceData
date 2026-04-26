"""ToolSpec 注册：technical domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_stock_factor_pro_history",
        description="获取股票技术面因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI/估值/量价）",
        domain="technical",
        params=(
            _param("ts_code", required=False, default="", description="股票代码（tushare格式如000001.SZ）", example="000001.SZ"),
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260414"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260414"),
        ),
        return_fields=("trade_date", "symbol", "close", "volume", "amount", "pct_chg", "ma5", "ma10", "ma20", "ma30", "ma60", "ma90", "ma250", "macd_dif", "macd_dea", "macd", "kdj_k", "kdj_d", "kdj_j", "rsi_6", "rsi_12", "rsi_24", "boll_upper", "boll_mid", "boll_lower", "cci", "pe_ttm", "pb", "turnover_rate", "total_mv", "circ_mv"),
        service=_service("finance_data.service.technical", "stock_factor", "get_stock_factor"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.technical.factor:TushareStockFactor", "get_stock_factor", available_if="tushare_token"),
        ),
        probe=_probe({"ts_code": "000001.SZ", "trade_date": "$RECENT", "start_date": "", "end_date": ""}, required_fields=("trade_date", "symbol")),
        metadata=_meta(entity="stock", scope="history", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20050101", source="tushare", source_priority="tushare", api_name="stk_factor_pro", primary_key="trade_date", limitations=("5000积分权限", "单次最多10000条")),
        display_name="技术因子",
    ),
]
