# openspec-governance Specification

## Purpose
TBD - created by archiving change restore-openspec-governance. Update Purpose after archive.
## Requirements
### Requirement: OpenSpec change 必须覆盖完整生命周期 rules
系统 MUST 在 `openspec/config.yaml` 中显式定义 proposal、specs、design、tasks、apply、verify、archive 七段 rules。其中 apply、verify、archive 三段 MUST 至少包含一条规则，不得为空。

#### Scenario: config.yaml 缺段会被识别
- **GIVEN** `openspec/config.yaml` 中缺失 apply、verify 或 archive 任意一段 rules
- **WHEN** 维护方运行任何 OpenSpec 治理校验
- **THEN** 校验 MUST 报告该段缺失
- **AND** 新 change 不应被允许进入 archive

#### Scenario: rules 仅定义边界不规定具体写法
- **GIVEN** 某段 rules 描述了某项产物必须包含的内容
- **WHEN** 后续 change 编写该产物
- **THEN** rules MUST 只约束「必须包含」的边界
- **AND** 不得规定该产物的章节顺序、文件名以外的具体写法

### Requirement: apply 阶段必须强制实施纪律
系统 MUST 在 apply rules 中显式约束三件事：按 tasks.md 顺序执行、每完成一组任务运行相关测试、实现偏离 spec 或 design 时先同步 markdown 制品再继续。

#### Scenario: 实现与 spec 偏离时的处理
- **GIVEN** 维护方在 apply 阶段发现实现与 spec 或 design 不一致
- **WHEN** 维护方决定继续 apply
- **THEN** 维护方 MUST 先更新 spec 或 design，再继续实现
- **AND** 不允许在 archive 时再补做该同步

#### Scenario: 接口对接铁律必须被引用
- **GIVEN** 一个 change 涉及上游金融数据接口接入
- **WHEN** apply 阶段开始
- **THEN** 维护方 MUST 遵循「真实调用 API 验证字段名」「打印样本行验证单位」「端到端调用关键字段非零」三条铁律
- **AND** apply rules MUST 指向 `.claude/rules/finance-coding.md` 的「接口对接铁律」章节

### Requirement: verify 阶段必须按 Completeness/Correctness/Coherence 三维输出
系统 MUST 在 verify rules 中要求 acceptance.md 至少包含三个章节：Completeness、Correctness、Coherence。同时 MUST 要求显式列出未测试场景、spec drift、上游未对齐项三类风险。

#### Scenario: acceptance.md 必须三维齐全
- **GIVEN** 一个 change 进入 verify 阶段
- **WHEN** 维护方编写 acceptance.md
- **THEN** acceptance.md MUST 至少包含 Completeness、Correctness、Coherence 三个章节
- **AND** 每个章节 MUST 给出具体证据，不允许只写「已完成」

#### Scenario: 风险必须显式记录
- **GIVEN** 一个 change 完成实现且开始 verify
- **WHEN** 维护方编写 acceptance.md
- **THEN** acceptance.md MUST 显式列出未测试场景、spec drift、上游未对齐项
- **AND** 即使为空也 MUST 显式声明「无」

### Requirement: archive 阶段必须保留固定 artifact 清单
系统 MUST 在 archive rules 中要求每个归档 change 都带 `acceptance.md`。涉及上游金融数据源的 change MUST 额外带 `upstream-alignment.md`。

#### Scenario: 缺 acceptance.md 不允许归档
- **GIVEN** 一个 change 即将运行 `openspec archive`
- **WHEN** 该 change 目录下没有 `acceptance.md`
- **THEN** archive rules MUST 阻止归档
- **AND** 维护方 MUST 先补齐 acceptance.md

#### Scenario: 涉及新数据源时强制 upstream-alignment
- **GIVEN** 一个 change 在 proposal 中声明涉及新数据源或新上游接口
- **WHEN** 该 change 进入 archive
- **THEN** 该 change MUST 提供 `upstream-alignment.md`
- **AND** 该 artifact MUST 给出官方文档入口、字段映射、单位、更新时间和状态

### Requirement: 项目特有 artifact 必须沉淀为模板
系统 MUST 在 `openspec/templates/` 下提供 `acceptance.template.md` 与 `upstream-alignment.template.md`，作为新 change 编写这两类 artifact 的起点。

#### Scenario: 模板提供章节骨架
- **GIVEN** 维护方开始编写 acceptance.md 或 upstream-alignment.md
- **WHEN** 维护方查阅 `openspec/templates/`
- **THEN** 模板 MUST 提供本 spec 要求的全部章节占位
- **AND** 模板 MUST 给出至少一行说明文字解释如何填写

#### Scenario: 模板与现有 archive 一致
- **GIVEN** 模板已落地
- **WHEN** 维护方比对模板与 `archive/2026-04-15-unify-delivery-tool-specs/acceptance.md` 或 `archive/2026-04-10-split-kline-history-by-period/upstream-alignment.md`
- **THEN** 模板 MUST 至少覆盖该参考实现的所有顶级章节

### Requirement: OpenSpec 与 tool-acceptance skill 关系必须显式说明
系统 MUST 在项目入口文档（CLAUDE.md 或 README.md）中说明：OpenSpec verify 与 `.claude/skills/tool-acceptance` 是同一验收流程的两种描述，acceptance.md 是该流程的归档产物。

#### Scenario: 文档明确两套流程的关系
- **GIVEN** 新人首次接触本项目的 change 流程
- **WHEN** 阅读 CLAUDE.md 或 README.md
- **THEN** 文档 MUST 给出「先 propose、再写 spec、再 apply、再用 tool-acceptance 完成验收并写入 acceptance.md、最后 archive」的标准顺序
- **AND** 不允许出现 OpenSpec 流程与 tool-acceptance skill 互相独立的描述

