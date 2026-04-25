<!-- 用 openspec/templates/acceptance.template.md 落地。 -->
<!-- 本 change 是 retroactive，「实现」由 ab32a22 + c010fe9 完成；本验收聚焦合规材料完整性 + spec drift 识别。 -->

## 验收结论

变更 `retroactive-baostock-minute-kline` 已完成 retroactive 合规追认。ab32a22（2026-04-20）+ c010fe9（2026-04-25）的「分钟 K 线 baostock 接入」能力已沉淀为 OpenSpec 可追溯材料：proposal / design / tasks / upstream-alignment / acceptance 五份制品齐全；`kline-history` capability 中「分钟权限敏感性」Requirement 通过 MODIFIED 强化为含 3 个 Scenario 的形态，融入 baostock>=0.9.1 与服务地址变更两个新约束。本 change 不修改任何 src/ 代码、不修改 pyproject.toml。识别 1 项 spec drift，已显式记录待跟进。

## Completeness

- 已落地 retroactive proposal：顶部标注 RETROACTIVE，列出 ab32a22 + c010fe9 两 hash，说明追认范围与非目标。
- 已落地 retroactive design：含 source-of-truth 映射表（6 行实施事实 → spec 对应）+ 3 条 Decision + 风险段（含 spec drift 预警）。
- 已落地 retroactive upstream-alignment：七维度对照表（baostock 主源 + tushare 未启用对比）、字段映射表（baostock 原始 → MinuteKlineBar）、权限敏感性说明、4 条结论。
- 已落地 spec MODIFIED：`kline-history` 的「分钟 K 线必须显式声明权限敏感性」Requirement 重命名为「⋯⋯与上游依赖最低版本」，扩展为 3 个 Scenario（权限提示 / 依赖最低版本 / 服务地址变更容错）。
- 已落地 retroactive tasks：8 项任务清单，均与本 change 文档动作对应。
- 历史合规追认覆盖：ab32a22 涉及的全部 6 个 src 文件（interface/kline/minute.py、provider/baostock/kline/minute.py、service/kline.py、tool_specs/registry.py、client.py、mcp/server.py）的设计意图均在 design.md source-of-truth 映射或 upstream-alignment.md 字段映射中可定位。

## Correctness

已执行并通过：

- `openspec validate retroactive-baostock-minute-kline --strict` → `Change 'retroactive-baostock-minute-kline' is valid`
- `git show --stat ab32a22 c010fe9` → 确认两 commit 涉及文件数 = 10（ab32a22）+ 1（c010fe9，pyproject.toml）
- `cat openspec/specs/kline-history/spec.md` 比对当前 spec 中分钟权限敏感性 Requirement 形态：当前 1 个 Scenario，本 change 待 archive 后变为 3 个 Scenario
- `grep -A 5 "_VALID_PERIODS" src/finance_data/provider/baostock/kline/minute.py` → 确认 5/15/30/60min 四档 period 与 spec 一致
- `grep "baostock" pyproject.toml` → 确认 baostock>=0.9.1 已在依赖中
- 历史回归：ab32a22 commit message 声明「405 passed」，本 change 不动代码，无需重跑测试

未做 Playwright 验证：本 change 不涉及前端。

## Coherence

- 本 change 仅做合规追认，不重写代码、不调整 fallback 策略、不改工具签名（与 design.md Decision 2 一致）。
- spec MODIFIED 保留原 Requirement 名作为前缀（「分钟 K 线必须显式声明权限敏感性」→「⋯⋯与上游依赖最低版本」），不破坏 `kline-history` 整体结构（与 design.md Decision 1 一致）。
- upstream-alignment 用反推方式产出，明确标注「缺现场证据」，不冒充正向流程的验收（与 design.md Decision 3 + Risk 段一致）。
- 不在本 retroactive 中触发任何独立的代码修改或后续 change（spec drift 推到 backlog，与 design.md Open Questions 一致）。
- 所有 retroactive 材料引用阶段 0 的 OpenSpec 治理 + 阶段 1 的 kline-history capability，符合 governance「项目特有 artifact 必须沉淀为模板」要求。

## 未测试项与风险

- 未真实调用 `bs.query_history_k_data_plus()` 验证返回字段：reTroactive 用代码事实（`provider/baostock/kline/minute.py` 的字段列表与转换逻辑）反推。若日后发现字段差异，触发独立 baostock provider 验收 change。
- 未实测「baostock 服务再次迁移时 service 层抛 DataFetchError」的端到端行为：受限于无法 mock 服务停服，靠 c010fe9 的事故复盘材料背书。
- 未实测 tushare `stk_mins` 接口的兼容性：本 change 明确不接入，但若用户开启 tushare 分钟权限，项目目前无 fallback 链可用，需要单独 change 评估。

## Spec Drift

**Drift 1（待跟进）**：本 change MODIFIED 后的 Requirement 要求「服务地址变更后 service 抛出的 `DataFetchError` MUST 携带 baostock 版本与服务地址提示，便于排查」，但当前 `provider/baostock/kline/minute.py` 的 `DataFetchError` 仅传递 baostock 原始 `error_msg`，未显式带版本号与服务地址。  
**处理**：不在本 retroactive 中修代码（与本 change 纪律一致）。已记录到 backlog，由独立后续 change（建议 slug：`enhance-baostock-error-context`）处理。

无其他 drift。

## 上游未对齐项

- baostock 0.9.1 的「服务地址迁移」是上游已发生事实，本 change 已在 spec 与 upstream-alignment 中显式记录；后续若 baostock 进一步限制免费访问或修改接口签名，需触发新一轮上游对齐 change。
- tushare `stk_mins` 接口未做对齐：本 change 不接入 tushare 分钟，若日后接入需补 upstream-alignment（按七维度对照模板填）。
