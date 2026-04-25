## 1. 起草新 kline-history spec

- [x] 1.1 创建 `openspec/changes/consolidate-kline-history-specs/specs/kline-history/spec.md`，按 design.md 的 source-of-truth 映射表写入 7 条 ADDED Requirements 与全部 Scenario。验证：覆盖原三份 spec 的全部 Requirement + 分钟 K 线 + 东财代理绕过显式约束。
- [x] 1.2 自检 7 条 Requirement 全部含至少一个 4-井号 Scenario 且使用 RFC 2119 关键词（MUST / MUST NOT / SHALL）。验证：`grep -E "^#### Scenario" openspec/changes/consolidate-kline-history-specs/specs/kline-history/spec.md | wc -l` ≥ 7。

## 2. 旧 capability 删除策略（不走 REMOVED）

- [x] 2.1 验证 OpenSpec 不允许「Requirement 全部 REMOVED 后产生空 capability」：实测 `openspec archive` 校验报「Spec must have at least one requirement」并 abort。
- [x] 2.2 决定改用「archive 仅 ADDED + archive 后物理 `rm -rf`」策略；同步更新 design.md Decision 5、proposal.md What Changes 与 Removed Capabilities 段、acceptance.md Migration 章节。
- [x] 2.3 把已写好的三份 REMOVED delta 文件删除（`rm -rf openspec/changes/consolidate-kline-history-specs/specs/{daily,weekly,monthly}-kline-history`），仅保留 `specs/kline-history/`。验证：`openspec validate consolidate-kline-history-specs --strict` 通过。
- [x] 2.4 当前 specs/{daily,weekly,monthly}-kline-history/spec.md 改为新格式（`# <name> Specification` + `## Purpose` + `## Requirements`），消除 OpenSpec 老格式遗留以便后续操作。验证：归档预演时 OpenSpec 能识别 capability 结构。

## 3. 自我验证

- [x] 3.1 用 `diff` 工具对比三份旧 spec 的 Requirement 标题与 REMOVED 段中的 Requirement 标题，确认 12 条全部匹配。验证：12/12 标题完全一致，已逐条比对。
- [x] 3.2 对 `kline-history/spec.md` 的 7 条 Requirement 与 design.md 的 source-of-truth 映射表逐行核对。验证：7 条 Requirement 全部在 design.md 映射表中有对应迁移来源（7 行表格 ↔ 7 条 Requirement）。
- [x] 3.3 用 `openspec show consolidate-kline-history-specs` 输出预览归档后的 spec 形态，确认 ADDED + REMOVED 均被识别。验证：JSON 输出统计 kline-history ADDED 7 / daily-kline-history REMOVED 4 / weekly-kline-history REMOVED 4 / monthly-kline-history REMOVED 4。
- [x] 3.4 写 `acceptance.md`，按 Completeness / Correctness / Coherence 三维 + 三类风险显式记录验收过程。验证：acceptance 模板七章节齐全。

## 4. 归档与目录清理

- [x] 4.1 `openspec archive consolidate-kline-history-specs`，OpenSpec 仅新增 `specs/kline-history/spec.md`，不动旧三份。验证：`Specs to update: kline-history: create` + `+ 7 added`，archive 成功。
- [x] 4.2 手动清理三份旧 capability 目录：`rm -rf openspec/specs/{daily,weekly,monthly}-kline-history/`。验证：`ls openspec/specs/` 仅剩 `kline-history`、`delivery-tool-spec-contract`、`openspec-governance`。
- [x] 4.3 运行 `openspec list --specs` 确认最终 capability 列表正确。验证：3 个 capability：`delivery-tool-spec-contract` (5 条实际 Requirement，但因老格式被 OpenSpec 计为 0)、`kline-history` 7 条、`openspec-governance` 6 条。`delivery-tool-spec-contract` 老格式问题留作 backlog，不在本 change scope。
