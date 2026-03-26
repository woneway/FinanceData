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
- `XUEQIU_COOKIE`：雪球登录 cookie 字符串（可选，手动指定时优先级最高）

### 雪球 Cookie 自动获取

雪球 K 线等需要登录的接口，cookie 通过 4 层 fallback 自动获取，通常无需手动配置：

1. **环境变量** `XUEQIU_COOKIE`（手动设置时最优先）
2. **浏览器自动提取**：从 Chrome 所有 Profile / Safari 读取（需 `browser-cookie3`，在浏览器中登录过 xueqiu.com 即可）
3. **文件缓存** `~/.finance_data/xueqiu_cookie.json`（24h TTL，浏览器提取成功后自动缓存）
4. **访客 cookie**（访问雪球首页获取，仅支持实时行情，不支持 K 线）

检测逻辑：`finance_data.provider.xueqiu.client.has_login_cookie()` 按上述顺序检查。

## 开发

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install -e ".[browser]"  # 可选：启用浏览器 cookie 自动提取
.venv/bin/pytest tests/ -v
```

## 目录结构

Domain-first 架构，四层分离：

```
src/finance_data/
├── interface/          # 协议层：Protocol 定义 + Pydantic models
│   └── <domain>/       # 每个领域: protocol.py + models.py
├── provider/           # 数据源实现
│   ├── akshare/        # akshare（无需 token，约 20 个领域）
│   ├── tushare/        # tushare（需 TUSHARE_TOKEN，约 15 个领域）
│   ├── xueqiu/         # 雪球（海外可达，4 个领域：realtime/kline/index + client.py）
│   └── metadata/       # 元数据：registry.py（ToolMeta 注册）+ validator.py
├── service/            # 业务编排层：Dispatcher 管理多 provider fallback 链
│   └── <domain>.py     # 每个领域一个 service，构建 provider 优先级链
├── dashboard/          # 健康监控看板（FastAPI 后端 + 静态前端）
│   ├── app.py          # FastAPI 路由：/api/tools, /api/providers, /api/health, /api/metrics
│   ├── health.py       # 探测逻辑：逐 tool×provider 调用并返回 SSE 流
│   ├── metrics.py      # 内存指标存储（调用次数、耗时、成功率）
│   ├── models.py       # Pydantic models（ToolInfo, HealthResult, InvokeResponse 等）
│   └── static/         # Vite 构建产物（由 frontend/ 编译生成）
└── mcp/
    └── server.py       # MCP server：27 个 tool 定义，调用 service 层

frontend/               # Dashboard 前端源码（React + shadcn/ui + Tailwind）
├── src/
│   ├── App.tsx         # 主布局：Header + Tabs（健康监控 / 工具调用）
│   ├── pages/
│   │   ├── HealthCheck.tsx  # 总览卡片 + Provider 概览 + 状态矩阵 + 异常记录
│   │   └── ToolInvoke.tsx   # 工具列表 + 参数输入 + 多 Provider 对比调用
│   └── lib/api.ts      # API 客户端（fetch + SSE）
└── vite.config.ts      # 构建输出到 src/finance_data/dashboard/static/
```

关键路径：`mcp/server.py` → `service/<domain>.py` → `provider/<src>/<domain>/`

## 新增接口流程

> 使用 `.claude/skills/add-new-interface.md` Skill 获得完整步骤指导。

1. 在 `src/finance_data/provider/<domain>/` 下新建或修改 akshare.py / tushare.py
2. 在 `tests/provider/<domain>/` 下添加对应测试
3. 在 `src/finance_data/mcp/server.py` 添加 MCP tool（含规范 docstring）
4. 在 `src/finance_data/provider/metadata/registry.py` 注册 ToolMeta
5. 运行校验：`python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
6. 更新 CLAUDE.md 接口列表

## 当前接口（27 个）

| Tool | 领域 | 说明 |
|------|------|------|
| `tool_get_stock_info_history` | stock | 个股基本信息，akshare 优先，fallback tushare+xueqiu |
| `tool_get_kline_history` | kline | K线历史数据（daily/weekly/monthly/分钟级），akshare+tushare+xueqiu |
| `tool_get_realtime_quote` | realtime | 实时行情（含 20 分钟缓存），akshare+tushare+xueqiu |
| `tool_get_index_quote_realtime` | index | 大盘指数实时行情，akshare+tushare+xueqiu |
| `tool_get_index_history` | index | 大盘指数历史 K线，akshare+tushare+xueqiu |
| `tool_get_sector_rank_realtime` | sector | 行业板块涨跌排名，仅 akshare |
| `tool_get_chip_distribution_history` | chip | 个股筹码分布（获利比例、成本、集中度），仅 akshare |
| `tool_get_financial_summary_history` | fundamental | 财务摘要（营收、净利润、ROE、毛利率），akshare+tushare+xueqiu |
| `tool_get_dividend_history` | fundamental | 历史分红记录，akshare+tushare+xueqiu |
| `tool_get_earnings_forecast_history` | fundamental | 业绩预告，akshare 优先 |
| `tool_get_stock_capital_flow_realtime` | cashflow | 个股资金流向（主力净流入），akshare+xueqiu |
| `tool_get_trade_calendar_history` | calendar | 交易日历（is_open 标记），仅 tushare |
| `tool_get_market_stats_realtime` | market | 市场涨跌统计（盘中实时，涨/跌/平家数），仅 akshare |
| `tool_get_lhb_detail` | lhb | 龙虎榜每日上榜详情（按日期范围），akshare 优先+tushare |
| `tool_get_lhb_stock_stat` | lhb | 个股上榜统计（近一月/三月/六月/一年），仅 akshare |
| `tool_get_lhb_active_traders` | lhb | 每日活跃游资营业部（席位追踪），仅 akshare |
| `tool_get_lhb_trader_stat` | lhb | 营业部统计-游资战绩排行（近一月等），仅 akshare |
| `tool_get_lhb_stock_detail` | lhb | 个股某日龙虎榜席位明细（买入/卖出），仅 akshare |
| `tool_get_zt_pool` | pool | 涨停股池（首板/连板检测），仅 akshare |
| `tool_get_strong_stocks` | pool | 强势股池（60日新高/量比放大），仅 akshare |
| `tool_get_previous_zt` | pool | 昨日涨停今日数据（低吸检测），仅 akshare |
| `tool_get_zbgc_pool` | pool | 炸板股池（冲板后开板，低吸补充），仅 akshare |
| `tool_get_market_north_capital` | north_flow | 北向资金日频资金流（沪股通+深股通），仅 akshare |
| `tool_get_north_stock_hold` | north_flow | 北向资金持股明细（akshare 排行/tushare 个股），akshare 优先 |
| `tool_get_margin` | margin | 融资融券汇总（按交易所），tushare 优先（支持日期范围） |
| `tool_get_margin_detail` | margin | 融资融券个股明细，tushare 优先（支持日期范围+个股） |
| `tool_get_sector_capital_flow` | sector_fund_flow | 板块资金流排名（行业/概念/地域/沪股通/深股通），仅 akshare |

## Provider 优先级

`akshare`（无需 token）→ `tushare`（需 `TUSHARE_TOKEN`）→ `xueqiu`（海外可达，8 个接口；实时行情/个股信息/资金流向/财务摘要/分红无需认证，K线需登录 cookie — 自动从浏览器提取或手动设置 `XUEQIU_COOKIE`）

Service 层在模块加载时根据 token/cookie 可用性动态构建 provider 链（见 `service/<domain>.py` 的 `_build_*()` 函数）。
