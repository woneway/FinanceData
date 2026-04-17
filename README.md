# FinanceData

金融数据服务，支持 **MCP（AI Agent）** 和 **Python library** 两种接入方式。

数据源：[akshare](https://github.com/akfamily/akshare)（免费，无需 token）→ [tushare](https://tushare.pro)（fallback，需 token）

## 快速开始

### 作为 MCP 服务（推荐）

在 Claude Desktop / Claude Code 配置文件中添加：

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "/path/to/FinanceData/.venv/bin/python",
      "args": ["/path/to/FinanceData/mcp_server.py"],
      "env": {
        "TUSHARE_TOKEN": "your_token"
      }
    }
  }
}
```

### 作为 Python 库

```bash
pip install -e .
```

```python
from finance_data.provider.stock import get_stock_info
from finance_data.provider.kline import get_kline
```

## 环境变量

| 变量 | 必须 | 说明 |
|------|------|------|
| `TUSHARE_TOKEN` | 否 | tushare API token，不设置则跳过 tushare fallback |
| `TUSHARE_API_URL` | 否 | 自定义 tushare API 地址（使用第三方代理时设置） |
| `TUSHARE_STOCK_MINUTE_PERMISSION` | 否 | 设置为 `1`/`true`/`yes`/`on` 时，健康检查会启用需要 TuShare 股票分钟权限的接口，例如 `stk_auction_c` |

## 接口列表（22 个）

### 股票基础

| Tool | 说明 |
|------|------|
| `tool_get_stock_info` | 个股基本信息（代码、名称、行业、上市时间等） |
| `tool_get_kline` | K 线历史数据（日/周/月/分钟级，支持复权） |
| `tool_get_realtime_quote` | 实时行情（含 20 分钟缓存） |

### 指数 & 板块

| Tool | 说明 |
|------|------|
| `tool_get_index_quote` | 大盘指数实时行情（上证、深证等） |
| `tool_get_index_history` | 大盘指数历史 K 线 |
| `tool_get_sector_rank` | 行业板块涨跌排名 |

### 基本面

| Tool | 说明 |
|------|------|
| `tool_get_financial_summary` | 财务摘要（营收、净利润、ROE、毛利率） |
| `tool_get_dividend` | 历史分红记录 |
| `tool_get_earnings_forecast` | 业绩预告 |

### 资金 & 筹码

| Tool | 说明 |
|------|------|
| `tool_get_fund_flow` | 个股资金流向（主力净流入等） |
| `tool_get_chip_distribution` | 个股筹码分布（获利比例、平均成本、集中度） |

### 市场统计

| Tool | 说明 |
|------|------|
| `tool_get_market_stats` | 市场涨跌统计（涨/跌/平家数、总成交额） |
| `tool_get_trade_calendar` | 交易日历（is_open 标记） |

### 龙虎榜

| Tool | 说明 |
|------|------|
| `tool_get_lhb_detail` | 每日上榜详情（按日期范围） |
| `tool_get_lhb_stock_stat` | 个股上榜统计（近一月/三月/六月/一年） |
| `tool_get_lhb_active_traders` | 每日活跃游资营业部 |
| `tool_get_lhb_trader_stat` | 营业部战绩排行 |
| `tool_get_lhb_stock_detail` | 个股某日龙虎榜席位明细 |

### 股票池

| Tool | 说明 |
|------|------|
| `tool_get_zt_pool` | 涨停股池（首板/连板检测） |
| `tool_get_strong_stocks` | 强势股池（60 日新高/量比放大） |
| `tool_get_previous_zt` | 昨日涨停今日数据（低吸检测） |
| `tool_get_zbgc_pool` | 炸板股池（冲板后开板，低吸补充） |

## 开发

```bash
# 创建虚拟环境并安装依赖
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# 运行测试
.venv/bin/pytest tests/ -v
```

### 目录结构

```
src/finance_data/
├── provider/          # Domain-first 架构
│   ├── stock/         # 股票基础信息
│   ├── kline/         # K 线数据
│   ├── realtime/      # 实时行情
│   ├── index/         # 指数
│   ├── sector/        # 板块
│   ├── fundamental/   # 基本面
│   ├── cashflow/      # 资金流向
│   ├── chip/          # 筹码分布
│   ├── calendar/      # 交易日历
│   ├── market/        # 市场统计
│   ├── lhb/           # 龙虎榜
│   └── pool/          # 股票池
├── tool_specs/        # ToolSpec 工具契约注册表
└── mcp/
    └── server.py      # MCP 显式 wrapper，执行走 ToolSpec dispatch
```

每个领域目录包含：`models.py` + `akshare.py` + `tushare.py`（按需）

### 新增接口

1. 在 `interface/<domain>/` 定义输入输出契约和 protocol
2. 在 `provider/<source>/<domain>/` 实现数据源适配
3. 在 `service/<domain>.py` 接入业务 dispatcher/fallback
4. 在 `src/finance_data/tool_specs/registry.py` 注册 `ToolSpec`
5. 在 `src/finance_data/mcp/server.py` 增加同名 MCP wrapper，函数体调用统一 ToolSpec dispatch helper
6. 补充 provider、service、ToolSpec、MCP、CLI、Dashboard API 和必要的前端契约测试
7. 运行 `finance-data verify --include-dashboard` 验证注册表、MCP、Dashboard API 和前端契约一致性

交付层约定：

- CLI、MCP、Dashboard API 和前端看板都以 `ToolSpec` 作为工具契约来源
- 默认业务调用最终进入 service，provider 直调仅用于诊断
- 前端看板不得维护独立工具参数表、provider 表或返回字段表
- `FinanceData` Python 客户端保留领域 API，直接调用 service

## License

MIT
