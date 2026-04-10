## Context

当前股票历史 K 线能力由单一工具 `tool_get_kline_history` 承载，并通过 `period` 参数在日线、周线、月线和分钟级之间切换。这个设计把多套上游语义压在了一个入口上：

- `tushare` 的日线、周线、月线来自不同官方文档入口，且周线/月线使用“每日更新”语义更适合当前产品。
- `akshare` 的股票历史行情文档同时覆盖 `daily/weekly/monthly`，但我们当前实现对不同周期并未完全按官方路径对齐。
- CLI、MCP、HTTP API 和前端页面都围绕一个 `period` 参数建模，导致工具契约复杂、验收边界模糊、后台健康检查难以解释。

这次设计把“周期差异”从接口内部逻辑提升为接口边界，用三个独立工具承载三种明确语义。

## Goals / Non-Goals

**Goals:**
- 将股票历史 K 线拆成日线、周线、月线三个独立能力。
- 对齐 `tushare` 和 `akshare` 的官方上游定义，再改造 provider。
- 默认只启用 `tushare` 和 `akshare` 参与主交付链。
- 彻底改造 provider、service、CLI、MCP、HTTP API 和前端页面。
- 保持 Web 管理后台的 provider 级健康度与验收可见性。

**Non-Goals:**
- 本次不保留分钟级股票 K 线能力。
- 本次不把 `xueqiu`、`baostock`、`tencent` 纳入新的历史 K 线主交付链。
- 本次不扩展到指数、板块或其它领域的 K 线拆分。

## Decisions

### 决策 1：拆成三个独立工具，不保留旧的 period 驱动入口

采用三个新工具：
- `tool_get_daily_kline_history`
- `tool_get_weekly_kline_history`
- `tool_get_monthly_kline_history`

不再保留 `tool_get_kline_history` 作为兼容入口。原因：
- 用户侧契约更简单，不再需要理解 `period` 枚举。
- provider 和 service 的语义边界更清楚。
- 周线、月线可独立验收，不再被日线和分钟级逻辑污染。

备选方案：
- 保留旧接口并做转发。未采用，因为会长期维持两套入口，增加维护成本和歧义。

### 决策 2：周线、月线统一采用“每日更新”语义

`tushare` 周线、月线默认对齐：
- `doc_id=336` 周/月线行情（每日更新）

而不是默认对齐：
- `doc_id=144` 周线行情
- `doc_id=145` 月线行情

原因：
- 当前产品更需要在管理后台和交付层看到“当前未完成周/月”的更新状态。
- 这与用户已经暴露出的验收需求更一致。

备选方案：
- 采用旧的完成周期语义。未采用，因为会与当前“每日更新”预期冲突。

### 决策 3：Provider 策略固定为主源 + fallback

新的历史 K 线能力默认只启用：
- 主源：`tushare`
- fallback：`akshare`

其它源默认关闭，不参与主交付链和主一致性判断。原因：
- 降低维护复杂度。
- 先把两源语义彻底对齐，再考虑扩源。

### 决策 4：service 统一语义，Web 后台保留源级视角

对外层：
- CLI、MCP、HTTP API 只暴露 service 语义。

后台层：
- Web 继续展示 provider 健康度、源级错误、验收状态。

原因：
- 使用方不应关心底层源。
- 维护方必须看到每个源是否健康。

### 决策 5：每个能力都需要显式上游映射表

| 能力 | tushare 上游 | akshare 上游 | 备注 |
|------|--------------|--------------|------|
| 日线 | `doc_id=27` 历史日线 | 股票历史行情 `daily` | 先实调确认字段和单位 |
| 周线 | `doc_id=336` 周/月线行情(每日更新) | 股票历史行情 `weekly` | 明确未完周处理 |
| 月线 | `doc_id=336` 周/月线行情(每日更新) | 股票历史行情 `monthly` | 明确未完月处理 |

## Risks / Trade-offs

- [旧入口中断] → 通过 proposal/spec 明确这是 breaking change，并在文档和前端彻底替换旧入口。
- [上游语义仍有隐藏差异] → 先做原始接口验证，再改 provider；验收时按接口逐层检查。
- [后台和交付层状态不一致] → service 和 provider 健康状态分开展示，避免混淆。
- [改造范围大] → 按 provider -> service -> ToolSpec/CLI/MCP/API -> 前端页面 -> 验收与测试 的顺序实施。

## Migration Plan

1. 建立三个新能力的 spec。
2. 完成 `tushare` 与 `akshare` 的上游对齐和原始调用验证。
3. 改造 provider 和 service。
4. 替换 ToolSpec、CLI、MCP、HTTP API 和前端页面入口。
5. 更新健康检查、测试和文档。
6. 下线旧的 `tool_get_kline_history`。

如果中途发现周线或月线的上游语义无法统一，则暂停实现，先回写 spec/design，而不是硬推代码。

## Open Questions

- 周线、月线在 `akshare` 上是否需要额外代理绕过或源切换，才能稳定对齐官方定义？
- 旧接口下线时，是否需要保留一次性的错误提示或迁移说明？
