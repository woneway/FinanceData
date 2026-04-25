# RETROACTIVE — 任务清单

> 本 change 是历史合规追认，所有「实现」步骤已在 fe01b51 完成。任务清单仅追溯实施时该做但未做的合规材料。

## 1. 起草 retroactive 制品

- [x] 1.1 创建 `proposal.md`，记录本 change 是 retroactive、覆盖 fe01b51 commit、明确把「DuckDB 缓存层」与「pct_change → pct_chg breaking」分别声明。
- [x] 1.2 创建 `design.md`，含 source-of-truth 映射表（8 行实施事实 → spec 对应）+ 5 条 Decision（拆为两 capability / 不规定开关实现 / validator 用 SHOULD / 写责任与读路径解耦 / 不追责 commit 拆分）。
- [x] 1.3 不需要 upstream-alignment.md（本 change 不接入新数据源）。
- [x] 1.4 在 proposal 中显式标记「pct_change → pct_chg」为 breaking，列出受影响的 4 个 interface 文件。

## 2. 起草两个新 capability spec

- [x] 2.1 在 `specs/cache-layer/spec.md` 写 6 条 ADDED Requirements：默认启用且可被显式关闭 / T-1 规则 / 三个语义入口 / tushare provider 接入模式 / 不绕过测试 mock / 写入责任与读路径解耦。
- [x] 2.2 在 `specs/field-naming/spec.md` 写 3 条 ADDED Requirements：涨跌幅字段必须用 pct_chg / breaking change 必须显式声明 / validator 守护（SHOULD）。
- [x] 2.3 `openspec validate retroactive-duckdb-cache-layer --strict` 通过。

## 3. 写 acceptance 并归档

- [x] 3.1 写 `acceptance.md`，按 Completeness / Correctness / Coherence + 三类风险显式记录。Spec Drift 段标注 fe01b51 当时未拆 commit 的事实，但归类为「设计缺陷追认」而非 drift；validator 未实现归类为「未测试项」。
- [ ] 3.2 `openspec archive retroactive-duckdb-cache-layer -y`，自动新增 `specs/cache-layer/spec.md` 与 `specs/field-naming/spec.md`。验证：`openspec list --specs` 显示 7 个 capability（原 5 + 新 2）。
- [x] 3.3 不需要任何代码或目录清理（本 change 不动 src）。
