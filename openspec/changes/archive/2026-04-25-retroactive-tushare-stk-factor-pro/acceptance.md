<!-- 用 openspec/templates/acceptance.template.md 落地。 -->
<!-- 本 change 是 retroactive，「实现」由 1e65aba 完成；本验收聚焦合规材料完整性 + spec drift 识别。 -->

## 验收结论

变更 `retroactive-tushare-stk-factor-pro` 已完成 retroactive 合规追认。1e65aba（2026-04-16）的「3 个 tushare 接口接入 + technical / fund_flow 两个新 domain」能力已沉淀为 OpenSpec 可追溯材料：proposal / design / tasks / upstream-alignment / acceptance 五份制品齐全；新建 `technical-factors`（4 条 Requirement）与 `fund-flow`（6 条 Requirement）两个 capability。本 change 不修改任何 src/ 代码。识别 2 项 spec drift，已显式记录待跟进。

## Completeness

- 已落地 retroactive proposal：顶部标注 RETROACTIVE，列出 1e65aba commit 的范围与 3 个新 tool。
- 已落地 retroactive design：含 source-of-truth 映射表（7 行实施事实 → spec 对应）+ 4 条 Decision + 风险段（含 spec drift 预警）。
- 已落地 retroactive upstream-alignment：分别对 stk_factor_pro / moneyflow_ind_dc / moneyflow_mkt_dc 写七维度对照表 + stk_factor_pro 字段名映射表（11 行）+ 5 条结论。
- 已落地新 capability `technical-factors`：4 条 ADDED Requirement（按单一工具暴露 / 上游对齐 / 字段单位换算 / 单源限制声明），含 6 个 Scenario。
- 已落地新 capability `fund-flow`：6 条 ADDED Requirement（板块按单一工具 / 大盘按单一工具 / 上游对齐 / 字段单位换算 / 更新时效声明 / 单源声明），含 7 个 Scenario。
- 历史合规追认覆盖：1e65aba 涉及的 19 个文件中，所有 src/ 与 tool_specs 文件的设计意图均在 design.md source-of-truth 映射或 upstream-alignment.md 字段映射中可定位；frontend HealthCheck.tsx 标签更新为非业务变更，不需 spec。

## Correctness

已执行并通过：

- `openspec validate retroactive-tushare-stk-factor-pro --strict` → `Change 'retroactive-tushare-stk-factor-pro' is valid`
- `git show --stat 1e65aba` → 确认涉及文件数 = 19、新增行数 = 789，与 proposal 描述一致
- `git show 1e65aba -- src/finance_data/tool_specs/registry.py` → 确认 3 个 ToolSpec（tool_get_stock_factor_pro_history / tool_get_dc_board_moneyflow_history / tool_get_dc_market_moneyflow_history）已注册
- `git show 1e65aba -- src/finance_data/provider/tushare/technical/factor.py` → 确认字段映射（vol×100 / amount×1000 / total_share×10000 / ma_bfq_5→ma5 / kdj_bfq→kdj_j 等）与 spec 要求一致
- `git show 1e65aba -- .claude/rules/finance-coding.md` → 确认「接口对接铁律」章节已沉淀
- 历史回归：1e65aba commit message 暗含「全部 6 层均通过」，本 change 不动代码，无需重跑测试

未做 Playwright 验证：本 change 不动前端业务逻辑，HealthCheck domain labels 是补充。

## Coherence

- 本 change 仅做合规追认，不重写代码、不调整 fallback 策略、不改工具签名（与 design.md Decision 3 一致）。
- 两个 capability 拆分按 domain 而非 source（与 design.md Decision 1 一致），与 CLAUDE.md 14 个 domain 体系对齐。
- 资金流的两个 tool 共用 `fund-flow` capability，板块和大盘各一条「按单一工具暴露」Requirement + 共享的上游对齐 / 单位 / 时效 / 单源约束（与 design.md Decision 2 一致）。
- `.claude/rules/finance-coding.md` 中「接口对接铁律」未在本 change 重定义，由阶段 0 governance Requirement 2 引用（与 design.md Decision 4 一致）。
- 所有 retroactive 材料引用阶段 0 的 OpenSpec 治理 + 阶段 1 的格局，符合 governance 「项目特有 artifact 必须沉淀为模板」要求。

## 未测试项与风险

- 未真实调用 `pro.stk_factor_pro()` / `pro.moneyflow_ind_dc()` / `pro.moneyflow_mkt_dc()` 验证返回字段：retroactive 用 1e65aba commit diff 反推。若后续发现字段差异，触发独立 tushare provider 验收 change。
- 未实测「单次 10000 条超限时实际行为」：spec 要求抛 DataFetchError 区分 auth / data，但 1e65aba 实现可能仅 catch generic Exception 抛 data kind，不区分超限场景。详见 Spec Drift 1。
- 未实测 `net_amount_rate` 单位是否真为百分比：spec 假设是百分比（与 `pct_chg` 同），但 provider 代码未做显式换算或 assert。详见 Spec Drift 2。
- 未做跨 provider 一致性测试：technical-factors / fund-flow 是单源 capability，跨源一致性测试不适用。

## Spec Drift

**Drift 1（待跟进）**：spec 要求「上游因积分不足或单次限制返回错误时 service MUST 抛出 DataFetchError（kind=auth 或 kind=data），MUST NOT 静默返回部分数据」。但 1e65aba 实现的 `provider/tushare/technical/factor.py` 错误归类逻辑只用关键字判断（`if "权限" in reason or "token" in reason.lower(): kind = "auth"`），未必能区分「单次 10000 条超限」这种边界场景。  
**处理**：不在本 retroactive 修代码。已记录 backlog，建议独立 change `enhance-tushare-error-classification`。

**Drift 2（待跟进）**：spec 假设 `net_amount_rate` 单位是百分比，与 `pct_chg` 一致。但 1e65aba 中 fund_flow provider 未显式 assert 或换算 `net_amount_rate`，是否真为百分比未经验证。  
**处理**：不在本 retroactive 修代码。已记录 backlog，建议独立 change `verify-fund-flow-rate-units` 真实调用 + 打印验证。

无其他 drift。

## 上游未对齐项

- akshare 等价资金流接口（同源东财但字段格式不一致）：本 change 不接入。若日后需要 fallback，需独立 change 做对齐。
- tushare `stk_factor`（非 pro 版）：本 change 不接入，因 pro 字段更全。
- 实时（盘中）资金流：tushare 暂无对等接口，本 change 不涉及。
