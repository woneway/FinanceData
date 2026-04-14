"""FinanceData 统一 Python API 入口。

Usage:
    from finance_data import FinanceData

    fd = FinanceData(tushare_token="xxx")
    df = fd.kline_daily("000001", start="20260401", end="20260410")
"""
from __future__ import annotations

import os
from typing import Any

from finance_data.interface.types import DataResult


class FinanceData:
    """金融数据统一客户端。

    Args:
        tushare_token: tushare API token（可选，不传则读 TUSHARE_TOKEN 环境变量）
        tushare_api_url: tushare API 代理地址（可选，不传则读 TUSHARE_API_URL）
    """

    def __init__(
        self,
        tushare_token: str = "",
        tushare_api_url: str = "",
    ):
        if tushare_token:
            os.environ["TUSHARE_TOKEN"] = tushare_token
        if tushare_api_url:
            os.environ["TUSHARE_API_URL"] = tushare_api_url

        # 延迟导入 service，确保环境变量已设置
        self._services: dict[str, Any] = {}

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

    def stock_info(self, symbol: str) -> DataResult:
        """获取个股基本信息（公司名称/行业/上市日期/注册资本等）"""
        return self._get_service("stock", "stock_history").get_stock_info_history(symbol)

    # ------------------------------------------------------------------
    # kline — K线行情
    # ------------------------------------------------------------------

    def kline_daily(
        self, symbol: str, start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史日线行情"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "daily_kline_history").get_daily_kline_history(
            symbol, start=start, end=end, adj=adj,
        )

    def kline_weekly(
        self, symbol: str, start: str = "20240101", end: str = "", adj: str = "qfq",
    ) -> DataResult:
        """获取个股历史周线行情"""
        import datetime
        if not end:
            end = datetime.date.today().strftime("%Y%m%d")
        return self._get_service("kline", "weekly_kline_history").get_weekly_kline_history(
            symbol, start=start, end=end, adj=adj,
        )

    def kline_monthly(
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

    def quote(self, symbol: str) -> DataResult:
        """获取个股实时行情（含量比/流通市值/涨跌停价）"""
        return self._get_service("realtime", "realtime_quote").get_realtime_quote(symbol)

    # ------------------------------------------------------------------
    # index — 指数数据
    # ------------------------------------------------------------------

    def index_quote(self, symbol: str = "000001.SH") -> DataResult:
        """获取大盘指数实时行情"""
        return self._get_service("index", "index_quote").get_index_quote_realtime(symbol)

    def index_kline(
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

    def board_index(
        self, idx_type: str = "行业板块", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取东财板块索引/快照"""
        return self._get_service("board", "board_index").get_board_index(
            idx_type=idx_type, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    def board_member(
        self, board_name: str, idx_type: str = "行业板块", trade_date: str = "",
        start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取东财板块成分股列表"""
        return self._get_service("board", "board_member").get_board_member(
            board_name=board_name, idx_type=idx_type, trade_date=trade_date,
            start_date=start_date, end_date=end_date,
        )

    def board_kline(
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

    def financial_summary(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取个股财务摘要（营收/净利润/ROE/毛利率）"""
        return self._get_service("fundamental", "financial_summary").get_financial_summary_history(
            symbol, start_date=start_date, end_date=end_date,
        )

    def dividend(self, symbol: str) -> DataResult:
        """获取个股历史分红记录"""
        return self._get_service("fundamental", "dividend").get_dividend_history(symbol)

    def chip(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        """获取个股筹码分布"""
        return self._get_service("chip", "chip_history").get_chip_distribution_history(
            symbol, start_date=start_date, end_date=end_date,
        )

    # ------------------------------------------------------------------
    # lhb — 龙虎榜
    # ------------------------------------------------------------------

    def lhb_detail(self, start_date: str, end_date: str) -> DataResult:
        """获取龙虎榜每日上榜详情"""
        return self._get_service("lhb", "lhb_detail").get_lhb_detail_history(start_date, end_date)

    def lhb_inst_detail(self, start_date: str, end_date: str) -> DataResult:
        """获取龙虎榜机构买卖统计"""
        return self._get_service("lhb", "lhb_inst_detail").get_lhb_inst_detail_history(start_date, end_date)

    def lhb_stock_stat(self, period: str = "近一月") -> DataResult:
        """获取个股龙虎榜上榜统计"""
        return self._get_service("lhb", "lhb_stock_stat").get_lhb_stock_stat_history(period)

    def lhb_active_traders(self, start_date: str = "", end_date: str = "") -> DataResult:
        """获取活跃游资营业部统计"""
        return self._get_service("lhb", "lhb_active_traders").get_lhb_active_traders_history(
            start_date=start_date, end_date=end_date,
        )

    def lhb_trader_stat(self, period: str = "近一月") -> DataResult:
        """获取营业部龙虎榜战绩排行"""
        return self._get_service("lhb", "lhb_trader_stat").get_lhb_trader_stat_history(period)

    def lhb_stock_detail(self, symbol: str, date: str, flag: str = "全部") -> DataResult:
        """获取个股某日龙虎榜席位明细"""
        return self._get_service("lhb", "lhb_stock_detail").get_lhb_stock_detail_history(
            symbol=symbol, date=date, flag=flag,
        )

    # ------------------------------------------------------------------
    # pool — 题材股池
    # ------------------------------------------------------------------

    def zt_pool(self, date: str) -> DataResult:
        """获取涨停股池"""
        return self._get_service("pool", "zt_pool").get_zt_pool_history(date)

    def strong_stocks(self, date: str) -> DataResult:
        """获取强势股池"""
        return self._get_service("pool", "strong_stocks").get_strong_stocks_history(date)

    def previous_zt(self, date: str) -> DataResult:
        """获取昨日涨停今日表现"""
        return self._get_service("pool", "previous_zt").get_previous_zt_history(date)

    def zbgc_pool(self, date: str) -> DataResult:
        """获取炸板股池"""
        return self._get_service("pool", "zbgc_pool").get_zbgc_pool_history(date)

    def limit_list(
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

    def kpl_list(self, trade_date: str, tag: str = "涨停") -> DataResult:
        """获取开盘啦榜单（涨停/跌停/炸板/自然涨停/竞价）"""
        return self._get_service("pool", "kpl_list").get_kpl_list(
            trade_date=trade_date, tag=tag,
        )

    def limit_step(self, trade_date: str) -> DataResult:
        """获取涨停连板天梯"""
        return self._get_service("pool", "limit_step").get_limit_step(trade_date=trade_date)

    # ------------------------------------------------------------------
    # lhb 追加 — 游资
    # ------------------------------------------------------------------

    def hm_list(self) -> DataResult:
        """获取市场游资名录"""
        return self._get_service("lhb", "hm_list").get_hm_list()

    def hm_detail(
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

    def auction(self, trade_date: str) -> DataResult:
        """获取开盘集合竞价成交数据"""
        return self._get_service("market", "auction").get_auction(trade_date=trade_date)

    def auction_close(self, trade_date: str) -> DataResult:
        """获取收盘集合竞价成交数据"""
        return self._get_service("market", "auction_close").get_auction_close(trade_date=trade_date)

    # ------------------------------------------------------------------
    # north_flow — 北向资金
    # ------------------------------------------------------------------

    def north_capital(self) -> DataResult:
        """获取北向资金日频资金流"""
        return self._get_service("north_flow", "north_flow").get_north_flow_history()

    def north_hold(self, symbol: str = "", **kwargs) -> DataResult:
        """获取北向资金持股明细"""
        return self._get_service("north_flow", "north_stock_hold").get_north_stock_hold_history(
            symbol=symbol, **kwargs,
        )

    # ------------------------------------------------------------------
    # margin — 融资融券
    # ------------------------------------------------------------------

    def margin(self, trade_date: str = "", start_date: str = "", end_date: str = "",
               exchange_id: str = "") -> DataResult:
        """获取融资融券汇总"""
        return self._get_service("margin", "margin").get_margin_history(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
            exchange_id=exchange_id,
        )

    def margin_detail(self, trade_date: str = "", start_date: str = "", end_date: str = "",
                      ts_code: str = "") -> DataResult:
        """获取融资融券个股明细"""
        return self._get_service("margin", "margin_detail").get_margin_detail_history(
            trade_date=trade_date, start_date=start_date, end_date=end_date,
            ts_code=ts_code,
        )

    # ------------------------------------------------------------------
    # market — 市场全局
    # ------------------------------------------------------------------

    def market_stats(self) -> DataResult:
        """获取当日市场涨跌家数统计"""
        return self._get_service("market", "market_realtime").get_market_stats_realtime()

    def trade_calendar(self, start: str, end: str) -> DataResult:
        """获取交易日历"""
        return self._get_service("calendar", "trade_calendar").get_trade_calendar_history(start, end)

    def hot_rank(self) -> DataResult:
        """获取东财热股排行"""
        return self._get_service("hot_rank", "hot_rank").get_hot_rank_realtime()

    def ths_hot(self, trade_date: str = "") -> DataResult:
        """获取同花顺热股排行"""
        return self._get_service("hot_rank", "ths_hot").get_ths_hot(trade_date=trade_date)

    def suspend(self, date: str) -> DataResult:
        """获取停牌股票信息"""
        return self._get_service("suspend", "suspend").get_suspend_history(date)

    # ------------------------------------------------------------------
    # cashflow — 资金流向
    # ------------------------------------------------------------------

    def capital_flow(self, symbol: str) -> DataResult:
        """获取个股资金流向"""
        return self._get_service("cashflow", "stock_capital_flow").get_stock_capital_flow_realtime(symbol)
