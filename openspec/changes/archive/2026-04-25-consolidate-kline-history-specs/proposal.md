## Why

`openspec/specs/` 下当前存在 daily-kline-history、weekly-kline-history、monthly-kline-history 三份独立 spec，但 `diff` 显示三份 95% 文本相同（仅替换「日 / 周 / 月」字样与少量 scenario 名）。这违反 SDD 原则「外部行为不变就不该写多份 spec」（参见 wiki `[[spec-driven-development]]` 与 `[[openspec-framework]]`）：

- 三份 spec 的 4 条核心 Requirement（独立工具暴露 / 上游对齐 / 默认主源 fallback / 后台可观测）本质是同一组行为契约的 period 维度复制。
- 周 / 月独有的「每日更新语义 + 未完成周期处理」与日线独有的「Web 后台展示状态」、月线独有的「前端独立入口」散落在三份文件中，任何一处更新都会引发跨文件不一致。
- 阶段 2 即将回填 `retroactive-baostock-minute-kline`，分钟 K 线需要新加一份 spec 时，按现有模式会变成 4 份高度重复 spec，进一步放大维护负担。

本次合并把三份 spec 收敛为单一 `kline-history` spec，按 period 维度组织 Requirement：通用 Requirement 用「period ∈ {daily, weekly, monthly, minute}」覆盖所有周期；周期专属行为（每日更新、未完成周期、分钟级权限）用各自专属 Requirement 表达。本 change **不修改任何 src/ 下代码**，仅做 spec 收敛。

## What Changes

- 新建 `openspec/specs/kline-history/` capability，吸收原三份 spec 的全部 Requirement。
- archive 后手动 `rm -rf openspec/specs/{daily,weekly,monthly}-kline-history/` 三个 capability 目录（OpenSpec 1.2.0 不允许「全部 Requirement 被 REMOVED」的空 capability，因此 capability 删除走物理清理而非 OpenSpec REMOVED 机制；详见 design.md Decision 5）。
- 在新 spec 中新增「分钟 K 线 period 范围」声明，为阶段 2 `retroactive-baostock-minute-kline` 接入腾出位置（不实现，仅预留 spec 槽位）。
- 在新 spec 中保留并显式化原三份散落的差异：日 / 周 / 月 / 分钟各自的更新时效、未完成周期处理、默认 provider 链。
- 非目标：不修改任何 provider/service/MCP/CLI/Dashboard 代码；不修改 `delivery-tool-spec-contract`；不改变 MCP 工具名（仍为 `tool_get_kline_daily_history` / `tool_get_kline_weekly_history` / `tool_get_kline_monthly_history` / `tool_get_kline_minute_history`）。
- 兼容性：MCP / CLI / HTTP API / Dashboard 行为零变更；只有 `openspec/specs/` 下 capability 名变化。
- 上线风险：极低，spec 收敛不影响运行时；唯一风险是合并时遗漏周期专属 scenario，对策见 design.md。

## Capabilities

### New Capabilities
- `kline-history`: 个股历史 K 线能力的统一行为契约，覆盖 daily / weekly / monthly / minute 四个周期，定义独立工具暴露、上游对齐、默认 provider 链、未完成周期处理、后台可观测性等约束。

### Modified Capabilities
- 无。

### Removed Capabilities
- `daily-kline-history`、`weekly-kline-history`、`monthly-kline-history`：合并到新 `kline-history`，所有 Requirement 与 Scenario 已等价迁移；不再单独存在。capability 物理目录在 archive 后由维护方手动 `rm -rf` 清理（OpenSpec 不支持空 capability 归档）。

## Impact

- 受影响代码：无。
- 受影响 spec：`openspec/specs/daily-kline-history/spec.md`（删除）、`weekly-kline-history/spec.md`（删除）、`monthly-kline-history/spec.md`（删除）、`openspec/specs/kline-history/spec.md`（新建）。
- 受影响 archived change：无（历史 archive 中的 spec delta 文件保留不变，仅作为历史记录）。
- 依赖：复用 archive/2026-04-10 的 `upstream-alignment.md` 作为合并后 spec 的上游对齐依据；遵循 archive/2026-04-25 的 `openspec-governance` 第 6 条 Requirement「OpenSpec 与 tool-acceptance skill 关系必须显式说明」。
