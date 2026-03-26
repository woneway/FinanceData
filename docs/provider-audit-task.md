# Provider 实现审计任务书

## 目标

对数据流经的三层（MCP → Service → Provider）进行全链路审计，验证**正确性**与**一致性**，产出结构化报告。

---

## 术语定义

### 一、Provider 正确性（C1-C8，单个 Provider）

每个 provider 实现必须满足以下 8 项检查：

| # | 维度 | 通过标准 | 检查方法 |
|---|------|---------|---------|
| C1 | 协议签名匹配 | 方法名、参数名、参数类型、返回类型与 `interface/<domain>/*.py` 中 Protocol 完全一致 | 对比 Protocol 定义与 provider 类方法签名 |
| C2 | 字段映射正确 | 从原始 API 返回的 DataFrame/JSON 到 dataclass 的每个字段映射无误：无拼写错误、无取错列名、类型转换完整 | 逐字段对照 dataclass 定义与 provider 代码中的赋值逻辑 |
| C3 | Symbol 格式转换 | 输入 `000001` 正确转为各源格式（akshare 视接口而定、tushare→`000001.SZ`、xueqiu→`SZ000001`），输出 `symbol` 字段统一为纯数字 `000001` | 检查 symbol 转换代码 |
| C4 | 错误处理规范 | 网络异常→`kind="network"`、数据异常→`kind="data"`、认证失败→`kind="auth"`、配额超限→`kind="quota"`；无裸 `except`；`from e` 保留调用链 | 检查 try/except 块 |
| C5 | 边界条件处理 | 空 DataFrame 不抛异常（返回空 `data=[]` 或合理错误）；Optional 字段缺失时为 `None` 不是 `NaN`；非交易日查询有合理行为 | 检查空值处理逻辑 |
| C6 | DataResult 规范 | `data` 为 `List[Dict]`（通过 `to_dict()`）；`source` 为 `"akshare"/"tushare"/"xueqiu"`；`meta` 含必要上下文 | 检查 return 语句 |
| C7 | 无副作用 | 不修改全局状态；akshare `_no_proxy()` 正确恢复环境变量；xueqiu session 单例安全；无资源泄漏 | 检查上下文管理器和全局变量操作 |
| C8 | to_dict() 键名一致 | dataclass 字段名与 `to_dict()` 输出的 dict key 一一对应，不存在重命名（如字段叫 `profit_ratio` 但 key 输出 `cost_profit_ratio`） | 对比 dataclass 字段定义与 to_dict() 返回的 key |

> **C8 说明**: 这是 interface 层自身的正确性检查。`to_dict()` 是 Provider 到 MCP 的数据出口，key 名不一致会导致消费方读不到数据。**已知问题**: `interface/chip/history.py:25` 字段 `profit_ratio` 输出为 key `cost_profit_ratio`。

### 二、跨 Provider 一致性（S1-S6，多 Provider 同接口对比）

同一接口有多个 provider 时，必须满足以下 6 项检查：

| # | 维度 | 通过标准 | 检查方法 |
|---|------|---------|---------|
| S1 | 输出字段覆盖 | 同一 dataclass 的字段，各 provider 都填充（允许 Optional 字段为 None，但须标注为"设计差异"或"bug"） | 对比各 provider 构造 dataclass 时填了哪些字段 |
| S2 | 字段语义一致 | 同名字段含义相同：`pct_chg` 统一为百分比值（如 5.23 代表 5.23%）或统一为小数（0.0523）；`volume` 统一为"股"或"手" | 追溯各 provider 原始 API 文档或代码注释 |
| S3 | 数值精度 | 价格小数位数一致；百分比表示方式一致；金额单位一致（元 vs 万元） | 对比各 provider 的数值处理代码 |
| S4 | 日期格式 | 输出中日期字段统一格式（`YYYYMMDD` 或 `YYYY-MM-DD`，二选一）；输入参数的日期格式要求一致 | 检查日期处理代码 |
| S5 | 排序与范围 | 同样参数返回数据的排序方向一致（升序/降序）；日期范围边界一致（含头含尾 vs 含头不含尾） | 检查排序代码和日期过滤逻辑 |
| S6 | 默认行为 | 缺省参数的默认行为一致（如不传 start_date 时各 provider 返回的数据范围接近） | 检查默认值处理 |

> **S1 补充**: 对于一致性检查结果，需区分**设计差异**（intentional，如 tushare 不支持某字段）和**bug**（应填但漏填）。报告模板中增加"设计差异"栏记录。

### 三、Service 层正确性（SC1-SC3）

`src/finance_data/service/*.py` 中的 Dispatcher 需额外检查：

| # | 维度 | 通过标准 | 检查方法 |
|---|------|---------|---------|
| SC1 | Provider 注册完整 | 所有可用的 provider 实现都被注册到 dispatcher 中，无遗漏 | 对比 `provider/` 目录下的实现文件与 `service/*.py` 中 `_build_*()` 的 import |
| SC2 | 优先级正确 | Dispatcher 中 provider 的顺序与 CLAUDE.md 文档描述一致 | 对比 `_build_*()` 中 `providers.append()` 顺序与 CLAUDE.md |
| SC3 | Dispatcher 签名匹配 | Dispatcher 的方法签名与 Protocol 一致，参数透传无遗漏 | 对比 Dispatcher 方法签名与 Protocol 定义 |

### 四、MCP 层正确性（MC1-MC4）

`src/finance_data/mcp/server.py` 需额外检查：

| # | 维度 | 通过标准 | 检查方法 |
|---|------|---------|---------|
| MC1 | 错误处理一致 | 所有 MCP tool 函数都有统一的 try/except 包装（或统一不包装），不能部分有部分没有 | 检查每个 `@mcp.tool()` 函数是否有 try/except |
| MC2 | 参数默认值合理 | 默认值不能是硬编码的过期日期或易误用的值 | 检查所有 `@mcp.tool()` 的参数默认值 |
| MC3 | 参数透传正确 | MCP tool 的参数名、顺序与 service 层方法调用完全匹配 | 对比 MCP tool 签名与 service 调用语句 |
| MC4 | 命名一致 | MCP tool 函数名与 CLAUDE.md 接口列表、metadata registry 三处一致 | 交叉比对三处名称 |

> **已知问题**:
> - MC1: `tool_get_kline_history`（:85）和 `tool_get_realtime_quote`（:105）没有 try/except，其他大多数有
> - MC2: `tool_get_kline_history` 默认 `end="20241231"` 硬编码过期日期
> - MC4: MCP 函数名 `tool_get_market_north_capital`（:659）vs CLAUDE.md 写的 `tool_get_north_flow`

---

## 审计范围

### 多 Provider 接口（13 个，审计 C1-C8 + S1-S6 + SC1-SC3 + MC1-MC4）

| # | 接口 | Protocol | akshare | tushare | xueqiu | 优先级 |
|---|------|----------|---------|---------|--------|--------|
| 1 | stock_info | `StockHistoryProtocol.get_stock_info_history(symbol)` | ✓ | ✓ | - | ak→ts |
| 2 | kline | `KlineHistoryProtocol.get_kline_history(symbol, period, start, end, adj)` | ✓ | ✓ | ✓ | ak→ts→xq |
| 3 | realtime_quote | `RealtimeQuoteProtocol.get_realtime_quote(symbol)` | ✓ | ✓ | ✓ | ak→ts→xq |
| 4 | index_quote | `IndexQuoteProtocol.get_index_quote_realtime(symbol)` | ✓ | ✓ | ✓ | ak→ts→xq |
| 5 | index_history | `IndexHistoryProtocol.get_index_history(symbol, start, end)` | ✓ | ✓ | ✓ | ak→ts→xq |
| 6 | financial_summary | `FinancialSummaryProtocol.get_financial_summary_history(symbol)` | ✓ | ✓ | - | ak→ts |
| 7 | dividend | `DividendProtocol.get_dividend_history(symbol)` | ✓ | ✓ | - | ak→ts |
| 8 | chip_distribution | `ChipHistoryProtocol.get_chip_distribution_history(symbol)` | ✓ | ✓ | - | ak→ts |
| 9 | lhb_detail | `LhbDetailProtocol.get_lhb_detail_history(start_date, end_date)` | ✓ | ✓ | - | ak→ts |
| 10 | north_stock_hold | `NorthStockHoldProtocol.get_north_stock_hold_history(market, indicator, symbol, trade_date)` | ✓ | ✓ | - | ak→ts |
| 11 | margin | `MarginProtocol.get_margin_history(trade_date, start_date, end_date, exchange_id)` | ✓ | ✓ | - | ts→ak |
| 12 | margin_detail | `MarginDetailProtocol.get_margin_detail_history(trade_date, start_date, end_date, ts_code)` | ✓ | ✓ | - | ts→ak |
| 13 | trade_calendar | `TradeCalendarProtocol.get_trade_calendar_history(start, end)` | ✓ | ✓ | - | ts→ak |

### 单 Provider 接口（14 个，审计 C1-C8 + MC1-MC4）

| # | 接口 | Protocol | Provider |
|---|------|----------|----------|
| 14 | sector_rank | `SectorRankProtocol.get_sector_rank_realtime()` | akshare |
| 15 | earnings_forecast | `EarningsForecastProtocol.get_earnings_forecast_history(symbol)` | akshare |
| 16 | fund_flow | `StockCapitalFlowProtocol.get_stock_capital_flow_realtime(symbol)` | akshare |
| 17 | market_stats | `MarketRealtimeProtocol.get_market_stats_realtime()` | akshare |
| 18 | north_flow | `NorthFlowProtocol.get_north_flow_history()` | akshare |
| 19 | lhb_stock_stat | `LhbStockStatProtocol.get_lhb_stock_stat_history(period)` | akshare |
| 20 | lhb_active_traders | `LhbActiveTradersProtocol.get_lhb_active_traders_history(start_date, end_date)` | akshare |
| 21 | lhb_trader_stat | `LhbTraderStatProtocol.get_lhb_trader_stat_history(period)` | akshare |
| 22 | lhb_stock_detail | `LhbStockDetailProtocol.get_lhb_stock_detail_history(symbol, date, flag)` | akshare |
| 23 | zt_pool | `ZtPoolProtocol.get_zt_pool_history(date)` | akshare |
| 24 | strong_stocks | `StrongStocksProtocol.get_strong_stocks_history(date)` | akshare |
| 25 | previous_zt | `PreviousZtProtocol.get_previous_zt_history(date)` | akshare |
| 26 | zbgc_pool | `ZbgcPoolProtocol.get_zbgc_pool_history(date)` | akshare |
| 27 | sector_fund_flow | `SectorCapitalFlowProtocol.get_sector_capital_flow_history(indicator, sector_type)` | akshare |

---

## 执行流程

按 **domain 分组** 推进（同一 domain 共享 provider 文件，一次性审计效率更高）。每完成一个 domain 立即更新报告文档 `docs/provider-audit-report.md`。

### 分组顺序（多 Provider domain 优先）

| 批次 | Domain | 包含接口 | 文件数 |
|------|--------|---------|--------|
| 1 | kline | #2 kline | ak+ts+xq 各1 |
| 2 | realtime | #3 realtime_quote | ak+ts+xq 各1 |
| 3 | index | #4 index_quote + #5 index_history | ak+ts+xq 各2 |
| 4 | stock | #1 stock_info | ak+ts 各1 |
| 5 | fundamental | #6 financial_summary + #7 dividend + #15 earnings_forecast | ak+ts 各1（共享文件） |
| 6 | chip | #8 chip_distribution | ak+ts 各1 |
| 7 | lhb | #9 lhb_detail + #19-#22 | ak+ts 各1（共享文件） |
| 8 | north_flow | #10 north_stock_hold + #18 north_flow | ak+ts 各1 |
| 9 | margin | #11 margin + #12 margin_detail | ak+ts 各1（共享文件） |
| 10 | calendar | #13 trade_calendar | ts+ak 各1 |
| 11 | 单 Provider | #14 sector_rank, #16 fund_flow, #17 market_stats, #23-#27 pool 系列 | 各1 |

### 每个 Domain 的审计步骤

**Step 1: 读取标准定义**
- 读 `interface/<domain>/*.py` 中的 Protocol 签名和 dataclass 字段定义
- 检查 C8：`to_dict()` 输出 key 是否与 dataclass 字段名一一对应
- 记录：方法签名、dataclass 全部字段（名称+类型+是否 Optional）

**Step 2: 逐 Provider 检查正确性（C1-C7）**
- 读 `provider/akshare/<domain>/*.py`
- 读 `provider/tushare/<domain>/*.py`（如有）
- 读 `provider/xueqiu/<domain>/*.py`（如有）
- 逐项对照 C1-C7 检查清单

**Step 3: 检查 Service 层（SC1-SC3）**
- 读 `service/<domain>.py`
- 检查 provider 注册完整性、优先级顺序、签名匹配

**Step 4: 检查 MCP 层（MC1-MC4）**
- 读 `mcp/server.py` 中对应的 tool 函数
- 检查错误处理一致性、参数默认值、参数透传、命名一致

**Step 5: 跨 Provider 检查一致性（S1-S6）**
- 仅多 Provider 接口需要此步骤
- 横向对比各 provider 对同一 dataclass 字段的填充方式
- 区分"设计差异"和"bug"

**Step 6: 更新报告**
- 将该 domain 所有接口的审计结果**追加**到 `docs/provider-audit-report.md`

---

## 报告模板

每个接口的报告格式：

```markdown
## {序号}. {接口名}

**Protocol**: `{Protocol类名}.{方法名}({参数})`
**Dataclass**: `{Dataclass类名}` ({字段数} fields)
**Providers**: akshare ✓ / tushare ✓ / xueqiu ✓

### Interface 层（C8）

| 检查项 | 结论 | 详情 |
|--------|------|------|
| to_dict() key 一致性 | ✅/❌ | {具体差异} |

### Provider 正确性（C1-C7）

| 维度 | akshare | tushare | xueqiu |
|------|---------|---------|--------|
| C1 协议签名 | ✅ | ✅ | - |
| C2 字段映射 | ✅ | ⚠️ `xxx` 字段未填充 | - |
| C3 Symbol转换 | ✅ | ✅ | - |
| C4 错误处理 | ✅ | ❌ 裸except | - |
| C5 边界条件 | ⚠️ 空DF未处理 | ✅ | - |
| C6 DataResult | ✅ | ✅ | - |
| C7 无副作用 | ✅ | ✅ | - |

### Service 层（SC1-SC3）

| 维度 | 结论 | 详情 |
|------|------|------|
| SC1 Provider 注册完整 | ✅/❌ | {file:line} |
| SC2 优先级正确 | ✅/❌ | 实际={}, CLAUDE.md={} |
| SC3 签名匹配 | ✅/❌ | {差异说明} |

### MCP 层（MC1-MC4）

| 维度 | 结论 | 详情 |
|------|------|------|
| MC1 错误处理 | ✅/❌ | 有/无 try/except |
| MC2 参数默认值 | ✅/⚠️ | {问题说明} |
| MC3 参数透传 | ✅/❌ | {差异说明} |
| MC4 命名一致 | ✅/❌ | MCP={}, CLAUDE.md={}, registry={} |

### 一致性（仅多 Provider）

| 维度 | 结论 | 详情 |
|------|------|------|
| S1 字段覆盖 | ⚠️ | tushare 缺少 `xxx` 字段 |
| S2 字段语义 | ✅ | pct_chg 均为百分比值 |
| S3 数值精度 | ✅ | 价格均保留2位小数 |
| S4 日期格式 | ❌ | akshare=YYYY-MM-DD, tushare=YYYYMMDD |
| S5 排序方向 | ✅ | 均按日期升序 |
| S6 默认行为 | ⚠️ | akshare 默认近30天, tushare 默认近1年 |

### 设计差异（非 bug，已知的 Provider 能力差异）

- {说明，如：tushare 不提供 xxx 字段，属于数据源本身不支持}

### 问题清单

- [ ] **P0**: {阻塞性问题，必须修复} — `{file:line}`
- [ ] **P1**: {功能问题，应该修复} — `{file:line}`
- [ ] **P2**: {建议改进} — `{file:line}`
```

---

## 报告文档最终结构

`docs/provider-audit-report.md`：

```
# Provider 实现审计报告

> 生成时间: {date}
> 审计范围: 27 个接口 / 3 个 Provider / 4 层检查

## 总览

| 层 | 检查项 | ✅ 通过 | ⚠️ 警告 | ❌ 问题 |
|----|--------|--------|---------|--------|
| Interface (C8) | 27 | X | X | X |
| Provider (C1-C7) | 27×providers | X | X | X |
| Service (SC1-SC3) | 27 | X | X | X |
| MCP (MC1-MC4) | 27 | X | X | X |
| 一致性 (S1-S6) | 13 | X | X | X |

## 问题汇总（按优先级）

### P0 - 阻塞性
- [ ] ...

### P1 - 需修复
- [ ] ...

### P2 - 建议改进
- [ ] ...

---

## 1. stock_info
{审计结果}

## 2. kline
{审计结果}

...（共 27 个接口）
```

---

## 约束

1. **逐 domain 推进**：同一 domain 下的接口一次性审计（共享 provider 文件），完成后立即更新报告
2. **只读代码，不改代码**：本任务仅做审计分析，不修改任何源文件
3. **证据驱动**：每个判断必须引用具体文件路径和行号（如 `provider/akshare/kline/history.py:42`）
4. **区分 bug 与设计差异**：一致性检查中明确标注哪些是"设计差异"（数据源能力限制）、哪些是"bug"（应修但未修）
5. **多 Provider domain 优先**：按分组顺序表执行（批次 1-10 → 批次 11）
