# RETROACTIVE — 任务清单

> 本 change 是历史合规追认，所有「实现」步骤已在 ab32a22 + c010fe9 完成。任务清单仅追溯实施时该做但未做的合规材料。

## 1. 起草 retroactive 制品

- [x] 1.1 创建 `proposal.md`，记录本 change 是 retroactive、覆盖哪两个 commit、为何需要追认。验证：proposal 顶部含「RETROACTIVE」标识，列出 ab32a22 + c010fe9 两个 hash。
- [x] 1.2 创建 `design.md`，记录 source-of-truth 映射表（实施事实 → spec 对应）+ 三条 Decision（用 MODIFIED 而非 ADDED / 不重写代码 / upstream-alignment 用反推方式）。验证：design 含 3 条 Decision + 一张映射表。
- [x] 1.3 创建 `upstream-alignment.md`，按七维度对照表记录 baostock 的接口、字段、单位、复权、历史范围、更新时间、状态，并补充字段映射表与权限敏感性说明。验证：模板七章节 + 三个结论小节齐全。

## 2. 起草 spec MODIFIED delta

- [x] 2.1 在 `specs/kline-history/spec.md` 用 MODIFIED 重写「分钟 K 线必须显式声明权限敏感性」Requirement，融入 baostock>=0.9.1 与服务地址变更两个新约束，扩展为 3 个 Scenario。验证：Requirement 改名为「分钟 K 线必须显式声明权限敏感性与上游依赖最低版本」、含 3 个 Scenario。
- [x] 2.2 `openspec validate retroactive-baostock-minute-kline --strict` 通过。验证：CLI 退出码 0。

## 3. 写 acceptance 并归档

- [x] 3.1 写 `acceptance.md`，按 Completeness / Correctness / Coherence 三维 + 三类风险显式记录。Spec Drift 段必须显式记录「当前实现的 DataFetchError 不携带 baostock 版本号与服务地址提示」这一 drift，并标记为「待跟进」。验证：acceptance 七章节齐全，drift 段明确。
- [ ] 3.2 `openspec archive retroactive-baostock-minute-kline -y`，把 `kline-history` 中分钟权限敏感性 Requirement 替换为 MODIFIED 版本。验证：`openspec list --archived` 包含本 change；`openspec/specs/kline-history/spec.md` 中分钟权限敏感性 Requirement 含 3 个 Scenario（原 1 个 → 现 3 个）。
- [x] 3.3 不需要任何代码或目录清理（本 change 不动 src）。
