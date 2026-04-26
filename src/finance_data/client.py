"""FinanceData 统一 Python API 入口。

Usage:
    from finance_data import FinanceData

    fd = FinanceData()
    df = fd.kline_daily_history("000001", start="20260401", end="20260410")

方法名严格 = MCP tool 名去掉 ``tool_get_`` 前缀。旧名（如 ``kline_daily`` /
``quote``）仍可调用，但发出 ``DeprecationWarning``，详见 ``_DEPRECATED_ALIASES``。

配置统一从项目根目录 config.toml 读取，无需传参。
"""
from __future__ import annotations

import warnings
from typing import Any

from finance_data.interface.types import DataResult


# 旧名 → 新名映射（48 项），由 unify-tool-naming-history-suffix change 引入。
# 客户端方法名规则：= MCP tool 名去掉 `tool_get_` 前缀。
# 旧名通过 __getattr__ 代理到新方法，至少保留 1 个 minor 版本。
_DEPRECATED_ALIASES: dict[str, str] = {
    "stock_info": "stock_info_snapshot",
    "stock_list": "stock_basic_list_snapshot",
    "kline_daily": "kline_daily_history",
    "kline_weekly": "kline_weekly_history",
    "kline_monthly": "kline_monthly_history",
    "kline_minute": "kline_minute_history",
    "quote": "stock_quote_realtime",
    "index_quote": "index_quote_realtime",
    "index_kline": "index_kline_history",
    "board_index": "board_index_history",
    "board_member": "board_member_history",
    "board_kline": "board_kline_history",
    "chip": "chip_distribution_history",
    "financial_summary": "financial_summary_history",
    "dividend": "dividend_history",
    "capital_flow": "capital_flow_realtime",
    "trade_calendar": "trade_calendar_history",
    "market_stats": "market_stats_realtime",
    "suspend": "suspend_daily",
    "hot_rank": "hot_rank_realtime",
    "ths_hot": "ths_hot_history",
    "auction": "auction_history",
    "auction_close": "auction_close_history",
    "daily_market": "daily_market_history",
    "daily_basic_market": "daily_basic_market_history",
    "stk_limit": "stk_limit_daily",
    "lhb_detail": "lhb_detail_history",
    "lhb_stock_stat": "lhb_stock_stat_history",
    "lhb_active_traders": "lhb_active_traders_history",
    "lhb_trader_stat": "lhb_trader_stat_history",
    "lhb_stock_detail": "lhb_stock_detail_daily",
    "lhb_inst_detail": "lhb_inst_detail_history",
    "hm_list": "hm_list_snapshot",
    "hm_detail": "hm_detail_history",
    "zt_pool": "zt_pool_daily",
    "strong_stocks": "strong_stocks_daily",
    "previous_zt": "previous_zt_daily",
    "zbgc_pool": "zbgc_pool_daily",
    "limit_list": "limit_list_history",
    "kpl_list": "kpl_list_history",
    "limit_step": "limit_step_history",
    "north_hold": "north_hold_history",
    "north_capital": "north_capital_snapshot",
    "margin": "margin_history",
    "margin_detail": "margin_detail_history",
    "stock_factor": "stock_factor_pro_history",
    "board_moneyflow": "dc_board_moneyflow_history",
    "market_moneyflow": "dc_market_moneyflow_history",
}


class FinanceData:
    """金融数据统一客户端。

    配置从项目根目录 config.toml 读取，无需手动传入 token。

    方法命名规则：方法名 = 对应 MCP tool 名去掉 ``tool_get_`` 前缀。
    旧名通过 ``__getattr__`` 拦截器以 deprecated alias 暴露，仍可调用但发出
    ``DeprecationWarning``。
    """

    _DEPRECATED_ALIASES = _DEPRECATED_ALIASES

    def __init__(self):
        self._services: dict[str, Any] = {}

    def __getattr__(self, name: str):
        """拦截 deprecated alias 调用：发出 DeprecationWarning 并代理到新方法。

        非 alias 名按 Python 默认行为抛 ``AttributeError``；私有 / dunder 名
        因不在 ``_DEPRECATED_ALIASES`` 中也按默认行为处理。
        """
        new_name = _DEPRECATED_ALIASES.get(name)
        if new_name is None:
            raise AttributeError(
                f"{type(self).__name__!r} object has no attribute {name!r}"
            )
        warnings.warn(
            f"fd.{name}() 已废弃，请改用 fd.{new_name}()。"
            "旧名将在下个 minor 版本移除。",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, new_name)

    def _get_service(self, module: str, name: str):
        key = f"{module}.{name}"
        if key not in self._services:
            import importlib
            mod = importlib.import_module(f"finance_data.service.{module}")
            self._services[key] = getattr(mod, name)
        return self._services[key]

    # ------------------------------------------------------------------
    # stock — 个股信息
    # ------------------------------------------------------------------

    def stock_info_snapshot(self, symbol: str) -> DataResult:
        """获取个股基本信息（公司名称/行业/上市日期/注册资本等）"""
        return self._get_service("stock", "stock_history").get_stock_info_history(symbol)

    # ------------------------------------------------------------------
    # kline — K线行情
    # ------------------------------------------------------------------

    def kline_daily_history(
        self, symbol: str, start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史日线行情"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "daily_kline_history").get_daily_kline_history(
            symbol, start=start, end=end, adj=adj,
        )

    def kline_weekly_history(
        self, symbol: str, start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史周线行情"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "weekly_kline_history").get_weekly_kline_history(
            symbol, start=start, end=end, adj=adj,
        )

    def kline_minute_history(
        self, symbol: str, period: str = "5min",
        start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史分钟K线（5min/15min/30min/60min）"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "minute_kline_history").get_minute_kline_history(
            symbol, period=period, start=start, end=end, adj=adj,
        )

    def kline_monthly_history(
        self, symbol: str, start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史月线行情"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "monthly_kline_history").get_monthly_kline_history(
            symbol, start=start, end=end, adj=adj,
        )

    # ------------------------------------------------------------------
    # quote — 实时行情
    # ------------------------------------------------------------------

    def stock_quote_realtime(self, symbol: str) -> DataResult:
        """获取个股实时行情（含量比/流通市值/涨跌停价）"""
        return self._get_service("realtime", "realtime_quote").get_realtime_quote(symbol)

    # ------------------------------------------------------------------
    # index — 指数数据
    # ------------------------------------------------------------------

    def index_quote_realtime(self, symbol: str = "000001.SH") -> DataResult:
        """获取大盘指数实时行情"""
        return self._get_service("index", "index_quote").get_index_quote_realtime(symbol)

    def index_kline_history(
        self, symbol: str = "000001.SH", start: str = "20240101", end: str = "",
    ) -> DataResult:
        """获取大盘指数历史K线"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("index", "index_history").get_index_history(
            symbol, start=start, end=end,
        )

    # ------------------------------------------------------------------
    # board — 板块数据
    # ------------------------------------------------------------------

    def board_index_history(
        self, idx_type: str = "行业板块", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取东财板块索引/快照"""
        return self._get_service("board", "board_index").get_board_index(
            idx_type=idx_type, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    def board_member_history(
        self, board_name: str, idx_type: str = "行业板块", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取东财板块成分股列表"""
        return self._get_service("board", "board_member").get_board_member(
            board_name=board_name, idx_type=idx_type, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    def board_kline_history(
        self, board_name: str, idx_type: str = "行业板块", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取东财板块日行情"""
        return self._get_service("board", "board_daily").get_board_daily(
            board_name=board_name, idx_type=idx_type, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    # ------------------------------------------------------------------
    # fundamental — 基本面
    # ------------------------------------------------------------------

    def financial_summary_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取个股财务摘要（营收/净利润/ROE/毛利率）"""
        return self._get_service("fundamental", "financial_summary").get_financial_summary_history(
            symbol, start_date=start_date, end_date=end_date,
        )

    def dividend_history(self, symbol: str) -> DataResult:
        """获取个股历史分红记录"""
        return self._get_service("fundamental", "dividend").get_dividend_history(symbol)

    def chip_distribution_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取个股筹码分布"""
        return self._get_service("chip", "chip_history").get_chip_distribution_history(
            symbol, start_date=start_date, end_date=end_date,
        )

    # ------------------------------------------------------------------
    # lhb — 龙虎榜
    # ------------------------------------------------------------------

    def lhb_detail_history(self, start_date: str, end_date: str) -> DataResult:
        """获取龙虎榜每日上榜详情"""
        return self._get_service("lhb", "lhb_detail").get_lhb_detail_history(start_date, end_date)

    def lhb_inst_detail_history(self, start_date: str, end_date: str) -> DataResult:
        """获取龙虎榜机构买卖统计"""
        return self._get_service("lhb", "lhb_inst_detail").get_lhb_inst_detail_history(start_date, end_date)

    def lhb_stock_stat_history(self, period: str = "近一月") -> DataResult:
        """获取个股龙虎榜上榜统计"""
        return self._get_service("lhb", "lhb_stock_stat").get_lhb_stock_stat_history(period)

    def lhb_active_traders_history(self, start_date: str = "", end_date: str = "") -> DataResult:
        """获取活跃游资营业部统计"""
        return self._get_service("lhb", "lhb_active_traders").get_lhb_active_traders_history(
            start_date=start_date, end_date=end_date,
        )

    def lhb_trader_stat_history(self, period: str = "近一月") -> DataResult:
        """获取营业部龙虎榜战绩排行"""
        return self._get_service("lhb", "lhb_trader_stat").get_lhb_trader_stat_history(period)

    def lhb_stock_detail_daily(self, symbol: str, date: str, flag: str = "全部") -> DataResult:
        """获取个股某日龙虎榜席位明细"""
        return self._get_service("lhb", "lhb_stock_detail").get_lhb_stock_detail_history(
            symbol=symbol, date=date, flag=flag,
        )

    # ------------------------------------------------------------------
    # pool — 题材股池
    # ------------------------------------------------------------------

    def zt_pool_daily(self, date: str) -> DataResult:
        """获取涨停股池"""
        return self._get_service("pool", "zt_pool").get_zt_pool_history(date)

    def strong_stocks_daily(self, date: str) -> DataResult:
        """获取强势股池"""
        return self._get_service("pool", "strong_stocks").get_strong_stocks_history(date)

    def previous_zt_daily(self, date: str) -> DataResult:
        """获取昨日涨停今日表现"""
        return self._get_service("pool", "previous_zt").get_previous_zt_history(date)

    def zbgc_pool_daily(self, date: str) -> DataResult:
        """获取炸板股池"""
        return self._get_service("pool", "zbgc_pool").get_zbgc_pool_history(date)

    def limit_list_history(
        self,
        trade_date: str = "",
        limit_type: str = "涨停池",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        """获取同花顺涨跌停榜单（涨停池/连扳池/炸板池/跌停池/冲刺涨停）"""
        return self._get_service("pool", "limit_list").get_limit_list(
            trade_date=trade_date, limit_type=limit_type,
            start_date=start_date, end_date=end_date,
        )

    def kpl_list_history(self, trade_date: str, tag: str = "涨停") -> DataResult:
        """获取开盘啦榜单（涨停/跌停/炸板/自然涨停/竞价）"""
        return self._get_service("pool", "kpl_list").get_kpl_list(
            trade_date=trade_date, tag=tag,
        )

    def limit_step_history(self, trade_date: str) -> DataResult:
        """获取涨停连板天梯"""
        return self._get_service("pool", "limit_step").get_limit_step(trade_date=trade_date)

    # ------------------------------------------------------------------
    # lhb 追加 — 游资
    # ------------------------------------------------------------------

    def hm_list_snapshot(self) -> DataResult:
        """获取市场游资名录"""
        return self._get_service("lhb", "hm_list").get_hm_list()

    def hm_detail_history(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
        hm_name: str = "",
    ) -> DataResult:
        """获取游资每日交易明细"""
        return self._get_service("lhb", "hm_detail").get_hm_detail(
            trade_date=trade_date, start_date=start_date,
            end_date=end_date, hm_name=hm_name,
        )

    # ------------------------------------------------------------------
    # market 追加 — 竞价
    # ------------------------------------------------------------------

    def auction_history(self, trade_date: str) -> DataResult:
        """获取开盘集合竞价成交数据"""
        return self._get_service("market", "auction").get_auction(trade_date=trade_date)

    def auction_close_history(self, trade_date: str) -> DataResult:
        """获取收盘集合竞价成交数据"""
        return self._get_service("market", "auction_close").get_auction_close(trade_date=trade_date)

    # ------------------------------------------------------------------
    # north_flow — 北向资金
    # ------------------------------------------------------------------

    def north_capital_snapshot(self) -> DataResult:
        """获取北向资金日频资金流"""
        return self._get_service("north_flow", "north_flow").get_north_flow_history()

    def north_hold_history(self, symbol: str = "", **kwargs) -> DataResult:
        """获取北向资金持股明细"""
        return self._get_service("north_flow", "north_stock_hold").get_north_stock_hold_history(
            symbol=symbol, **kwargs,
        )

    # ------------------------------------------------------------------
    # margin — 融资融券
    # ------------------------------------------------------------------

    def margin_history(self, trade_date: str = "", start_date: str = "", end_date: str = "",
               exchange_id: str = "") -> DataResult:
        """获取融资融券汇总"""
        return self._get_service("margin", "margin").get_margin_history(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
            exchange_id=exchange_id,
        )

    def margin_detail_history(self, trade_date: str = "", start_date: str = "", end_date: str = "",
                      ts_code: str = "") -> DataResult:
        """获取融资融券个股明细"""
        return self._get_service("margin", "margin_detail").get_margin_detail_history(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
            ts_code=ts_code,
        )

    # ------------------------------------------------------------------
    # market — 市场全局
    # ------------------------------------------------------------------

    def market_stats_realtime(self) -> DataResult:
        """获取当日市场涨跌家数统计"""
        return self._get_service("market", "market_realtime").get_market_stats_realtime()

    def trade_calendar_history(self, start: str, end: str) -> DataResult:
        """获取交易日历"""
        return self._get_service("calendar", "trade_calendar").get_trade_calendar_history(start, end)

    def hot_rank_realtime(self) -> DataResult:
        """获取东财热股排行"""
        return self._get_service("hot_rank", "hot_rank").get_hot_rank_realtime()

    def ths_hot_history(self, trade_date: str = "") -> DataResult:
        """获取同花顺热股排行"""
        return self._get_service("hot_rank", "ths_hot").get_ths_hot(trade_date=trade_date)

    def suspend_daily(self, date: str) -> DataResult:
        """获取停牌股票信息"""
        return self._get_service("suspend", "suspend").get_suspend_history(date)

    # ------------------------------------------------------------------
    # cashflow — 资金流向
    # ------------------------------------------------------------------

    def capital_flow_realtime(self, symbol: str) -> DataResult:
        """获取个股资金流向"""
        return self._get_service("cashflow", "stock_capital_flow").get_stock_capital_flow_realtime(symbol)

    # ------------------------------------------------------------------
    # 全市场按日期查询（PlaybookOS 消费）
    # ------------------------------------------------------------------

    def daily_market_history(self, trade_date: str) -> DataResult:
        """获取全市场日线行情（OHLCV，~5000股）"""
        return self._get_service("daily_market", "daily_market").get_daily_market(trade_date)

    def daily_basic_market_history(self, trade_date: str) -> DataResult:
        """获取全市场日频基本面（换手率/量比/PE/PB/市值）"""
        return self._get_service("daily_basic", "daily_basic_market").get_daily_basic_market(trade_date)

    def stk_limit_daily(self, trade_date: str) -> DataResult:
        """获取全市场涨跌停价"""
        return self._get_service("stk_limit", "stk_limit").get_stk_limit(trade_date)

    def stock_basic_list_snapshot(self, list_status: str = "L") -> DataResult:
        """获取全市场股票列表（名称/行业/ST标记）"""
        return self._get_service("stock", "stock_basic_list").get_stock_basic_list(list_status)

    # ------------------------------------------------------------------
    # technical — 技术因子
    # ------------------------------------------------------------------

    def stock_factor_pro_history(
        self, ts_code: str = "", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取股票技术面因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI/估值）"""
        return self._get_service("technical", "stock_factor").get_stock_factor(
            ts_code=ts_code, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    # ------------------------------------------------------------------
    # fund_flow — 资金流向（板块+大盘）
    # ------------------------------------------------------------------

    def dc_board_moneyflow_history(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
        ts_code: str = "", content_type: str = "",
    ) -> DataResult:
        """获取东财概念及行业板块资金流向"""
        return self._get_service("fund_flow", "board_moneyflow").get_board_moneyflow(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
            ts_code=ts_code, content_type=content_type,
        )

    def dc_market_moneyflow_history(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取大盘资金流向（沪深整体）"""
        return self._get_service("fund_flow", "market_moneyflow").get_market_moneyflow(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
        )
