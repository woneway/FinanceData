# Provider 实现审计报告

> 生成时间: 2026-03-25
> 审计范围: 27 个接口 / 3 个 Provider / 4 层检查

## 总览

| 层 | 检查项 | ✅ 通过 | ⚠️ 警告 | ❌ 问题 |
|----|--------|--------|---------|--------|
| Interface (C8) | 27 | - | - | - |
| Provider (C1-C7) | 27×providers | - | - | - |
| Service (SC1-SC3) | 27 | - | - | - |
| MCP (MC1-MC4) | 27 | - | - | - |
| 一致性 (S1-S6) | 13 | - | - | - |

## 问题汇总（按优先级）

### P0 - 阻塞性
_审计完成后汇总_

### P1 - 需修复
_审计完成后汇总_

### P2 - 建议改进
_审计完成后汇总_

---

## 2. kline

**Protocol**: `KlineHistoryProtocol.get_kline_history(symbol: str, period: str, start: str, end: str, adj: str) -> DataResult`
**Dataclass**: `KlineBar` (11 fields: symbol, date, period, open, high, low, close, volume, amount, pct_chg, adj)
**Providers**: akshare ✓ / tushare ✓ / xueqiu ✓

### Interface 层（C8）

| 检查项 | 结论 | 详情 |
|--------|------|------|
| to_dict() key 一致性 | ✅ | 11 个字段名完全一致 |

### Provider 正确性（C1-C7）

| 维度 | akshare | tushare | xueqiu |
|------|---------|---------|--------|
| C1 协议签名 | ✅ | ✅ | ✅ |
| C2 字段映射 | ⚠️ daily volume 由 amount 估算 | ⚠️ volume 单位为"手"未转换 | ✅ |
| C3 Symbol转换 | ✅ `_symbol_to_tx()` 正确 | ✅ `_ts_code()` 正确 | ✅ `_to_xueqiu_symbol()` 正确 |
| C4 错误处理 | ✅ 规范 | ✅ 含 auth 检测 | ✅ 含 cookie 重试 |
| C5 边界条件 | ✅ 空 DF 检查完整 | ✅ 空 DF 检查完整 | ✅ 空 items 检查+None 跳过 |
| C6 DataResult | ✅ | ✅ | ✅ |
| C7 无副作用 | ✅ `_no_proxy()` 正确恢复 | ✅ | ✅ session 单例线程安全 |

**C1 说明**: 三个 provider 均添加了 `adj="qfq"` 默认值，而 Protocol 无默认值。Python 允许此差异（provider 更宽松），不影响通过 Protocol 调用。

**C2 详细说明**:
- **akshare daily** (`history.py:52-57`): 腾讯源不直接提供 volume，使用 `_calc_volume()` 从 amount 和均价估算：`volume = amount * 10000 / avg_price`。这是腾讯源 API 的限制，属于**设计差异**。
- **tushare** (`history.py:56`): `volume=float(row.get("vol", 0))` — tushare `vol` 字段单位为"手"（1手=100股），但代码未乘以100转为"股"。akshare minute 和 xueqiu 的 volume 单位为"股"。这是**bug**。
- **tushare** (`history.py:57`): `amount=float(row.get("amount", 0)) * 1000` — tushare amount 单位为"千元"，正确乘以 1000 转为"元"。

### Service 层（SC1-SC3）

| 维度 | 结论 | 详情 |
|------|------|------|
| SC1 Provider 注册完整 | ✅ | akshare 始终注册；tushare 依赖 `TUSHARE_TOKEN`；xueqiu 依赖 `XUEQIU_COOKIE` — `service/kline.py:27-34` |
| SC2 优先级正确 | ✅ | 实际=ak→ts→xq，CLAUDE.md=akshare+tushare+xueqiu |
| SC3 签名匹配 | ✅ | 参数透传完整 — `service/kline.py:20` |

### MCP 层（MC1-MC4）

| 维度 | 结论 | 详情 |
|------|------|------|
| MC1 错误处理 | ❌ | 无 try/except — `mcp/server.py:61-86`，异常会直接抛出 |
| MC2 参数默认值 | ❌ | `end="20241231"` 硬编码过期日期 — `mcp/server.py:65` |
| MC3 参数透传 | ✅ | `kline_history.get_kline_history(symbol, period=period, start=start, end=end, adj=adj)` — `mcp/server.py:85` |
| MC4 命名一致 | ❌ | MCP=`tool_get_kline_history`，CLAUDE.md=`tool_get_kline`，registry=`tool_get_kline_history` |

### 一致性（S1-S6）

| 维度 | 结论 | 详情 |
|------|------|------|
| S1 字段覆盖 | ✅ | 三个 provider 均填充全部 11 个字段 |
| S2 字段语义 | ❌ | **volume**: tushare 单位为"手"，akshare/xueqiu 为"股"；**pct_chg**: 均为百分比值（如 5.23），一致 |
| S3 数值精度 | ⚠️ | akshare daily `pct_chg` 保留 2 位小数（`history.py:72`），其他 provider 使用原始精度 |
| S4 日期格式 | ✅ | 均为 YYYYMMDD |
| S5 排序方向 | ⚠️ | tushare 默认降序（newest first），akshare/xueqiu 为升序 — tushare `history.py` 无显式排序 |
| S6 默认行为 | ✅ | 所有参数由 service 层统一传入，各 provider 行为一致 |

### 设计差异（非 bug）

- akshare daily（腾讯源）不直接提供 volume，需从 amount 估算 — 数据源 API 限制
- xueqiu 仅支持 daily/weekly/monthly，不支持分钟级 K 线 — 数据源能力差异
- akshare weekly/monthly 无腾讯源替代，当前直接报错 — `history.py:125-127`

### 问题清单

- [ ] **P0**: tushare volume 单位为"手"未转换为"股"，与其他 provider 不一致 — `provider/tushare/kline/history.py:56`
- [ ] **P1**: MCP 层 `tool_get_kline_history` 无 try/except 错误处理 — `mcp/server.py:61-86`
- [ ] **P1**: MCP 默认 `end="20241231"` 硬编码过期日期 — `mcp/server.py:65`
- [ ] **P1**: tushare 返回数据未排序，可能为降序，与 akshare/xueqiu 的升序不一致 — `provider/tushare/kline/history.py:49-59`
- [ ] **P2**: CLAUDE.md 工具名 `tool_get_kline` 与实际 `tool_get_kline_history` 不一致
- [ ] **P2**: akshare daily `pct_chg` 精度与其他 provider 不同（保留 2 位 vs 原始精度）

---

## 3. realtime_quote

**Protocol**: `RealtimeQuoteProtocol.get_realtime_quote(symbol: str) -> DataResult`
**Dataclass**: `RealtimeQuote` (11 fields: symbol, name, price, pct_chg, volume, amount, market_cap, pe, pb, turnover_rate, timestamp)
**Providers**: akshare ✓ / tushare ✓ / xueqiu ✓

### Interface 层（C8）

| 检查项 | 结论 | 详情 |
|--------|------|------|
| to_dict() key 一致性 | ✅ | 11 个字段名完全一致 |

### Provider 正确性（C1-C7）

| 维度 | akshare | tushare | xueqiu |
|------|---------|---------|--------|
| C1 协议签名 | ✅ | ✅ | ✅ |
| C2 字段映射 | ✅ market_cap/pe/pb/turnover_rate=None | ❌ name="" 硬编码; price 为 EOD close | ❌ name 映射了 d["symbol"] 而非 d["name"] |
| C3 Symbol转换 | ✅ | ✅ `_ts_code()` | ✅ `_to_xueqiu_symbol()` |
| C4 错误处理 | ✅ | ✅ 含 auth 检测 | ⚠️ HTTP 401/403 归类为 "network" 而非 "auth" |
| C5 边界条件 | ✅ 空 DF 检查 | ✅ | ✅ `_opt_float` 正确处理 None/NaN |
| C6 DataResult | ✅ | ✅ | ✅ |
| C7 无副作用 | ⚠️ `_no_proxy()` 非线程安全 | ✅ | ✅ session 单例线程安全 |

**C2 详细说明**:
- **tushare** (`provider/tushare/realtime/realtime.py:30,45`): 使用 `pro.daily(limit=1)` 获取最近一条日线数据，`price` 实际是收盘价而非实时价。盘中调用时返回的是**昨日收盘价**，严重语义错误。
- **tushare** (`provider/tushare/realtime/realtime.py:44`): `name=""` 硬编码空字符串。
- **xueqiu** (`provider/xueqiu/realtime/realtime.py:97`): `name=str(data.get("symbol", ""))` 映射了雪球 ticker（如 "SZ000001"）而非股票中文名称，应为 `d.get("name", "")`。

### Service 层（SC1-SC3）

| 维度 | 结论 | 详情 |
|------|------|------|
| SC1 Provider 注册完整 | ✅ | akshare 始终注册；tushare 依赖 TUSHARE_TOKEN；xueqiu 始终注册（无需 auth） — `service/realtime.py:37-45` |
| SC2 优先级正确 | ✅ | 实际=ak→ts→xq，与 CLAUDE.md 一致 |
| SC3 签名匹配 | ✅ | 参数透传正确 |

### MCP 层（MC1-MC4）

| 维度 | 结论 | 详情 |
|------|------|------|
| MC1 错误处理 | ❌ | 无 try/except — `mcp/server.py:89-106` |
| MC2 参数默认值 | ✅ | 仅 `symbol: str`，无默认值 |
| MC3 参数透传 | ✅ | `realtime_quote.get_realtime_quote(symbol)` — `mcp/server.py:105` |
| MC4 命名一致 | ✅ | MCP=registry=CLAUDE.md=`tool_get_realtime_quote` |

### 一致性（S1-S6）

| 维度 | 结论 | 详情 |
|------|------|------|
| S1 字段覆盖 | ⚠️ | akshare: market_cap/pe/pb/turnover_rate=None；tushare: 同+name=""；xueqiu 填充全部字段 |
| S2 字段语义 | ❌ | **price**: tushare 为 EOD close 非实时价；**volume**: tushare 单位"手"，akshare/xueqiu 为"股"；pct_chg 均为百分比值 |
| S3 数值精度 | ✅ | 均使用 float() 无显式舍入 |
| S4 日期格式 | ⚠️ | akshare/tushare 用 `datetime.now().isoformat()` 无时区；xueqiu 用实际市场时间戳含 `+08:00` |
| S5 排序方向 | N/A | 各 provider 仅返回 1 条记录 |
| S6 默认行为 | ✅ | 均在无数据时抛出 DataFetchError |

### 设计差异（非 bug）

- akshare（sina 源）不提供 market_cap、pe、pb、turnover_rate — 数据源 API 限制
- tushare `pro.daily` 不提供 name 字段 — 数据源 API 限制

### 问题清单

- [ ] **P0**: tushare 实时行情使用 `pro.daily(limit=1)` 返回 EOD close 而非实时价格 — `provider/tushare/realtime/realtime.py:30,45`
- [ ] **P1**: xueqiu `name` 字段映射了 `d["symbol"]`（ticker code）而非 `d["name"]`（中文名） — `provider/xueqiu/realtime/realtime.py:97`
- [ ] **P1**: tushare volume 单位"手"未转换为"股" — `provider/tushare/realtime/realtime.py:47`
- [ ] **P1**: MCP 层 `tool_get_realtime_quote` 无 try/except — `mcp/server.py:89-106`
- [ ] **P1**: registry `return_fields` 和 MCP docstring 使用 `pct_change` 但实际 key 为 `pct_chg` — `registry.py:56`, `mcp/server.py:103`
- [ ] **P2**: akshare/tushare timestamp 无时区信息，xueqiu 含 `+08:00` — 跨 provider 不一致
- [ ] **P2**: xueqiu auth 失败（HTTP 401/403）归类为 "network" 而非 "auth"
- [ ] **P2**: registry `api_name="stock_zh_a_spot_em"` 但实际调用 `ak.stock_zh_a_spot()`（sina 源）

---

## 4. index_quote

**Protocol**: `IndexQuoteProtocol.get_index_quote_realtime(symbol: str) -> DataResult`
**Dataclass**: `IndexQuote` (7 fields: symbol, name, price, pct_chg, volume, amount, timestamp)
**Providers**: akshare ✓ / tushare ✓ / xueqiu ✓

### Interface 层（C8）

| 检查项 | 结论 | 详情 |
|--------|------|------|
| to_dict() key 一致性 | ✅ | 7 个字段名完全一致 |

### Provider 正确性（C1-C7）

| 维度 | akshare | tushare | xueqiu |
|------|---------|---------|--------|
| C1 协议签名 | ✅ | ✅ | ✅ |
| C2 字段映射 | ✅ | ⚠️ name="" 硬编码; amount*1000 正确 | ❌ name 映射了 d["symbol"] 而非中文名 |
| C3 Symbol转换 | ⚠️ fallback 逻辑可能误判 | ✅ 直接传入 | ✅ `_INDEX_MAP` + fallback |
| C4 错误处理 | ✅ | ✅ 含 auth 检测 | ✅ |
| C5 边界条件 | ✅ | ✅ | ✅ |
| C6 DataResult | ✅ | ✅ | ✅ |
| C7 无副作用 | ✅ `_no_proxy()` 正确恢复 | ✅ | ✅ |

### Service 层（SC1-SC3）

| 维度 | 结论 | 详情 |
|------|------|------|
| SC1 Provider 注册完整 | ✅ | ak→ts(conditional)→xq(always) — `service/index.py:41-47` |
| SC2 优先级正确 | ✅ | ak→ts→xq |
| SC3 签名匹配 | ✅ | 参数透传正确 |

### MCP 层（MC1-MC4）

| 维度 | 结论 | 详情 |
|------|------|------|
| MC1 错误处理 | ❌ | 无 try/except — `mcp/server.py:109-125` |
| MC2 参数默认值 | ✅ | `symbol="000001.SH"` 合理 |
| MC3 参数透传 | ✅ | `index_quote.get_index_quote_realtime(symbol)` — `mcp/server.py:124` |
| MC4 命名一致 | ⚠️ | MCP=registry=`tool_get_index_quote_realtime`，CLAUDE.md=`tool_get_index_quote`（缺 `_realtime` 后缀） |

### 一致性（S1-S6）

| 维度 | 结论 | 详情 |
|------|------|------|
| S1 字段覆盖 | ⚠️ | tushare: name=""；xueqiu: name 为 ticker code |
| S2 字段语义 | ✅ | pct_chg 均为百分比值；amount 均为元 |
| S3 数值精度 | ✅ | 均使用 float() |
| S4 日期格式 | ⚠️ | akshare/tushare timestamp 无时区；xueqiu 含 +08:00 |
| S5 排序方向 | N/A | 各 provider 仅返回 1 条记录 |
| S6 默认行为 | ✅ | 一致 |

### 问题清单

- [ ] **P1**: xueqiu `name` 字段映射 d["symbol"] 而非中文名 — `provider/xueqiu/index/realtime.py:67`
- [ ] **P1**: tushare `name` 硬编码空字符串 — `provider/tushare/index/realtime.py:28`
- [ ] **P1**: MCP 层无 try/except — `mcp/server.py:109-125`
- [ ] **P2**: CLAUDE.md 工具名 `tool_get_index_quote` 缺 `_realtime` 后缀
- [ ] **P2**: akshare/tushare timestamp 无时区，xueqiu 含 +08:00
- [ ] **P2**: MCP docstring 返回字段名 `pct_change` 与实际 `pct_chg` 不一致 — `mcp/server.py:122`
- [ ] **P2**: registry `api_name="index_zh_a_spot_em"` 但实际调用 sina 源 — `registry.py:72`

---

## 5. index_history

**Protocol**: `IndexHistoryProtocol.get_index_history(symbol: str, start: str, end: str) -> DataResult`
**Dataclass**: `IndexBar` (9 fields: symbol, date, open, high, low, close, volume, amount, pct_chg)
**Providers**: akshare ✓ / tushare ✓ / xueqiu ✓

### Interface 层（C8）

| 检查项 | 结论 | 详情 |
|--------|------|------|
| to_dict() key 一致性 | ✅ | 9 个字段名完全一致 |

### Provider 正确性（C1-C7）

| 维度 | akshare | tushare | xueqiu |
|------|---------|---------|--------|
| C1 协议签名 | ✅ | ✅ | ✅ |
| C2 字段映射 | ⚠️ volume 估算; amount 为万元 | ✅ amount*1000=元 | ⚠️ start 未用于过滤 |
| C3 Symbol转换 | ⚠️ 非.SH 后缀默认归 sz | ✅ 直接传入 | ⚠️ 缺少 `_INDEX_MAP` |
| C4 错误处理 | ✅ | ✅ | ✅ 含 auth 检查 |
| C5 边界条件 | ✅ | ✅ | ✅ |
| C6 DataResult | ✅ | ✅ | ✅ |
| C7 无副作用 | ✅ | ✅ | ✅ |

**C2 详细说明**:
- **akshare** (`provider/akshare/index/history.py:69-71`): 腾讯源无 volume 列，使用 `round(amount * 10000 / avg_price)` 估算。amount 保持腾讯源原始单位（万元），未转换为元。
- **tushare** (`provider/tushare/index/history.py:31`): `amount * 1000` 正确转换千元→元。
- **xueqiu** (`provider/xueqiu/index/history.py:73-81`): 仅用 `count=-284` 从 end 向前取数据，`start` 参数未用于服务端过滤。日期范围超过 ~284 个交易日时数据会被静默截断。

### Service 层（SC1-SC3）

| 维度 | 结论 | 详情 |
|------|------|------|
| SC1 Provider 注册完整 | ✅ | ak→ts(TUSHARE_TOKEN)→xq(XUEQIU_COOKIE) — `service/index.py:52-59` |
| SC2 优先级正确 | ✅ | ak→ts→xq |
| SC3 签名匹配 | ✅ | 参数透传正确 |

### MCP 层（MC1-MC4）

| 维度 | 结论 | 详情 |
|------|------|------|
| MC1 错误处理 | ❌ | 无 try/except — `mcp/server.py:128-150` |
| MC2 参数默认值 | ⚠️ | `end="20241231"` 硬编码过期日期 — `mcp/server.py:133` |
| MC3 参数透传 | ✅ | `index_history.get_index_history(symbol, start=start, end=end)` — `mcp/server.py:149` |
| MC4 命名一致 | ✅ | MCP=registry=CLAUDE.md=`tool_get_index_history` |

### 一致性（S1-S6）

| 维度 | 结论 | 详情 |
|------|------|------|
| S1 字段覆盖 | ✅ | 三个 provider 均填充全部 9 个字段 |
| S2 字段语义 | ❌ | **amount**: akshare=万元, tushare=元, xueqiu=元(推测) — 量级差异 |
| S3 数值精度 | ⚠️ | akshare volume 为估算值，与 tushare/xueqiu 真实值可能有偏差 |
| S4 日期格式 | ✅ | 均为 YYYYMMDD |
| S5 排序方向 | ⚠️ | 未统一显式排序 |
| S6 默认行为 | ⚠️ | xueqiu 固定取 284 条，长日期范围数据不完整 |

### 设计差异（非 bug）

- akshare 腾讯源不提供 volume，需从 amount 估算 — 数据源 API 限制
- xueqiu K 线需要登录 cookie（XUEQIU_COOKIE）— 数据源认证要求

### 问题清单

- [ ] **P0**: akshare amount 单位为"万元"，tushare 为"元" — 跨 provider 量级差异 — `provider/akshare/index/history.py:81`, `provider/tushare/index/history.py:31`
- [ ] **P1**: MCP 层无 try/except — `mcp/server.py:128-150`
- [ ] **P1**: MCP `end="20241231"` 硬编码过期日期 — `mcp/server.py:133`
- [ ] **P1**: xueqiu `start` 参数未用于过滤，超 284 交易日数据被截断 — `provider/xueqiu/index/history.py:73-81`
- [ ] **P1**: akshare symbol 转换：非 `.SH` 后缀默认归 `sz`，无后缀的纯数字代码可能被误分类 — `provider/akshare/index/history.py:38`
- [ ] **P2**: akshare volume 为估算值，未在 meta 中标注 — `provider/akshare/index/history.py:69-71`
- [ ] **P2**: MCP docstring 遗漏 amount 和 pct_chg 返回字段 — `mcp/server.py:147`
- [ ] **P2**: registry `api_name="index_zh_a_hist"` 但实际调用 `stock_zh_index_daily_tx` — `registry.py:88`
- [ ] **P2**: xueqiu history 缺少 realtime 中的 `_INDEX_MAP` 映射 — `provider/xueqiu/index/history.py:17-21`

---
