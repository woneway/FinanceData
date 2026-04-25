<!-- 用 openspec/templates/acceptance.template.md 落地。 -->
<!-- 本 change 是 retroactive，「实现」由 fe01b51 完成；本验收聚焦合规材料完整性 + 设计缺陷追认 + 字段名 breaking 显式留痕。 -->

## 验收结论

变更 `retroactive-duckdb-cache-layer` 已完成 retroactive 合规追认。fe01b51（2026-04-18）的两件结构性变更（DuckDB 缓存层 + `pct_change → pct_chg` breaking）已沉淀为 OpenSpec 可追溯材料：proposal / design / tasks / acceptance 四份制品齐全（不含 upstream-alignment 因不接入新数据源）。新建 `cache-layer`（6 条 Requirement）与 `field-naming`（3 条 Requirement）两个 capability，把混在一个 commit 里的两件变更分离声明。本 change 不修改任何 src/ 代码。识别 1 项「未测试项」（validator 未实现）和 1 项「设计缺陷追认」（commit 未拆分）。

## Completeness

- 已落地 retroactive proposal：顶部标注 RETROACTIVE，说明 fe01b51 携带两件变更（A 基础设施 + B breaking），分别用两个 capability 沉淀。
- 已落地 retroactive design：含 source-of-truth 映射表（8 行）+ 5 条 Decision（拆为两 capability / 不规定开关实现 / validator 用 SHOULD（已升级为 MUST）/ 写责任与读路径解耦 / 不追责 commit 拆分）+ 风险段。
- 已落地新 capability `cache-layer`：6 条 ADDED Requirement，覆盖默认启用与关闭开关、T-1 规则、三个 resolver 入口、tushare provider 接入模式、不绕过测试 mock、写入责任与读路径解耦。
- 已落地新 capability `field-naming`：3 条 ADDED Requirement，把 `pct_chg` 升为项目级字段命名规范、要求 breaking change 显式声明、要求 validator 守护。
- 已显式记录 fe01b51 中 4 个受影响 interface 文件（hot_rank / lhb / pool / sector_fund_flow），让下游接入方能定位 `pct_change → pct_chg` 历史 breaking。

## Correctness

已执行并通过：

- `openspec validate retroactive-duckdb-cache-layer --strict` → `Change 'retroactive-duckdb-cache-layer' is valid`
- `git show --stat fe01b51` → 确认涉及 33 个文件、375 行新增、51 行删除
- `git show fe01b51 -- src/finance_data/cache/db.py src/finance_data/cache/resolver.py` → 确认 cache 层接入文件存在
- `git show fe01b51 -- src/finance_data/interface/hot_rank/realtime.py src/finance_data/interface/lhb/history.py src/finance_data/interface/pool/history.py src/finance_data/interface/sector_fund_flow/history.py` → 确认 4 个 interface 文件含 `pct_change → pct_chg` 改动
- `cat src/finance_data/cache/resolver.py` → 确认当前 `_is_cache_enabled()` 仍读 `os.environ.get("FINANCE_DATA_CACHE")`，与 spec「可被显式关闭」一致；阶段 3 将改实现而不破坏 spec
- `cat tests/conftest.py` → 确认测试 conftest 已禁用缓存
- 历史回归：fe01b51 commit message 声明「432 passed, 0 failed」，本 change 不动代码，无需重跑测试

## Coherence

- 两个 capability 拆分严格按照「行为契约 vs 命名规范」语义边界（与 design.md Decision 1 一致）。
- cache-layer Requirement「默认启用且可被显式关闭」不规定开关具体实现形式，给阶段 3 改用 `config.toml` 留出空间（与 design.md Decision 2 一致）。
- field-naming validator Requirement 在 spec 内写为 MUST 并明确「在 validator 实现前处于『认可但未守护』状态」，由 acceptance.md 「未测试项」承接（与 design.md Decision 3 调整后一致）。
- cache 层「写责任与读路径解耦」明确写责任由独立下载脚本承担（与 aa87952 引入的 download 脚本约定一致）。
- 本 change 不在 spec 中追责 fe01b51 当时未拆 commit，仅在 design.md 「Context」段做事实陈述（与 design.md Decision 5 一致）。

## 未测试项与风险

- **validator 未实现**：field-naming「字段命名规范必须由 validator 守护」Requirement 标记为 MUST，但当前没有 CI 或 pre-commit 守护。状态为「认可但未守护」，待独立后续 change `implement-pct-chg-validator` 落地。建议实现方式：扫描 `src/`、`tools/`、`tool_specs/` 目录，正则匹配 `pct_change` 字符串（含 dataclass 字段定义、return_fields tuple、provider 输出 dict key），触发 PR 阻断。
- **未实测 cache hit / miss 真实行为**：本 change 不动代码也不跑集成测试。现有 `tests/conftest.py` 已通过禁用缓存避免测试受影响；fe01b51 commit message 声明「432 passed」。
- **未实测「FINANCE_DATA_CACHE 环境变量」与未来 config.toml 开关的兼容性**：阶段 3 自己决策。
- **未实测「T-1 规则」边界场景**：例如调用方在凌晨 0:01 请求「今天」数据，`_get_today()` 是否会与人类预期一致；该场景未在 fe01b51 测试中显式覆盖。

## Spec Drift

**Drift 0（已追认，非 spec drift）**：fe01b51 把缓存层接入与字段重命名合并到一个 commit，违反 governance「proposal 应聚焦一个逻辑意图」纪律。本 retroactive 通过拆分两个 capability 在结果上分离两件事，但事实层面 commit 已不可拆。归类为「设计缺陷追认」，不属于运行时 spec drift。

**未发现运行时 drift**：cache-layer 6 条 Requirement 与 field-naming 3 条 Requirement 全部能在 fe01b51 实现中找到对应证据；无 spec 与代码偏离。

## 上游未对齐项

无。本 change 不接入任何上游金融数据源，纯基础设施 + 字段命名规范。
