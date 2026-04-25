<!-- 用本 change 落地的 acceptance 模板自我验证。 -->

## 验收结论

变更 `restore-openspec-governance` 已完成实现和验证。`openspec/config.yaml` 现已覆盖 propose→apply→verify→archive 完整生命周期 rules；`openspec/templates/` 已落地 `acceptance.template.md` 与 `upstream-alignment.template.md` 两份项目特有模板；`CLAUDE.md` 已新增「OpenSpec 流程」章节并显式声明 OpenSpec 与 `.claude/skills/tool-acceptance` 是同一验收流程的两种描述。本 change 不修改任何 src/ 下 Python 代码。

## Completeness

按 6 条 spec Requirement 逐条核对：

- 已实现「OpenSpec change 必须覆盖完整生命周期 rules」：`openspec/config.yaml` 现含 7 段 rules（proposal/specs/design/tasks/apply/verify/archive），其中 apply/verify/archive 各至少 4 条规则。
- 已实现「apply 阶段必须强制实施纪律」：`config.yaml` apply 段包含「按 tasks.md 顺序」「每组任务跑测试」「drift 时先同步 markdown」「显式引用 .claude/rules/finance-coding.md 接口对接铁律」「provider/service/CLI/HTTP/MCP/Web 修改必须配测试或显式记录」5 条。
- 已实现「verify 阶段必须按 Completeness/Correctness/Coherence 三维输出」：`config.yaml` verify 段约束 acceptance.md 三章节齐全 + 三类风险显式列出 + Correctness 列测试命令清单 + 涉及前端必用 Playwright；本文件作为示范用例已遵循。
- 已实现「archive 阶段必须保留固定 artifact 清单」：`config.yaml` archive 段约束 acceptance.md 必备、新数据源 change 必备 upstream-alignment.md（七维度）、spec 与代码必须一致、必须使用 templates 目录模板。
- 已实现「项目特有 artifact 必须沉淀为模板」：`openspec/templates/acceptance.template.md` 与 `openspec/templates/upstream-alignment.template.md` 已落地，章节覆盖参考实现的全部 H2，并各带一行用法注释。
- 已实现「OpenSpec 与 tool-acceptance skill 关系必须显式说明」：`CLAUDE.md` 新增「OpenSpec 流程」章节 + 4 阶段表格 + 8 步标准流程清单。

## Correctness

已执行并通过：

- `openspec validate restore-openspec-governance --strict` → `Change 'restore-openspec-governance' is valid`
- `python3 -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"` → YAML 语法合法
- `openspec status --change restore-openspec-governance --json` → `isComplete: true`，proposal/specs/design/tasks 4 个 artifact 均 done
- 模板 H2 章节比对：`grep -E "^##" openspec/templates/acceptance.template.md` 与 archive/2026-04-15 的 acceptance.md 章节对比，模板 7 章覆盖参考 6 章 + 按 spec 新增「上游未对齐项」
- 模板 H2 章节比对：`grep -E "^##" openspec/templates/upstream-alignment.template.md` 含数据维度小节模板 + 结论段，覆盖参考实现的形态
- 模板首行注释比对：两份模板首行均为 `<!-- 用法：... -->`，可识别

未运行 pytest，因本 change 不动 src/ 代码。

未做 Playwright 验证，因本 change 不涉及前端。

## Coherence

- OpenSpec 仍用官方 `spec-driven` schema，未 fork（与 design.md Decision 1 一致）。
- `.claude/rules/finance-coding.md` 与 `.claude/skills/tool-acceptance` 仍是单一事实来源，OpenSpec rules 通过引用而非复制集成（与 design.md Decision 2 一致）。
- `openspec/templates/` 与官方 schema 默认 templates（`/opt/homebrew/lib/.../spec-driven/templates/`）解耦（与 design.md Decision 4 一致）。
- 新增 rules 仅描述「必须包含」边界，不规定章节顺序、文件名以外的具体写法（与 spec Scenario「rules 仅定义边界不规定具体写法」一致）。
- 历史 archived change（2026-04-10、2026-04-15）未被修改，向后兼容（与 proposal「不动现有 archived change」一致）。

## 未测试项与风险

- 未实测「archive rules 阻止缺 acceptance.md 的归档」场景：当前 OpenSpec CLI 不感知项目本地 rules，rules 是给人 + AI 看的约束，靠 review 纪律执行。后续若需机械化守护，可加 pre-commit hook 检查 `openspec archive` 前的 acceptance.md 存在性。
- 未实测「涉及新数据源的 change 强制 upstream-alignment.md」场景：理由同上，待阶段 2 回填 4 个 retroactive change 时实战验证 rules 的可操作性。
- 未实测模板被新 change 复制后是否能完整填写：将在阶段 1 `consolidate-kline-history-specs` 与阶段 2 retroactive change 中验证。

## Spec Drift

无。spec 6 条 Requirement 全部在 config.yaml / templates / CLAUDE.md 中找到对应实现证据，未发现实现与 spec 偏离。

## 上游未对齐项

无。本 change 不涉及任何上游金融数据接口。
