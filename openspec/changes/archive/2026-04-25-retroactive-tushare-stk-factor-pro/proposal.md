# RETROACTIVE — 历史合规化 change

> 本 change 为 1e65aba（2026-04-16，feat: 接入 3 个 tushare 接口）的 retroactive 制品，仅用于补齐 OpenSpec 合规材料，不修改任何代码。

## Why

1e65aba commit 在 OpenSpec 流程外引入了 3 个 tushare 接口和 2 个新 domain：

- **technical / `tool_get_stock_factor_pro_history`**（tushare `stk_factor_pro`）：技术因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI/估值/量价），单股票或日期范围，需 5000 积分权限，单次最多 10000 条。
- **fund_flow / `tool_get_dc_board_moneyflow_history`**（tushare `moneyflow_ind_dc`）：东财概念 / 行业 / 地域板块资金流向，T+1 17:00 更新。
- **fund_flow / `tool_get_dc_market_moneyflow_history`**（tushare `moneyflow_mkt_dc`）：大盘资金流向（沪深整体），T+1 17:00 更新。

该 commit 同时在 `.claude/rules/finance-coding.md` 中新增了「接口对接铁律」（真实调用 API 验证字段名、打印样本验证单位、端到端调用关键字段非零），是项目编码规范的重要里程碑 —— 但 commit 本身并未落地任何 OpenSpec 制品。

阶段 0 的 `openspec-governance` capability 第 2 条 Requirement 要求「apply 阶段必须遵循接口对接铁律 + apply rules MUST 指向 .claude/rules/finance-coding.md 的接口对接铁律章节」，本 retroactive 既追认这 3 个接口的接入，也回顾「接口对接铁律」这一规范引入的合理性。

## What Changes

- 新增 `openspec/changes/archive/2026-04-25-retroactive-tushare-stk-factor-pro/` 历史合规归档：proposal / design / tasks / acceptance / upstream-alignment。
- 新增两个 capability spec：`technical-factors`（覆盖 `tool_get_stock_factor_pro_history`）与 `fund-flow`（覆盖板块 / 大盘资金流两个工具）。
- 不修改任何 src/ 代码、不修改任何 provider 实现、不调整工具签名。
- 非目标：不重新评估 tushare 5000 积分门槛是否合适、不引入 fallback provider、不改变 fund_flow 的板块类型 choices。
- 兼容性：纯文档动作，运行时零影响。
- 上线风险：无。

## Capabilities

### New Capabilities
- `technical-factors`: 个股技术因子能力的行为契约，覆盖 MA/MACD/KDJ/RSI/BOLL/CCI 等技术指标 + PE/PB/换手率 / 总市值 / 流通市值等估值字段，定义工具暴露、上游对齐（tushare stk_factor_pro）、积分权限要求、单位与字段语义。
- `fund-flow`: 东财资金流向能力的行为契约，覆盖板块（概念 / 行业 / 地域）资金流与大盘资金流两类，定义工具暴露、上游对齐（tushare moneyflow_ind_dc / moneyflow_mkt_dc）、字段含义、更新时效。

### Modified Capabilities
- 无。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：无。
- 历史 commit 追溯：1e65aba（2026-04-16，含 19 个文件变化、789 行新增）。
- 受影响 spec：新增 `openspec/specs/technical-factors/` 与 `openspec/specs/fund-flow/`。
- 依赖：复用阶段 0 落地的 OpenSpec 治理 + 模板；不依赖 `kline-history`。
