---
name: tool-acceptance
description: 在 FinanceData 中验收单个接口或 tool 时使用。适用于用户要求“验收某个接口”“签收某个 tool”“做完整链路验收”的场景。该技能要求先阅读完整链路，再按 provider、service、CLI、HTTP API、MCP、Web 前端逐层验收，并输出正式验收报告与签收结论。
---

# Tool Acceptance

用于 FinanceData 的单接口验收。

只要用户要你验收、签收、复验、补验某个 `tool_get_*` 接口，就使用这个 skill。

## 何时使用

- 用户要求验收某个接口
- 用户要求判断某个 tool 是否可以签收
- 用户要求补做 `CLI / HTTP / MCP / Web` 任一层的验收
- 用户要求对 provider/service/交付层问题做正式复验

## 不适用

- 只是修一个 bug，但没有要求正式验收
- 只是解释代码逻辑，没有要求验收结论
- 只是做 OpenSpec 提案或实现，不要求形成验收报告

## 工作流

按下面顺序执行，不能跳步骤：

1. 阅读该接口完整链路代码
2. 输出验收方案和计划
3. 验证上游官方文档与原始接口
4. 验收 provider
5. 验收 service
6. 验收 CLI
7. 验收 HTTP API
8. 验收 MCP
9. 用 Playwright 验收 Web 前端页面与渲染
10. 输出正式验收报告和签收结论

执行细节见 [references/checklist.md](references/checklist.md)。

## 硬规则

- 先读完整链路，再开始验收，不要边跑边猜。
- 先给出”验收方案和计划”，再执行。
- 只要遇到 provider 语义、字段、单位、时间窗口问题，必须先：
  1. 查官方文档
  2. 调用原始接口
  3. 再判断 provider 或 service 哪层有问题
- 不能只根据项目代码推断上游语义。
- `CLI`、`HTTP API`、`MCP`、`Web 前端` 都属于正式验收项。
- `Web` 验收必须看页面渲染结果，不能只看接口 200。
- 要明确区分：
  - 上游问题
  - 环境问题
  - provider 适配问题
  - service 统一语义问题
  - 交付层（契约一致性）问题

### 语义传播规则（关键）

各层是串联依赖，不是独立评分：

```
provider → service → CLI / HTTP API / MCP / Web
```

**核心原则：底层语义错误自动传播到所有上层。**

- 如果 provider 有语义问题（单位错误、字段不一致），所有依赖它的上层自动”不通过”，因为上层只是透传数据，无法修正底层错误。
- **”能调通” ≠ “通过”**。每层的验收标准是”数据语义正确”，不是”HTTP 200”或”页面能渲染”。
- **”通过”的定义**：该层返回的数据在字段语义、单位、值域上都正确，且对外暴露的契约（docstring、metadata、参数说明）与实际实现一致。
- **契约一致性也是验收项**：ToolSpec metadata 的 `source_priority`、MCP docstring 的数据源描述、CLI describe 的输出，都必须与实际 service 实现一致。不一致则该层不通过。

判定传播示例：

```
provider: 不通过 (reg_capital 单位错误)
  → service: 不通过 (透传了错误数据)
    → CLI: 不通过      (返回了错误数据)
    → HTTP API: 不通过  (返回了错误数据)
    → MCP: 不通过      (返回了错误数据)
    → Web: 不通过      (渲染了错误数据)
```

只有底层问题已修复，上层才有资格独立判定通过。

### 跨源一致性门禁（签收前置条件）

多源接口签收前，必须满足：

1. **字段集完全对齐**：所有 provider 必须返回完全相同的字段集。如果某字段只有一个源有，要么另一个源补上映射，要么从所有源删除。不允许带着字段缺失差异签收。
2. **Health consistency = "一致"**：dashboard 健康监控的 consistency 必须显示"一致"（0 差异）。有差异则不签收。
3. **修复后必须重新探测**：修了 provider 代码后，必须重新执行 health probe 验证 consistency 结果，不能只看代码判定通过。用 CLI `finance-data health <tool>` 或 dashboard"探测此接口"按钮。

单源接口不适用此规则，但需在报告中明确写出"当前单源，无跨源一致性要求"。

## 项目约束

- `CLI` 和 `MCP` 面向使用方，默认以 `service` 视角验收。
- `Web` 是管理后台，除了 service 可用性，还要看 provider 健康度和页面渲染。
- 验收报告必须使用中文。
- 报告结构和阶段结论必须固定，避免每次漂移。

## 需要读取的文件

- 开始执行前，读取 [references/checklist.md](references/checklist.md)
- 输出最终结论前，读取 [references/report-template.md](references/report-template.md)

## Gotchas

- 不要把局部验证当成最终验收。
- 不要因为某一层能返回数据，就忽略上游定义没对齐。
- 不要把“功能可用”和“可签收”混为一谈。
- Playwright 验收时，必须覆盖真实页面交互、提交、结果渲染，必要时也要覆盖错误提示。
- 如果某层因为环境未满足而无法执行，要在报告里明确写成“未执行”而不是“通过”。
