## Why

当前 `tool_get_kline_history` 把日线、周线、月线和分钟级都塞在同一个入口里，但上游 `tushare` 和 `akshare` 对这些周期的官方定义并不相同，导致 provider 适配、service 统一语义、交付层文档和后台健康检查都变得难以维护。尤其是周线和月线，已经出现“同一接口、不同源、不同语义”的问题。

这次变更需要把历史 K 线彻底拆开：将日线、周线、月线变成三个独立能力，先完成上游官方定义对齐，再同步改造 provider、service、CLI、MCP、HTTP API 和前端页面，最终把复杂度从“一个接口内部处理所有周期差异”收敛成“每个接口只处理一种明确语义”。

## What Changes

- **BREAKING** 将当前 `tool_get_kline_history` 拆分为三个独立历史接口：日线、周线、月线。
- 下线分钟级股票 K 线，不再对外提供该能力。
- 先完成上游对齐：
  - 日线对齐 `tushare` 官方历史日线文档与 `akshare` 股票历史行情文档。
  - 周线、月线对齐 `tushare` 官方“周/月线行情(每日更新)”文档与 `akshare` 股票历史行情文档。
- 改造 `provider` 层，按“日线 / 周线 / 月线”分别适配，不再让一个 provider 适配器同时混用多套周期语义。
- 改造 `service` 层，形成三个独立 dispatcher 和统一对外语义。
- 改造 `cli`、`mcp`、`http api` 和前端页面，彻底替换旧的 period 驱动入口。
- 默认只启用 `tushare` 和 `akshare` 参与新的历史 K 线主交付链；其他源先关闭开关，保留后续单独验收空间。
- Web 管理后台继续保留 provider 级健康度和验收可视化，便于维护方观察各源状态。

## Capabilities

### New Capabilities
- `daily-kline-history`: 个股历史日线行情，提供统一的日线语义与字段定义。
- `weekly-kline-history`: 个股历史周线行情，提供统一的“每日更新周线”语义与字段定义。
- `monthly-kline-history`: 个股历史月线行情，提供统一的“每日更新月线”语义与字段定义。

### Modified Capabilities
- None. `openspec/specs/` 当前还没有已建立的主规格，本次以新增 capability 为主。

## Impact

- 对外接口影响：
  - CLI、MCP、HTTP API 不再通过一个 `period` 参数承载所有历史 K 线能力，而是暴露三个独立工具。
  - 前端调用页面不再展示股票历史 K 线的周期下拉，而是改为三个独立工具入口。
- 代码影响范围：
  - ToolSpec 注册与工具元数据
  - provider 层历史 K 线适配
  - service 层 dispatcher 与 provider 选择逻辑
  - CLI、MCP、dashboard API 和前端调用页面
  - 健康检查、验收逻辑、测试与文档
- Provider 策略影响：
  - 主源：`tushare`
  - fallback：`akshare`
  - 其他源默认关闭，不参与本次主能力交付
- 上游官方文档入口：
  - Tushare 历史日线：`https://tushare.pro/document/2?doc_id=27`
  - Tushare 周/月线行情（每日更新）：`https://tushare.pro/document/2?doc_id=336`
  - AkShare 股票历史行情：`https://akshare.akfamily.xyz/data/stock/stock.html#id23`
