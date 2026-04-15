# FinanceData 接口列表与新增流程

## 新增接口流程

> 使用 `.claude/skills/add-new-interface.md` Skill 获得完整步骤指导。

1. **interface 层**：在 `interface/<domain>/` 定义 Protocol + dataclass model（含 `to_dict()`）
2. **provider 层**：在 `provider/<source>/<domain>/` 实现 provider 类
3. **service 层**：在 `service/<domain>.py` 创建 Dispatcher + `_build_*()` + 模块级实例
4. **mcp 层**：在 `mcp/server.py` 添加 `@mcp.tool()` 函数（含规范 docstring）
5. **metadata**：在 `tool_specs/registry.py` 注册 ToolSpec
6. **测试**：在 `tests/provider/<domain>/` 添加 mock 测试
7. **校验**：`python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
8. **更新 CLAUDE.md**：更新接口计数

## 当前接口（47 个）

| Tool | 领域 | 说明 |
|------|------|------|
| `tool_get_stock_info_snapshot` | stock | 个股基本信息，tushare+xueqiu |
| `tool_get_stock_basic_list_snapshot` | stock | 全市场股票列表（名称/行业/ST标记），tushare |
| `tool_get_kline_daily_history` | kline | 个股历史日线行情，tushare+akshare(腾讯) |
| `tool_get_kline_weekly_history` | kline | 个股历史周线行情（每日更新），tushare |
| `tool_get_kline_monthly_history` | kline | 个股历史月线行情（每日更新），tushare |
| `tool_get_stock_quote_realtime` | quote | 实时行情（价格/涨跌/量能/PE/PB/市值/换手率/量比/涨跌停价），xueqiu+tencent |
| `tool_get_index_quote_realtime` | index | 大盘指数实时行情，akshare(新浪)+xueqiu |
| `tool_get_index_kline_history` | index | 大盘指数历史 K线，tushare+xueqiu |
| `tool_get_board_index_history` | board | 东财板块索引/快照（行业/概念/地域），tushare |
| `tool_get_board_member_history` | board | 东财板块成分股列表，tushare |
| `tool_get_board_kline_history` | board | 东财板块日行情，tushare |
| `tool_get_chip_distribution_history` | fundamental | 个股筹码分布（获利比例、成本、集中度），tushare |
| `tool_get_financial_summary_history` | fundamental | 财务摘要（营收、净利润、ROE、毛利率），akshare(新浪)+tushare+xueqiu |
| `tool_get_dividend_history` | fundamental | 历史分红记录，akshare(同花顺)+tushare+xueqiu |
| `tool_get_lhb_detail_history` | lhb | 龙虎榜每日上榜详情（按日期范围），akshare(东财)+tushare |
| `tool_get_lhb_inst_detail_history` | lhb | 龙虎榜机构买卖每日统计，akshare(东财) |
| `tool_get_lhb_stock_stat_history` | lhb | 个股上榜统计（近5日），akshare(新浪) |
| `tool_get_lhb_active_traders_history` | lhb | 活跃游资营业部统计，akshare(新浪) |
| `tool_get_lhb_trader_stat_history` | lhb | 营业部龙虎榜战绩排行，akshare(新浪) |
| `tool_get_lhb_stock_detail_daily` | lhb | 个股某日龙虎榜席位明细，akshare(新浪) |
| `tool_get_hm_list_snapshot` | lhb | 市场游资名录（昵称/描述/营业部），tushare |
| `tool_get_hm_detail_history` | lhb | 游资每日交易明细（买卖股票/金额），tushare |
| `tool_get_zt_pool_daily` | pool | 涨停股池（连板数/封板资金），akshare(东财) |
| `tool_get_strong_stocks_daily` | pool | 强势股池（新高/量比），akshare(东财) |
| `tool_get_previous_zt_daily` | pool | 昨日涨停今日表现，akshare(东财) |
| `tool_get_zbgc_pool_daily` | pool | 炸板股池（冲板后开板），akshare(东财) |
| `tool_get_limit_list_history` | pool | 同花顺涨跌停榜单（涨停/连扳/炸板/跌停/冲刺，支持日期范围），tushare |
| `tool_get_kpl_list_daily` | pool | 开盘啦榜单（涨停/跌停/炸板/自然涨停/竞价），tushare |
| `tool_get_limit_step_daily` | pool | 涨停连板天梯，tushare |
| `tool_get_north_capital_snapshot` | north_flow | 北向资金日频资金流（沪深股通），akshare(东财) |
| `tool_get_north_hold_history` | north_flow | 北向资金持股明细（支持日期范围），tushare |
| `tool_get_margin_history` | margin | 融资融券汇总（按交易所），tushare |
| `tool_get_margin_detail_history` | margin | 融资融券个股明细，tushare+akshare(上交所)+xueqiu |
| `tool_get_capital_flow_realtime` | cashflow | 个股资金流向（主力净流入），xueqiu |
| `tool_get_market_stats_realtime` | market | 市场涨跌统计（盘中实时，涨/跌/平家数），akshare(乐估) |
| `tool_get_trade_calendar_history` | market | 交易日历（is_open 标记），tushare+akshare(新浪) |
| `tool_get_hot_rank_realtime` | market | 热股排行（东财人气榜），akshare(东财) |
| `tool_get_ths_hot_daily` | market | 同花顺热股排行（含概念/热度/上榜理由），tushare |
| `tool_get_suspend_daily` | market | 停牌股票信息，akshare(东财)+tushare |
| `tool_get_auction_daily` | market | 开盘集合竞价成交（全市场），tushare |
| `tool_get_auction_close_daily` | market | 收盘集合竞价成交（全市场），tushare |
| `tool_get_daily_market_history` | market | 全市场日线行情 OHLCV（~5000股/日），tushare |
| `tool_get_daily_basic_market_history` | market | 全市场日频基本面（换手率/量比/PE/PB/市值），tushare |
| `tool_get_stk_limit_daily` | market | 全市场涨跌停价，tushare |
| `tool_get_stock_factor_pro_history` | technical | 股票技术面因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI/估值），tushare |
| `tool_get_dc_board_moneyflow_history` | fund_flow | 东财概念及行业板块资金流向，tushare |
| `tool_get_dc_market_moneyflow_history` | fund_flow | 大盘资金流向（沪深整体），tushare |

### 已下线接口

| Tool | 原因 |
|------|------|
| `tool_get_kline_history` | 已拆分为 daily/weekly/monthly 三个独立工具，分钟级已下线 |
| `tool_get_earnings_forecast_history` | 依赖东财 stock_yjyg_em，无 provider 实现 |
| `tool_get_sector_capital_flow` | push2.eastmoney.com 域名不可达 |
| `tool_get_sector_list` | push2.eastmoney.com 域名不可达（stock_board_industry_name_em） |
| `tool_get_sector_rank_realtime` | 已被 tool_get_board_index_history 替代 |
| `tool_get_sector_member` | 已被 tool_get_board_member_history 替代 |
| `tool_get_sector_history` | 已被 tool_get_board_kline_history 替代 |
