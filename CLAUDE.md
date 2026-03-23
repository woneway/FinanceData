# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。

## MCP 配置

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "/Users/lianwu/ai/projects/FinanceData/.venv/bin/python",
      "args": ["/Users/lianwu/ai/projects/FinanceData/mcp_server.py"],
      "env": {
        "TUSHARE_TOKEN": "your_token"
      }
    }
  }
}
```

## 环境变量

- `TUSHARE_TOKEN`：tushare API token（tushare 接口必须）
- `TUSHARE_API_URL`：tushare API 地址（可选，默认官方地址；使用第三方代理时设置）

## 开发

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```

## 目录结构

Domain-first 架构：`src/finance_data/provider/<domain>/`，每个领域独立 models.py + akshare.py + tushare.py。

## 新增接口流程

1. 在 `src/finance_data/provider/<domain>/` 下新建或修改 akshare.py / tushare.py
2. 在 `tests/provider/<domain>/` 下添加对应测试
3. 在 `src/finance_data/mcp/server.py` 添加 MCP tool
4. 更新 CLAUDE.md 接口列表

## 当前接口（22 个）

| Tool | 领域 | 说明 |
|------|------|------|
| `tool_get_stock_info` | stock | 个股基本信息，akshare 优先，fallback tushare |
| `tool_get_kline` | kline | K线历史数据（daily/weekly/monthly/分钟级），akshare+tushare |
| `tool_get_realtime_quote` | realtime | 实时行情（含 20 分钟缓存），akshare+tushare |
| `tool_get_index_quote` | index | 大盘指数实时行情，akshare+tushare |
| `tool_get_index_history` | index | 大盘指数历史 K线，akshare+tushare |
| `tool_get_sector_rank` | sector | 行业板块涨跌排名，仅 akshare |
| `tool_get_chip_distribution` | chip | 个股筹码分布（获利比例、成本、集中度），仅 akshare |
| `tool_get_financial_summary` | fundamental | 财务摘要（营收、净利润、ROE、毛利率），akshare+tushare |
| `tool_get_dividend` | fundamental | 历史分红记录，akshare+tushare |
| `tool_get_earnings_forecast` | fundamental | 业绩预告，akshare 优先 |
| `tool_get_fund_flow` | cashflow | 个股资金流向（主力净流入），仅 akshare |
| `tool_get_trade_calendar` | calendar | 交易日历（is_open 标记），仅 tushare |
| `tool_get_market_stats` | market | 市场涨跌统计（涨/跌/平家数、总成交额），仅 akshare |
| `tool_get_lhb_detail` | lhb | 龙虎榜每日上榜详情（按日期范围），akshare 优先+tushare |
| `tool_get_lhb_stock_stat` | lhb | 个股上榜统计（近一月/三月/六月/一年），仅 akshare |
| `tool_get_lhb_active_traders` | lhb | 每日活跃游资营业部（席位追踪），仅 akshare |
| `tool_get_lhb_trader_stat` | lhb | 营业部统计-游资战绩排行（近一月等），仅 akshare |
| `tool_get_lhb_stock_detail` | lhb | 个股某日龙虎榜席位明细（买入/卖出），仅 akshare |
| `tool_get_zt_pool` | pool | 涨停股池（首板/连板检测），仅 akshare |
| `tool_get_strong_stocks` | pool | 强势股池（60日新高/量比放大），仅 akshare |
| `tool_get_previous_zt` | pool | 昨日涨停今日数据（低吸检测），仅 akshare |
| `tool_get_zbgc_pool` | pool | 炸板股池（冲板后开板，低吸补充），仅 akshare |

## Provider 优先级

`akshare`（无需 token）→ `tushare`（需 `TUSHARE_TOKEN`）
