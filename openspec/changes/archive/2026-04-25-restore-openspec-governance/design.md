## Context

OpenSpec 在 FinanceData 项目中已运行两轮 change（2026-04-10 拆分 K 线、2026-04-15 统一交付工具契约），但治理层缺口直接导致 4-15 之后 15 个 commits 全部脱离 OpenSpec：

- `config.yaml` 的 rules 段只覆盖 propose 阶段（proposal/specs/design/tasks），实施与验收阶段无任何强约束。
- 两次 archive 各自手写了 `upstream-alignment.md` 和 `acceptance.md`，但这两份 artifact 没有沉淀为 schema 或模板，新 change 不会自动复用。
- `.claude/rules/finance-coding.md` 与 `.claude/skills/tool-acceptance` 在 Claude 配置侧定义了「接口对接铁律」与「逐层验收」要求，但与 OpenSpec rules 互不引用，新人写 change 时无所适从。

参考 wiki `[[openspec-framework]]` 的「三层约束」：spec 结构 + config.yaml 规则 + verify 门禁。其中规则与门禁是 FinanceData 当前的短板。本设计选择**不 fork OpenSpec schema**，原因详见 Decision 1。

## Goals / Non-Goals

**Goals:**
- 让 `config.yaml` 覆盖 propose→apply→verify→archive 完整生命周期。
- 把项目特有的 acceptance / upstream-alignment 两类 artifact 形态用模板锁定。
- 把分散在 Claude 配置中的「接口对接铁律」与「逐层验收」要求显式引入 OpenSpec rules。
- 在 CLAUDE.md 写清 OpenSpec 与 tool-acceptance skill 的关系。

**Non-Goals:**
- 不修改任何 src/ 下 Python 代码。
- 不动现有 archived change 的内容。
- 不 fork OpenSpec schema、不增加新的 artifact 类型到 schema 层（理由见 Decision 1）。
- 不引入新工具或自动化校验脚本。

## Decisions

### 1. 不 fork OpenSpec schema，先用 config.yaml rules 强约束

**选项**：
- A. 跟 PlaybookOS 一样用 `openspec schema fork` 把 acceptance / upstream-alignment 注册成正式 artifact。
- B. 保持默认 `spec-driven` schema，把要求写进 `config.yaml` 的 rules 段。

**选择 B**。

**理由**：
- PlaybookOS 的 7-artifact 链对单人短周期项目偏重，schema fork 会引入「每次 openspec new 都要补齐所有 artifact」的强制成本。
- FinanceData 的 acceptance / upstream-alignment 是「条件性 artifact」（仅特定 change 需要），用 rules 描述「何时必须提供」更精准。
- 短期收益相同：rules 写明「archive 必须有 acceptance.md / 涉及新数据源必须有 upstream-alignment.md」即可达到守护效果。
- 后退路径开放：若未来 change 数量大幅增加（比如 20+ archived），再考虑升级到 schema fork。

### 2. apply rules 引用而非复制「接口对接铁律」

**理由**：
- `.claude/rules/finance-coding.md` 是单一事实来源，OpenSpec rules 直接引用避免双写漂移。
- 引用形式：rules 中写「apply 阶段必须遵循 `.claude/rules/finance-coding.md` 中的『接口对接铁律』章节」。
- 副作用：当 finance-coding.md 更新时，OpenSpec rules 自动跟随，不需要同步两处。

### 3. verify rules 锁定 Completeness/Correctness/Coherence 三维结构

**理由**：
- archive/2026-04-15 的 acceptance.md 已经验证了三维结构的可用性。
- 三维结构对应 wiki `[[openspec-framework]]` verify 输出口径中的 PASS/WARNING/FAIL + Untested + Drift。
- 强制三维 + 风险三类（未测试 / drift / 上游未对齐）=「显式列出风险」，符合 wiki 的最佳实践。

### 4. 模板放 `openspec/templates/` 而非 schema 内置 templates

**理由**：
- 项目特有模板与官方 schema 默认模板（`/opt/homebrew/lib/.../spec-driven/templates/`）解耦。
- `openspec/templates/` 是约定俗成的项目本地模板路径，未来若 fork schema 可平滑迁移。
- 不需要修改 OpenSpec CLI 的模板解析逻辑（CLI 只会用 schema 默认 + custom path 覆盖）。

## Source-of-Truth 映射

| 治理项 | Source of truth | 引用方式 |
|---|---|---|
| 接口对接铁律 | `.claude/rules/finance-coding.md` | apply rules 引用 |
| 逐层验收流程 | `.claude/skills/tool-acceptance` | verify rules 引用 |
| acceptance 形态 | `openspec/templates/acceptance.template.md` | verify rules 引用 + archive 时复制 |
| upstream-alignment 形态 | `openspec/templates/upstream-alignment.template.md` | apply rules 引用 + archive 时复制 |
| OpenSpec 流程总览 | `CLAUDE.md` 新增章节 | 项目根入口文档 |

## Risks / Trade-offs

- [Risk] rules 写得过死会在阶段 4-5（拆大文件、命名统一）卡住自己。  
  → Mitigation: rules 只描述「必须包含」边界，不规定章节顺序、文件名以外的具体写法（spec 中已写为 Requirement）。

- [Risk] 模板与已 archived change 的实际形态可能微妙不一致。  
  → Mitigation: 模板严格拷自 archive 实例，并在 spec 中要求「模板 MUST 至少覆盖该参考实现的所有顶级章节」。

- [Risk] OpenSpec CLI 不感知项目本地模板，新建 change 时不会自动拉取。  
  → Mitigation: 在 CLAUDE.md 流程章节中明确写「`openspec new change <slug>` 之后手动从 templates 复制对应 artifact」。可接受的额外摩擦。

- [Risk] config.yaml rules 写英文 vs 中文不一致。  
  → Mitigation: 当前 rules 已全中文，新增段沿用中文风格。

## Migration Plan

1. 修改 `openspec/config.yaml`：在 rules 段补 apply、verify、archive 三段。
2. 创建 `openspec/templates/acceptance.template.md`，从 `archive/2026-04-15-unify-delivery-tool-specs/acceptance.md` 拷贝并替换具体内容为占位说明。
3. 创建 `openspec/templates/upstream-alignment.template.md`，从 `archive/2026-04-10-split-kline-history-by-period/upstream-alignment.md` 拷贝并改造为通用模板。
4. 修改 `CLAUDE.md`：新增「OpenSpec 流程」章节，描述 propose→apply→verify→archive 与 tool-acceptance skill 的关系。
5. 运行 `openspec validate restore-openspec-governance --strict` 确认 spec/design/tasks 自身合法。
6. 完成 acceptance.md，使用本 change 落地的 acceptance 模板做自我验证。

回滚策略：本 change 仅新增配置与文档，不动代码，回滚为 `git revert` 即可。

## Open Questions

- 是否需要 pre-commit / CI 钩子检查「即将 archive 的 change 必须带 acceptance.md」？  
  → 暂不引入，先靠 rules 与 review 纪律，等阶段 2 回填 4 个 retroactive change 后评估。
- `openspec/templates/` 的命名是否需要带版本号便于演进？  
  → 暂不带，git history 即版本。
