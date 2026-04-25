## Context

本 change 是对 1e65aba（2026-04-16）的 retroactive 合规。该 commit 引入了 3 个 tushare 接口和 2 个新 domain（technical / fund_flow），涉及 19 个文件、789 行新增代码：

- `interface/technical/factor.py` + `interface/fund_flow/{board.py, market.py}`：3 个 dataclass + Protocol。
- `provider/tushare/technical/factor.py` + `provider/tushare/fund_flow/{board.py, market.py}`：3 个 provider 实现。
- `service/{technical.py, fund_flow.py}`：2 个 service dispatcher。
- `tool_specs/registry.py` 新增 3 个 ToolSpec。
- `mcp/server.py` 新增 3 个 `@mcp.tool()`。
- `client.py` 新增 `stock_factor()` / `board_moneyflow()` / `market_moneyflow()`。
- `frontend/src/pages/HealthCheck.tsx` 新增 domain labels。
- `.claude/rules/finance-coding.md` 新增「接口对接铁律」（这是项目编码规范的重要里程碑）。

阶段 0 的 governance 第 2 条 Requirement 已要求「apply 阶段必须遵循接口对接铁律」，本 retroactive 既追认 3 个接口的接入，也回顾「接口对接铁律」作为规范的合理性。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec capability | `technical-factors`、`fund-flow`（新增） | ADDED Requirements |
| 历史 commit | 1e65aba | 引用 |
| 实际接入代码 | 19 个文件（见 commit stat） | 不修改 |
| 编码规范沉淀 | `.claude/rules/finance-coding.md` 接口对接铁律 | 引用，不修改 |

## Goals / Non-Goals

**Goals:**
- 把 1e65aba 的 3 个 tool 接入沉淀为 OpenSpec 可追溯材料：proposal / design / tasks / upstream-alignment / acceptance。
- 新建 `technical-factors` 与 `fund-flow` 两个 capability，为未来同 domain 接入提供结构基础。
- 在 spec 中显式声明 tushare 5000 积分门槛、单次 10000 条限制、单源无 fallback 的事实约束。

**Non-Goals:**
- 不修改任何 src/ 代码、不调整 tool 签名、不引入新 fallback。
- 不重新评估 tushare 是否合适、不评估积分门槛的可达性。
- 不接入 akshare 等价资金流接口（外部依赖，独立 change 评估）。

## Decisions

### 1. 拆为两个 capability：technical-factors 与 fund-flow

**选项**：
- A. 合并为一个 `tushare-extra` capability。
- B. 按 domain 拆为 `technical-factors` 与 `fund-flow` 两个 capability。

**选择 B**。

**理由**：
- A 按数据源划分 capability，违反 SDD「按行为契约划分 capability」原则。
- B 与项目现有 14 个 domain 体系对齐（见 CLAUDE.md），便于未来按 domain 扩展。
- 板块资金流 + 大盘资金流是同一 domain（fund_flow）的两类业务，合在一起有内聚；技术因子是独立 domain（technical），应单独 capability。
- 两个 capability 总计 9 条 Requirement，平均每 capability 4-5 条，颗粒度合适。

### 2. 资金流的两个 tool 共用一个 capability，每 tool 一组 Requirement

**理由**：
- 板块资金流（`tool_get_dc_board_moneyflow_history`）与大盘资金流（`tool_get_dc_market_moneyflow_history`）是同一 domain，共享上游对齐、单位换算、更新时效、单源约束。
- 在 capability 内用「板块资金流必须⋯」「大盘资金流必须⋯」分开两条 Requirement 声明独立暴露，再用共享 Requirement 覆盖通用约束（上游对齐、单位、时效、单源）。

### 3. 不在本 change 重构 service 层做单次 10000 条窗口拆分

**背景**：tushare `stk_factor_pro` 单次最多 10000 条；如果调用方的查询窗口超出，当前 service 层不会自动拆分，会得到截断数据。

**选项**：
- A. 本 retroactive 顺便加窗口拆分逻辑。
- B. 本 retroactive 仅记录该限制为 spec drift（spec 要求「超限抛错而非静默截断」，但实现可能未抛错），交独立后续 change 处理。

**选择 B**。

**理由**：
- A 违反 retroactive 「不修代码」原则。
- B 通过 acceptance.md 显式记录 drift，确保问题不被遗忘；后续可开 `enhance-stk-factor-pro-window-pagination` change 实现自动分页。

### 4. 「接口对接铁律」不在本 change 重新沉淀

**理由**：
- 阶段 0 的 governance Requirement 2「apply 阶段必须强制实施纪律」已显式引用 `.claude/rules/finance-coding.md` 的「接口对接铁律」章节。
- 1e65aba 引入的铁律内容已是当前项目活的规范，本 retroactive 仅引用，不重定义。

## Source-of-Truth 映射（实施 → spec）

| 实施事实 | 来源 | 对应 Requirement |
| --- | --- | --- |
| 3 个独立 MCP tool（factor / board / market） | `tool_specs/registry.py` 1e65aba diff | technical-factors「按单一工具暴露」+ fund-flow「板块按单一工具」「大盘按单一工具」 |
| 5000 积分门槛 + 10000 条限制 | ToolSpec.metadata.limitations | technical-factors「单源 tushare 限制必须显式声明」 |
| 单源无 fallback | service/technical.py + service/fund_flow.py 的 dispatcher 仅含 1 个 provider | technical-factors「单源声明」+ fund-flow「单源声明」 |
| 字段单位换算（vol×100 / amount×1000 / 万元×10000） | provider/tushare/{technical,fund_flow}/* 的 _safe() * N 操作 | technical-factors「字段单位必须经 provider 显式换算」+ fund-flow「字段单位必须经 provider 显式换算」 |
| 字段名前后缀去除（ma_bfq_5 → ma5 等） | provider/tushare/technical/factor.py 行 86-110 | technical-factors「上游对齐覆盖技术指标字段名规则」 |
| content_type 三选一（概念 / 行业 / 地域） | tool_specs/registry.py choices 字段 | fund-flow「按 content_type 过滤」Scenario |
| T+1 17:00 更新时效 | ToolSpec.metadata.update_timing | fund-flow「资金流必须显式声明数据更新时效」 |

## Risks / Trade-offs

- [Risk] spec 要求超限时 `DataFetchError` 抛出，但 1e65aba 实现可能在数据为空时抛 `data` kind，未必区分「超限」vs「无数据」。  
  → Mitigation: 在 acceptance.md 中显式记录该 drift；交独立 change 优化错误归类。

- [Risk] spec 要求 `net_amount_rate` 是百分比，但 provider 实现是否真的换算成百分比未在本 change 验证（基于 commit diff 推测）。  
  → Mitigation: 在 acceptance.md 标记为「未实测项」，建议后续接入 fund_flow 测试时验证。

- [Risk] 板块资金流 / 大盘资金流的 akshare 等价接口未对齐。  
  → Mitigation: 不在本 retroactive 评估，留作 backlog（独立 change 决策）。

## Migration Plan

1. 创建 5 份制品（proposal / design / tasks / upstream-alignment / acceptance）。
2. 创建 2 个 ADDED spec：`technical-factors` 与 `fund-flow`。
3. `openspec validate retroactive-tushare-stk-factor-pro --strict` 通过。
4. 写 acceptance.md 记录 spec drift 与未实测项。
5. `openspec archive retroactive-tushare-stk-factor-pro -y`，自动落地两个新 capability。

回滚策略：纯文档动作，回滚为 `git revert` 即可。

## Open Questions

- 是否要把 `tool_get_stock_factor_pro_history` 名字短化为 `tool_get_stock_factor_history`？  
  → 阶段 5 命名统一时一并评估，不在本 retroactive 决策。
- akshare 是否有等价资金流接口？  
  → 不在本 retroactive 范围。
