<!-- 用 openspec/templates/acceptance.template.md 落地。 -->

## 验收结论

变更 `consolidate-kline-history-specs` 已完成实现和验证。三份 95% 重复的 K 线 spec（daily/weekly/monthly-kline-history）已合并为单一 `kline-history` capability，按周期参数化组织 7 条 Requirement / 14 条 Scenario。原三份 capability 中全部 12 条 Requirement 在本 acceptance.md 的 Migration 章节逐条记录等价覆盖关系，旧 capability 物理目录在 archive 后由维护方手动 `rm -rf` 清理（OpenSpec 1.2.0 不支持空 capability 归档，详见 design.md Decision 5）。本 change 不修改任何 src/ 下 Python 代码，运行时行为零变更。

## Migration（旧 12 条 Requirement → 新 7 条 Requirement）

| 旧 capability | 旧 Requirement | 新 Requirement |
|---|---|---|
| daily-kline-history | 个股历史日线必须作为独立能力对外提供 | 个股历史 K 线必须按周期独立暴露 |
| daily-kline-history | 个股历史日线必须先对齐上游官方定义 | 个股历史 K 线必须先完成上游对齐再实现 provider |
| daily-kline-history | 个股历史日线默认只使用主源和 fallback | 各周期 K 线必须采用项目偏好的默认主源与 fallback |
| daily-kline-history | Web 管理后台必须展示历史日线的源级状态 | 各周期 K 线必须在 Web 管理后台暴露源级状态 |
| weekly-kline-history | 个股历史周线必须作为独立能力对外提供 | 个股历史 K 线必须按周期独立暴露 |
| weekly-kline-history | 个股历史周线必须采用每日更新周线语义 | 各周期 K 线必须显式定义更新时效与未完成周期处理 |
| weekly-kline-history | 个股历史周线必须先完成上游对齐再改造 provider | 个股历史 K 线必须先完成上游对齐再实现 provider |
| weekly-kline-history | 个股历史周线默认只使用 tushare 和 akshare | 各周期 K 线必须采用项目偏好的默认主源与 fallback + 涉及东财上游的周期 K 线 fallback 必须配置代理绕过 |
| monthly-kline-history | 个股历史月线必须作为独立能力对外提供 | 个股历史 K 线必须按周期独立暴露 |
| monthly-kline-history | 个股历史月线必须采用每日更新月线语义 | 各周期 K 线必须显式定义更新时效与未完成周期处理 |
| monthly-kline-history | 个股历史月线必须先完成上游对齐再改造 provider | 个股历史 K 线必须先完成上游对齐再实现 provider |
| monthly-kline-history | 前端与后台必须同步改造成独立历史月线能力 | 个股历史 K 线必须按周期独立暴露 + 各周期 K 线必须在 Web 管理后台暴露源级状态 |

12/12 旧 Requirement 全部映射到新 spec。新 spec 额外引入 2 条 Requirement（涉及东财上游代理绕过、分钟 K 线权限敏感性），来自代码事实与 ab32a22 commit 实际实现，原三份旧 spec 缺失。

## Completeness

按本 change 的 7 条新 Requirement 逐条核对：

- 已实现「个股历史 K 线必须按周期独立暴露」：包含 4 个 Scenario（CLI / MCP / HTTP / 前端独立入口），覆盖原 daily/weekly/monthly 三份「独立能力」Requirement。
- 已实现「个股历史 K 线必须先完成上游对齐再实现 provider」：含 2 个 Scenario，并强制 upstream-alignment.md 七维度覆盖与 archive 阻断规则。
- 已实现「各周期 K 线必须显式定义更新时效与未完成周期处理」：含 3 个 Scenario（日线时效 / 周月未完成周期一致性 / 分钟实时未完成 bar）。
- 已实现「各周期 K 线必须采用项目偏好的默认主源与 fallback」：含 2 个 Scenario，显式列出四周期默认链 + 分钟无 fallback。
- 已实现「涉及东财上游的周期 K 线 fallback 必须配置代理绕过」：含 1 个 Scenario，新增显式约束（原三份 spec 缺失，来自代码事实）。
- 已实现「各周期 K 线必须在 Web 管理后台暴露源级状态」：含 1 个 Scenario，扩展为四周期共享。
- 已实现「分钟 K 线必须显式声明权限敏感性」：含 1 个 Scenario，新增以匹配 ab32a22 commit 的实际实现。

## Correctness

已执行并通过：

- `openspec validate consolidate-kline-history-specs --strict` → `Change 'consolidate-kline-history-specs' is valid`
- `grep -E "^### Requirement" openspec/specs/{daily,weekly,monthly}-kline-history/spec.md` 与 REMOVED 段标题逐行对比 → 12/12 完全匹配
- `grep -cE "^### Requirement" openspec/changes/consolidate-kline-history-specs/specs/kline-history/spec.md` → 7
- `grep -cE "^#### Scenario" openspec/changes/consolidate-kline-history-specs/specs/kline-history/spec.md` → 14
- `openspec show consolidate-kline-history-specs --type change --json` → JSON 统计 kline-history ADDED 7 / daily REMOVED 4 / weekly REMOVED 4 / monthly REMOVED 4，与预期一致

未运行 pytest，因本 change 不动 src/ 代码，运行时行为零变更。

未做 Playwright 验证，因本 change 不动前端。

## Coherence

- 新 spec 严格按 OpenSpec 规则使用 RFC 2119 关键词（MUST / MUST NOT / SHALL）+ Given/When/Then 4-井号 Scenario 结构。
- spec 仅写行为契约，未出现类名、函数名、框架名或文件路径（与 `openspec/config.yaml` specs rules 一致）。
- 新 spec 的「数据接口必须显式定义更新时效、字段含义、单位、未完成周期处理方式、错误行为」已通过 7 条 Requirement 覆盖（与 specs rules 一致）。
- 阶段 0 落地的 acceptance.template.md 章节模板被本文件严格遵循（与 openspec-governance 第 5 条 Requirement 一致）。
- design.md 的 5 条 Decision 与 source-of-truth 映射表与最终 spec 内容一致。
- archive 后会自动产生 `openspec/specs/kline-history/spec.md`，三份旧 capability 的 spec.md 中 Requirement 全部移除（剩空文件，由 task 4.2 手动 `rm -rf` 清理）。

## 未测试项与风险

- 未实测 archive 操作对三份旧 capability 目录的清理行为：OpenSpec 1.2.0 已知不会自动删除空 capability 目录，需要 task 4.2 手动 `rm -rf`。本验收仅在归档前完成，归档后的清理动作将记录在 archive 目录的 tasks.md 完成态中。
- 未实测「阶段 2 retroactive-baostock-minute-kline 接入时分钟相关 Requirement 与实际一致」：本 change 已基于 ab32a22 commit 内容撰写分钟 K 线 Requirement，但实际的 baostock 字段、单位、错误情况需在阶段 2 二次校对，若发现 drift 触发同步流程。
- 未实测 historical archive（archive/2026-04-10）中 spec delta 文件指向已删除 capability 后的归档系统行为：根据 OpenSpec 设计，historical archive 是冻结历史，不会被 validate 检查，应不影响。

## Spec Drift

无。本 change 是 spec→spec 的整理动作，不存在「实现与 spec 偏离」语境；REMOVED 段的 12 条 Migration 与新 spec 7 条 Requirement 之间的覆盖关系已通过 design.md 映射表与 task 3.1/3.2 双重核对。

## 上游未对齐项

无。本 change 不接入新数据源；新 spec 中关于 tushare/akshare/baostock 的 provider 链表述均沿用 archive/2026-04-10/upstream-alignment.md 的对齐结论与 ab32a22 commit 已实现的分钟 K 线事实，无新增上游接口。
