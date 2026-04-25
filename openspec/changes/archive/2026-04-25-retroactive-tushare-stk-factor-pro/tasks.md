# RETROACTIVE — 任务清单

> 本 change 是历史合规追认，所有「实现」步骤已在 1e65aba 完成。任务清单仅追溯实施时该做但未做的合规材料。

## 1. 起草 retroactive 制品

- [x] 1.1 创建 `proposal.md`，记录本 change 是 retroactive、覆盖 1e65aba commit、列出 3 个新增 tool 与 2 个新 domain（technical / fund_flow）。
- [x] 1.2 创建 `design.md`，含 source-of-truth 映射表 + 4 条 Decision（拆为两 capability / 资金流共用 capability / 不重构窗口拆分 / 不重定义接口对接铁律）。
- [x] 1.3 创建 `upstream-alignment.md`，按七维度对照表分别记录 stk_factor_pro / moneyflow_ind_dc / moneyflow_mkt_dc 三个上游接口；含 stk_factor_pro 字段名映射表。

## 2. 起草两个新 capability spec

- [x] 2.1 在 `specs/technical-factors/spec.md` 写 4 条 ADDED Requirements：单一工具暴露 / 上游对齐 / 字段单位换算 / 单源限制声明。
- [x] 2.2 在 `specs/fund-flow/spec.md` 写 6 条 ADDED Requirements：板块按单一工具 / 大盘按单一工具 / 上游对齐 / 字段单位换算 / 更新时效声明 / 单源声明。
- [x] 2.3 `openspec validate retroactive-tushare-stk-factor-pro --strict` 通过。

## 3. 写 acceptance 并归档

- [x] 3.1 写 `acceptance.md`，按 Completeness / Correctness / Coherence + 三类风险显式记录。Spec Drift 段已显式记录两项 drift：单次 10000 条超限错误归类、net_amount_rate 百分比未验证。
- [ ] 3.2 `openspec archive retroactive-tushare-stk-factor-pro -y`，自动新增 `specs/technical-factors/spec.md` 与 `specs/fund-flow/spec.md`。验证：`openspec list --specs` 显示 5 个 capability（原 3 + 新 2）。
- [x] 3.3 不需要任何代码或目录清理（本 change 不动 src）。
