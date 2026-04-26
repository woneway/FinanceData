"""ToolSpec 注册：market domain。"""
from __future__ import annotations

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import (
    _meta, _param, _probe, _provider, _service,
)

SPECS: list[ToolSpec] = [
    ToolSpec(
        name="tool_get_trade_calendar_history",
        description="获取交易日历",
        domain="market",
        params=(
            _param("start", required=True, description="开始日期 YYYYMMDD", example="20240301"),
            _param("end", required=True, description="结束日期 YYYYMMDD", example="20240401"),
        ),
        return_fields=("date", "is_open"),
        service=_service("finance_data.service.calendar", "trade_calendar", "get_trade_calendar_history"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.calendar.history:TushareTradeCalendar", "get_trade_calendar_history", available_if="tushare_token"),
            _provider("akshare", "finance_data.provider.akshare.calendar.history:AkshareTradeCalendar", "get_trade_calendar_history"),
            _provider("baostock", "finance_data.provider.baostock.calendar.history:BaostockTradeCalendar", "get_trade_calendar_history"),
        ),
        probe=_probe({"start": "$RECENT-30", "end": "$RECENT"}, required_fields=("date",)),
        metadata=_meta(entity="market", scope="historical", data_freshness="historical", update_timing="T+1_17:00", supports_history=True, history_start="19900101", source="both", source_priority="tushare", api_name="trade_cal", primary_key="date", examples=({"start": "20240101", "end": "20240401"},)),
        display_name="交易日历",
    ),
    ToolSpec(
        name="tool_get_market_stats_realtime",
        description="获取当日市场涨跌家数统计（盘中实时）",
        domain="market",
        params=(),
        return_fields=("date", "up_count", "down_count", "flat_count", "total_count", "total_amount"),
        service=_service("finance_data.service.market", "market_realtime", "get_market_stats_realtime"),
        providers=(
            _provider("akshare", "finance_data.provider.akshare.market.realtime:AkshareMarketRealtime", "get_market_stats_realtime"),
        ),
        probe=_probe({}, required_fields=("date",)),
        metadata=_meta(entity="market_stats", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_market_activity_legu", limitations=("tushare 无等效接口",), primary_key="date"),
        display_name="涨跌统计",
    ),
    ToolSpec(
        name="tool_get_suspend_daily",
        description="获取停牌股票信息",
        domain="market",
        params=(
            _param("date", required=True, description="交易日期 YYYYMMDD", example="20240408"),
        ),
        return_fields=("symbol", "name", "suspend_date", "resume_date", "suspend_reason"),
        service=_service("finance_data.service.suspend", "suspend", "get_suspend_history"),
        providers=(
            _provider("akshare", "finance_data.provider.akshare.suspend.history:AkshareSuspend", "get_suspend_history"),
            _provider("tushare", "finance_data.provider.tushare.suspend.history:TushareSuspend", "get_suspend_history", available_if="tushare_token"),
        ),
        probe=_probe({"date": "$RECENT"}, required_fields=("symbol",)),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=False, source="both", source_priority="akshare", api_name="stock_tfp_em,suspend_d", primary_key="symbol"),
        display_name="停牌信息",
    ),
    ToolSpec(
        name="tool_get_hot_rank_realtime",
        description="获取热股排行（东财人气榜）",
        domain="market",
        params=(),
        return_fields=("rank", "symbol", "name", "current", "pct_chg"),
        service=_service("finance_data.service.hot_rank", "hot_rank", "get_hot_rank_realtime"),
        providers=(
            _provider("akshare", "finance_data.provider.akshare.hot_rank.realtime:AkshareHotRank", "get_hot_rank_realtime"),
        ),
        probe=_probe({}, required_fields=("rank", "symbol")),
        metadata=_meta(entity="stock", scope="realtime", data_freshness="realtime", update_timing="T+0", supports_history=False, source="akshare", source_priority="akshare", api_name="stock_hot_rank_em", primary_key="rank"),
        display_name="东财人气榜",
    ),
    ToolSpec(
        name="tool_get_ths_hot_history",
        description="获取同花顺热股排行",
        domain="market",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("rank", "symbol", "name", "pct_chg", "current_price", "hot", "concept"),
        service=_service("finance_data.service.hot_rank", "ths_hot", "get_ths_hot"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.hot_rank.ths_hot:TushareThsHot", "get_ths_hot", available_if="tushare_token"),
        ),
        probe=_probe({}, required_fields=("rank", "symbol")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="ths_hot", primary_key="rank"),
        display_name="同花顺热股",
    ),
    ToolSpec(
        name="tool_get_auction_history",
        description="获取开盘集合竞价成交数据",
        domain="market",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "trade_date", "price", "volume", "amount", "pre_close", "volume_ratio"),
        service=_service("finance_data.service.market", "auction", "get_auction"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.market.auction:TushareAuction", "get_auction", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "price")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+0", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="stk_auction", primary_key="symbol"),
        display_name="开盘竞价",
    ),
    ToolSpec(
        name="tool_get_auction_close_history",
        description="获取收盘集合竞价成交数据",
        domain="market",
        params=(
            _param("trade_date", required=False, default="", description="交易日期 YYYYMMDD", example="20260410"),
            _param("start_date", required=False, default="", description="开始日期 YYYYMMDD", example="20260401"),
            _param("end_date", required=False, default="", description="结束日期 YYYYMMDD", example="20260410"),
        ),
        return_fields=("symbol", "trade_date", "close", "volume", "amount", "vwap"),
        service=_service("finance_data.service.market", "auction_close", "get_auction_close"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.market.auction_close:TushareAuctionClose", "get_auction_close", available_if="tushare_stock_minute_permission", notes="需要 TuShare 股票分钟权限"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "close")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20200101", source="tushare", source_priority="tushare", api_name="stk_auction_c", limitations=("TuShare 官方要求开通股票分钟权限后可调取",), primary_key="symbol"),
        display_name="收盘竞价",
    ),
    ToolSpec(
        name="tool_get_daily_market_history",
        description="获取全市场日线行情（OHLCV）",
        domain="market",
        params=(
            _param("trade_date", required=True, description="交易日期 YYYYMMDD", example="20260414"),
        ),
        return_fields=("symbol", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "volume", "amount"),
        service=_service("finance_data.service.daily_market", "daily_market", "get_daily_market"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.daily_market.history:TushareDailyMarket", "get_daily_market", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "close", "volume")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="19900101", source="tushare", source_priority="tushare", api_name="daily", primary_key="symbol"),
        display_name="全市场日线",
    ),
    ToolSpec(
        name="tool_get_daily_basic_market_history",
        description="获取全市场日频基本面（换手率/量比/PE/PB/市值）",
        domain="market",
        params=(
            _param("trade_date", required=True, description="交易日期 YYYYMMDD", example="20260414"),
        ),
        return_fields=("symbol", "trade_date", "close", "turnover_rate", "turnover_rate_f", "volume_ratio", "pe_ttm", "pb", "total_mv", "circ_mv"),
        service=_service("finance_data.service.daily_basic", "daily_basic_market", "get_daily_basic_market"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.daily_basic.history:TushareDailyBasicMarket", "get_daily_basic_market", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "turnover_rate")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20040101", source="tushare", source_priority="tushare", api_name="daily_basic", primary_key="symbol"),
        display_name="全市场基本面",
    ),
    ToolSpec(
        name="tool_get_stk_limit_daily",
        description="获取全市场涨跌停价",
        domain="market",
        params=(
            _param("trade_date", required=True, description="交易日期 YYYYMMDD", example="20260414"),
        ),
        return_fields=("symbol", "trade_date", "pre_close", "up_limit", "down_limit"),
        service=_service("finance_data.service.stk_limit", "stk_limit", "get_stk_limit"),
        providers=(
            _provider("tushare", "finance_data.provider.tushare.stk_limit.history:TushareStkLimit", "get_stk_limit", available_if="tushare_token"),
        ),
        probe=_probe({"trade_date": "$RECENT"}, required_fields=("symbol", "up_limit")),
        metadata=_meta(entity="stock", scope="daily", data_freshness="end_of_day", update_timing="T+1_16:00", supports_history=True, history_start="20070101", source="tushare", source_priority="tushare", api_name="stk_limit", primary_key="symbol"),
        display_name="涨跌停价",
    ),
]
