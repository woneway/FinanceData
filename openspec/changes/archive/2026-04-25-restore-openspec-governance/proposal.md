## Why

OpenSpec 已在项目中运行两轮 change（2026-04-10、2026-04-15），但治理层存在硬伤导致后续 15 个 commits 全部脱离 OpenSpec：

- `openspec/config.yaml` 仅定义了 proposal/specs/design/tasks 四段 rules，缺 `apply` 与 `verify` 段（OpenSpec PR #887 后已支持），导致实施与验收阶段无强约束。
- 已归档的两次 change 自发产出了 `upstream-alignment.md`（2026-04-10）和 `acceptance.md`（2026-04-15），证明项目实际需要这两类 artifact，但它们没有沉淀为模板，新 change 不会自动复用。
- `.claude/rules/finance-coding.md` 中的「接口对接铁律」与 `.claude/skills/tool-acceptance` 的逐层验收要求散落在 Claude 配置中，与 OpenSpec 规则分裂，新人写 change 时不知道要遵循哪一套。

本次治理变更要求：让 `config.yaml` 覆盖完整 propose→apply→verify→archive 闭环，并以两份模板锁定项目特有的 artifact 形态。本 change 不修改任何运行时代码。

## What Changes

- 扩展 `openspec/config.yaml`：补 `apply`、`verify`、`archive` 三段 rules，迁入「接口对接铁律」与「Completeness/Correctness/Coherence 三维」要求。
- 落地 `openspec/templates/acceptance.template.md`（拷自 archive/2026-04-15）。
- 落地 `openspec/templates/upstream-alignment.template.md`（拷自 archive/2026-04-10）。
- 在 README 或 CLAUDE.md 中补一段「新 change 流程」指引，把 OpenSpec 与 tool-acceptance skill 的关系说清楚。
- 非目标：不 fork OpenSpec schema，不修改任何 src/ 下的 Python 代码，不改动现有 archived change。
- 兼容性：仅扩展 rules 与新增模板文件，对历史 change 无影响。
- 上线风险：rules 写得太死会在阶段 4-5 自卡，因此只写「必须包含」边界，不规定具体写法。

## Capabilities

### New Capabilities
- `openspec-governance`: 定义 OpenSpec change 在 FinanceData 项目中的完整生命周期约束，包含 apply 实施纪律、verify 三维验收口径、archive 强制 artifact 清单、以及 acceptance 与 upstream-alignment 两类项目特有制品的形态契约。

### Modified Capabilities
- 无。

## Impact

- 受影响代码：无。
- 受影响配置：`openspec/config.yaml`。
- 新增文件：`openspec/templates/acceptance.template.md`、`openspec/templates/upstream-alignment.template.md`。
- 受影响文档：根目录 `CLAUDE.md` 增补 OpenSpec 流程段落。
- 依赖：复用 `.claude/rules/finance-coding.md`「接口对接铁律」、`.claude/skills/tool-acceptance` 验收要求、wiki `[[openspec-framework]]` 的三层约束模型。
