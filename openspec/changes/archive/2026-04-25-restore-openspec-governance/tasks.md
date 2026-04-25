## 1. 扩展 config.yaml 的 rules 段

- [x] 1.1 在 `openspec/config.yaml` 的 rules 段新增 `apply` 子段：约束按 tasks.md 顺序执行、每组任务跑测试、drift 时先同步 markdown，并显式引用 `.claude/rules/finance-coding.md` 的「接口对接铁律」。验证：`openspec validate restore-openspec-governance --strict` 通过；config.yaml 可被 `openspec` 解析（无 YAML 语法错误）。
- [x] 1.2 新增 `verify` 子段：要求 acceptance.md 至少含 Completeness、Correctness、Coherence 三章节，并显式列出未测试场景、spec drift、上游未对齐三类风险。验证：人工对照 spec Requirement「verify 阶段必须按 Completeness/Correctness/Coherence 三维输出」逐句覆盖。
- [x] 1.3 新增 `archive` 子段：要求每个 change archive 时必须含 acceptance.md；涉及新数据源时必须含 upstream-alignment.md。验证：人工对照 spec Requirement「archive 阶段必须保留固定 artifact 清单」。

## 2. 落地 templates 目录

- [x] 2.1 新建 `openspec/templates/` 目录，创建 `acceptance.template.md`，章节骨架按 `archive/2026-04-15-unify-delivery-tool-specs/acceptance.md` 拷贝（验收结论 / Completeness / Correctness / Coherence / 未测试项与风险 / Spec Drift），并按 spec 要求新增「上游未对齐项」章节，章节正文改为占位说明。验证：`diff` 模板与参考实例的 H1/H2 标题覆盖关系，模板新增章节符合 spec Requirement「verify 阶段必须按 Completeness/Correctness/Coherence 三维输出」中的「显式列出三类风险」要求。
- [x] 2.2 创建 `openspec/templates/upstream-alignment.template.md`，章节骨架按 `archive/2026-04-10-split-kline-history-by-period/upstream-alignment.md` 拷贝（按数据维度的对照表 + 结论），抽离出通用版本。验证：模板包含「调用方式 / 字段 / 单位 / 复权 / 历史范围 / 更新时间 / 状态」七个对照维度的占位。
- [x] 2.3 在两份模板顶部各添加一行 `<!-- 用法：复制本文件到 changes/<slug>/ 后填写实际内容。请保留全部 H2 章节。 -->` 注释。验证：模板首行可被人识别为说明。

## 3. 更新 CLAUDE.md 的 OpenSpec 流程章节

- [x] 3.1 在 `CLAUDE.md` 中新增「OpenSpec 流程」章节，按 propose → apply → verify → archive 描述每步必做事项，并显式说明 OpenSpec verify 与 `.claude/skills/tool-acceptance` 是同一验收流程的两种描述。验证：人工 review 章节逻辑顺序与 spec Requirement「OpenSpec 与 tool-acceptance skill 关系必须显式说明」对齐。
- [x] 3.2 在该章节末尾给出 8 步「新加一个接口」的标准流程清单（与本 change 配套的路线图 End State 段对齐）。验证：清单 8 步齐全，覆盖 propose → upstream-alignment → spec → design → tasks → apply → tool-acceptance → archive。

## 4. 自我验证与归档

- [x] 4.1 运行 `openspec validate restore-openspec-governance --strict`，确认 proposal/specs/design/tasks 全部合法。验证：CLI 退出码 0。
- [x] 4.2 用本 change 落地的 acceptance 模板编写 `acceptance.md`，按 Completeness/Correctness/Coherence 三维记录本次治理变更的完成情况。验证：acceptance.md 三章节齐全 + 风险三类显式记录（即使为空也写「无」）。
- [x] 4.3 对照 spec 的 6 条 Requirement 逐一验收，确保每条都有对应 tasks 完成。验证：每条 Requirement 在 acceptance.md 的 Completeness 章节中可定位到证据。
- [x] 4.4 运行 `openspec archive restore-openspec-governance`，归档 change。验证：`openspec list --archived` 包含本 change；`openspec/specs/openspec-governance/spec.md` 出现，内容与本 change 的 spec delta 一致。
