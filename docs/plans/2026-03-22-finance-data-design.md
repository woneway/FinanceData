# FinanceData 设计文档

**日期**: 2026-03-22
**状态**: 已确认
**替换**: mcp_akshare

---

## 背景

mcp_akshare 基于文档解析动态注册 akshare 函数，存在文档漂移、参数验证弱、搜索质量差等问题。
FinanceData 采用手工精选接口、强类型 Pydantic schema 的方式重新实现，同时接入 tushare 数据源。

---

## 目标

- 替换 mcp_akshare，提供更可靠的金融数据服务
- 支持 akshare + tushare 双数据源
- 同时支持 MCP（AI Agent）和 Python library 两种接入方式
- 接口精选，增量扩展

---

## 项目结构

```
FinanceData/
  src/
    finance_data/
      provider/
        akshare/
          stock.py          # 股票基础信息、列表
          kline.py          # 日K、分钟线
          market.py         # 实时行情、指数
          sentiment.py      # 涨停池、龙虎榜、资金流、热度
        tushare/
          financials.py     # 利润表、资产负债表、财务指标
          events.py         # 公告
        kline.py            # 路由层（K线双源选择）
        types.py            # 共享类型：DataResult, DataFetchError
      mcp/
        server.py           # MCP tools，薄封装
  tests/
    provider/
      test_stock.py
      test_kline.py
      test_financials.py
  docs/
    plans/
  mcp_server.py             # MCP 启动入口
  pyproject.toml
```

---

## 架构分层

```
┌─────────────────────────────┐
│      MCP / Python import    │  ← 接入层
├─────────────────────────────┤
│      provider/types.py      │  ← 统一输出契约
├──────────────┬──────────────┤
│   akshare/   │   tushare/   │  ← 数据源实现层
└──────────────┴──────────────┘
```

**原则：**
- `provider/akshare/` 和 `provider/tushare/` 各自只感知自己的数据源
- `server.py` 不含任何业务逻辑，只做 MCP 协议适配
- provider 层可直接作为 Python library 使用，不依赖 MCP

---

## 接入方式

### MCP（AI Agent）

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "python3",
      "args": ["/path/to/FinanceData/mcp_server.py"]
    }
  }
}
```

### Python Library

```python
from finance_data.provider.akshare.stock import get_stock_info
info = get_stock_info("000001")
```

---

## 类型契约

```python
# provider/types.py

@dataclass
class DataResult:
    data: List[Dict]
    source: str            # "akshare" | "tushare"
    meta: Dict             # 行数、时间戳、是否截断等

class DataFetchError(Exception):
    def __init__(self, source: str, func: str, reason: str, kind: str):
        # kind: "network" | "data" | "auth" | "quota"
        ...
```

所有 provider 函数返回 `DataResult`，统一结构。

---

## Pydantic Schema 规范

每个接口定义 Input + Output schema，Field 必须包含 `description` 和 `example`：

```python
class StockInfoInput(BaseModel):
    symbol: str = Field(description="股票代码", example="000001")

class StockInfoOutput(BaseModel):
    name: str = Field(description="股票名称")
    industry: str = Field(description="所属行业")
    ...
```

`example` 字段是给 AI 调用时的关键提示，必填。

---

## 数据源配置

| 数据源 | 认证方式 | 说明 |
|--------|----------|------|
| akshare | 无需认证 | 免费，无频率限制 |
| tushare | 环境变量 `TUSHARE_TOKEN` | 有 Points 积分限制 |

tushare 在模块初始化时读取 token，缺失时抛出明确错误。

---

## Fallover 策略（K线双源）

| 错误类型 | 处理 |
|----------|------|
| 网络超时/连接失败 | 切到备用源，写 warning 日志 |
| 数据不存在 | 直接抛出，不 fallover |
| 参数错误 | 直接抛出，不 fallover |

结果的 `source` 字段始终标明实际使用的数据源。

K线优先级：akshare → tushare（akshare 免费无限制）

---

## 接口清单（增量扩展）

### 首期（验证架构）

| Tool | 数据源 | 参数 |
|------|--------|------|
| `get_stock_info` | akshare | symbol |

### 后续扩展

**行情类**

| Tool | 数据源 | 参数 |
|------|--------|------|
| `get_daily_kline` | akshare→tushare | symbol, start_date, end_date, adjust |
| `get_minute_kline` | akshare | symbol, period, start_date, end_date |
| `get_realtime_quote` | akshare | symbol |
| `get_index_daily` | akshare | symbol, start_date, end_date |

**标的信息**

| Tool | 数据源 | 参数 |
|------|--------|------|
| `get_stock_list` | akshare | 无 |

**市场情绪**

| Tool | 数据源 | 参数 |
|------|--------|------|
| `get_zt_pool` | akshare | date |
| `get_lhb_detail` | akshare | start_date, end_date |
| `get_fund_flow_rank` | akshare | period |
| `get_hot_rank` | akshare | 无 |

**基本面**

| Tool | 数据源 | 参数 |
|------|--------|------|
| `get_daily_basic` | tushare | symbol, start_date, end_date |
| `get_income_statement` | tushare | symbol, period |
| `get_balance_sheet` | tushare | symbol, period |
| `get_financial_indicator` | tushare | symbol, period |
| `get_announcements` | tushare | symbol, start_date, end_date |

---

## 测试策略

- provider 函数独立可测，不依赖 MCP
- 用 `pytest` + `unittest.mock` mock 数据源调用
- 首期验证 `get_stock_info` 的完整链路

---

## 不做的事

- 不做缓存（业务层按需加）
- 不做 REST API（MCP + Python library 已足够）
- 不做动态函数发现（精选接口，增量扩展）
