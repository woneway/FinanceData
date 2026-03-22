# FinanceData 全量接口接入设计

**日期：** 2026-03-22
**状态：** 已批准，待实现

---

## 背景

FinanceData 目前只实现了 `tool_get_stock_info`（股票基本信息）。
`daily_stock_analysis` 项目使用了 52+ 个数据接口，覆盖 10 个数据领域。
本次目标：将所有接口全量接入 FinanceData，遵循统一规范，支持 akshare + tushare 双源。

---

## 核心原则

1. **统一出参 schema**：每个领域定义专属 dataclass，不同 provider 返回相同字段集合
2. **单 MCP tool**：同一领域只暴露一个 tool，内部按 akshare → tushare 顺序 fallback
3. **原子提交**：每个接口独立 migrate → verify → commit，始终保持 main 可用
4. **graceful degradation**：次要数据源失败不阻断主流程

---

## 架构：Domain-First 目录结构

```
src/finance_data/
  provider/
    base.py                    # StockProvider Protocol（不变）
    types.py                   # DataResult, DataFetchError（不变）

    stock/                     # 股票基本信息（从 akshare/、tushare/ 迁移）
      models.py                # StockInfo（23字段，现有）
      akshare.py               # ← 原 provider/akshare/stock.py
      tushare.py               # ← 原 provider/tushare/stock.py

    kline/                     # K线历史
      models.py                # KlineBar
      akshare.py
      tushare.py

    realtime/                  # 实时行情（含 TTL 缓存）
      models.py                # RealtimeQuote
      cache.py                 # TTLCache(maxsize=512, ttl=1200)
      akshare.py
      tushare.py

    index/                     # 大盘指数
      models.py                # IndexQuote, IndexBar
      akshare.py
      tushare.py

    sector/                    # 行业板块排名
      models.py                # SectorRank
      akshare.py
      tushare.py

    chip/                      # 筹码分布（仅 akshare）
      models.py                # ChipDistribution
      akshare.py

    fundamental/               # 财务基本面
      models.py                # FinancialSummary, DividendRecord, EarningsForecast
      akshare.py
      tushare.py

    cashflow/                  # 资金流向
      models.py                # FundFlow
      akshare.py
      tushare.py

    calendar/                  # 交易日历（仅 tushare）
      models.py                # TradeDate
      tushare.py

    market/                    # 市场统计
      models.py                # MarketStats
      akshare.py
      tushare.py

  mcp/
    server.py                  # 所有 MCP tools
```

---

## 数据模型

### kline/models.py
```python
@dataclass
class KlineBar:
    symbol: str
    date: str           # YYYYMMDD
    period: str         # daily/weekly/monthly/1min/5min/15min/30min/60min
    open: float
    high: float
    low: float
    close: float
    volume: float       # 手
    amount: float       # 元
    pct_chg: float      # 涨跌幅 %
    adj: str            # qfq/hfq/none
```

### realtime/models.py
```python
@dataclass
class RealtimeQuote:
    symbol: str
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    market_cap: Optional[float]
    pe: Optional[float]
    pb: Optional[float]
    turnover_rate: Optional[float]
    timestamp: str      # ISO 8601
```

### index/models.py
```python
@dataclass
class IndexQuote:
    symbol: str         # 000001.SH
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    timestamp: str

@dataclass
class IndexBar:
    symbol: str
    date: str
    open: float; high: float; low: float; close: float
    volume: float; amount: float; pct_chg: float
```

### sector/models.py
```python
@dataclass
class SectorRank:
    name: str
    pct_chg: float
    leader_stock: str
    leader_pct_chg: float
    up_count: Optional[int]
    down_count: Optional[int]
```

### chip/models.py
```python
@dataclass
class ChipDistribution:
    symbol: str
    date: str
    avg_cost: float
    concentration: float    # 筹码集中度 %
    profit_ratio: float     # 获利比例 %
    cost_90: float          # 90% 筹码成本区间上沿
    cost_10: float          # 下沿
```

### fundamental/models.py
```python
@dataclass
class FinancialSummary:
    symbol: str
    period: str             # YYYYMMDD（报告期）
    revenue: Optional[float]
    net_profit: Optional[float]
    roe: Optional[float]
    gross_margin: Optional[float]
    cash_flow: Optional[float]

@dataclass
class DividendRecord:
    symbol: str
    ex_date: str
    per_share: float
    record_date: str

@dataclass
class EarningsForecast:
    symbol: str
    period: str
    forecast_type: str      # 预增/预减/扭亏/首亏/续盈/续亏/略增/略减
    change_low: Optional[float]
    change_high: Optional[float]
    summary: str
```

### cashflow/models.py
```python
@dataclass
class FundFlow:
    symbol: str
    date: str
    net_inflow: float       # 净流入（元）
    net_inflow_pct: float   # 净流入占比 %
    main_inflow: float      # 主力净流入
    main_inflow_pct: float
```

### calendar/models.py
```python
@dataclass
class TradeDate:
    date: str       # YYYYMMDD
    is_open: bool
```

### market/models.py
```python
@dataclass
class MarketStats:
    date: str
    total_count: int
    up_count: int
    down_count: int
    flat_count: int
    total_amount: Optional[float]   # 总成交额（元）
```

---

## 实现规范

### Provider 函数签名
```python
# 每个 domain/akshare.py 和 domain/tushare.py 导出
def get_xxx(symbol: str, **kwargs) -> DataResult: ...
```

### MCP Tool 模式
```python
@mcp.tool()
async def tool_get_xxx(symbol: str, ...) -> str:
    providers = [("akshare", akshare.get_xxx), ("tushare", tushare.get_xxx)]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol, ...))
        except Exception as e:
            logger.warning(f"{name} 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

### 缓存（仅 realtime 领域）
```python
# realtime/cache.py
from cachetools import TTLCache
_quote_cache: TTLCache = TTLCache(maxsize=512, ttl=1200)
```

---

## K线粒度支持

| period 参数 | akshare 接口 | tushare 接口 |
|------------|-------------|-------------|
| `daily` | `stock_zh_a_hist(period="daily")` | `pro.daily()` |
| `weekly` | `stock_zh_a_hist(period="weekly")` | `pro.weekly()` |
| `monthly` | `stock_zh_a_hist(period="monthly")` | `pro.monthly()` |
| `1min` | `stock_zh_a_hist_min_em(period="1")` | `pro.stk_mins(freq="1min")` |
| `5min` | `stock_zh_a_hist_min_em(period="5")` | `pro.stk_mins(freq="5min")` |
| `15min` | `stock_zh_a_hist_min_em(period="15")` | `pro.stk_mins(freq="15min")` |
| `30min` | `stock_zh_a_hist_min_em(period="30")` | `pro.stk_mins(freq="30min")` |
| `60min` | `stock_zh_a_hist_min_em(period="60")` | `pro.stk_mins(freq="60min")` |

---

## 实现优先级与提交规范

| 顺序 | 领域 | commit 格式 |
|------|-----|------------|
| 1 | stock（路径迁移） | `refactor(stock): 迁移至 domain-first 目录结构` |
| 2 | kline | `feat(kline): 接入 K线历史接口 (akshare+tushare)` |
| 3 | realtime | `feat(realtime): 接入实时行情接口，含 TTL 缓存` |
| 4 | index | `feat(index): 接入大盘指数接口` |
| 5 | sector | `feat(sector): 接入行业板块排名接口` |
| 6 | chip | `feat(chip): 接入筹码分布接口 (akshare)` |
| 7 | fundamental | `feat(fundamental): 接入财务基本面接口` |
| 8 | cashflow | `feat(cashflow): 接入资金流向接口` |
| 9 | calendar | `feat(calendar): 接入交易日历接口 (tushare)` |
| 10 | market | `feat(market): 接入市场统计接口` |

每个领域的实现循环：
1. **迁移**：实现 domain/models.py + akshare.py + tushare.py + 更新 server.py
2. **验证**：`.venv/bin/pytest tests/ -v` 全部通过
3. **提交**：git commit

---

## 测试要求

每个 provider 实现需覆盖：
- 正常返回：DataResult 结构 + 所有 model 字段校验
- 空结果：DataFetchError(kind="data")
- 网络错误：DataFetchError(kind="network")
- 鉴权错误：DataFetchError(kind="auth")
- 领域特有场景（如 realtime 缓存命中、kline 各 period、chip 仅 akshare 单源）

---

## 不在本次范围内

- REST API / HTTP 服务层
- 港股、美股的完整支持（本次聚焦 A 股）
- 外部缓存（Redis）
- CI/CD 流水线
