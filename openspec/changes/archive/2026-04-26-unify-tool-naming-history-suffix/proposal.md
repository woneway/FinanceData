## Why

`FinanceData` Python 客户端（`client.py`）的 33 个公开方法与 MCP 48 个 tool 名称命名规则不一致，导致同一份能力在两个入口下命名感知割裂：

| 用户视角 | 客户端调用 | MCP 工具名 |
|---|---|---|
| 个股日线 | `fd.kline_daily(...)` | `tool_get_kline_daily_history` |
| 个股实时行情 | `fd.quote(...)` | `tool_get_stock_quote_realtime` |
| 个股基本信息 | `fd.stock_info(...)` | `tool_get_stock_info_snapshot` |
| 龙虎榜个股明细 | `fd.lhb_stock_detail(...)` | `tool_get_lhb_stock_detail_daily` |
| 停牌 | `fd.suspend(...)` | `tool_get_suspend_daily` |

阶段 0 governance 要求「OpenSpec change 必须覆盖完整生命周期 rules」+「项目特有 artifact 必须沉淀为模板」。命名规则是项目级契约，应在 spec 层固化。

阶段 4 落地的 `delivery-tool-spec-contract` 已定义 ToolSpec 是「工具契约真相源」+ MCP wrapper 不漂移；但**未对客户端方法名与 MCP tool 名的映射关系**作约束。本 change 把这一映射规则提升为 spec：客户端方法名 = MCP tool 全名去掉 `tool_get_` 前缀，scope 后缀（`_history` / `_realtime` / `_snapshot` / `_daily`）保留。

**Breaking 影响**：33 个公开方法重命名（如 `kline_daily` → `kline_daily_history`、`quote` → `stock_quote_realtime`）。所有旧名通过 `__getattr__` 实现 deprecated alias 保留至少 1 个 minor 版本（带 `DeprecationWarning`），确保现有用户脚本不立即失效。

## What Changes

**代码层**：
- `client.py` 33 个方法逐一重命名为「MCP tool 名去 `tool_get_` 前缀」形式。例：
  - `stock_info` → `stock_info_snapshot`
  - `kline_daily / weekly / monthly / minute` → `kline_daily_history / weekly_history / monthly_history / minute_history`
  - `quote` → `stock_quote_realtime`
  - `chip` → `chip_distribution_history`
  - `lhb_stock_detail` → `lhb_stock_detail_daily`
  - `suspend` → `suspend_daily`
  - `stock_factor` → `stock_factor_pro_history`
  - `board_moneyflow` / `market_moneyflow` → `dc_board_moneyflow_history` / `dc_market_moneyflow_history`
  - 完整映射表见 design.md。
- 新增 `__getattr__` 拦截器：用 `_DEPRECATED_ALIASES: dict[str, str]` 集中维护「旧名 → 新名」映射；用户调用 `fd.<old_name>(...)` 时发出 `DeprecationWarning` 并代理到新方法。
- `client.py` 顶部 docstring 更新：示例改用新方法名。

**文档层**：
- `CLAUDE.md` Python Library 使用示例：旧名（`fd.kline_daily / quote / capital_flow / board_member`）替换为新名（`kline_daily_history / stock_quote_realtime / capital_flow_realtime / board_member_history`）。

**测试层**：
- `tests/test_client_board.py` 用 `fd.board_member(...)` → 改为 `fd.board_member_history(...)`。
- 新增 `tests/test_client_naming.py` 守护测试：
  - 集合一致性：客户端公开方法集合（去掉私有 + alias）= MCP tool 名集合（去掉 `tool_get_`）。
  - 别名兼容性：每个 `_DEPRECATED_ALIASES` 中的旧名均可调用且发出 DeprecationWarning。

**Spec 层**：
- 新建 `client-naming` capability：定义客户端方法命名规则、deprecation 策略、守护测试要求。

**非目标**：
- 不修改 MCP tool 名称、ToolSpec 字段、service / provider / interface 任何代码。
- 不修改 `_get_service()` helper 的签名或行为。
- 不修改 client.py 方法的签名（参数与返回类型保留）。
- 不实施「自动从 MCP tool 名生成 client 方法」的反射机制（保持显式 method 定义可读性）。
- 不删除任何旧名（仅 deprecated）。

**兼容性**：
- 所有旧名仍可调用，发出 `DeprecationWarning`。
- 行为零变更（旧名通过 `__getattr__` 代理到新方法）。
- 测试 `tests/test_client_board.py` 的旧调用更新到新名，但旧名守护测试覆盖兼容性。

**上线风险**：
- 中。33 个方法重命名 + 1 处测试更新 + 1 处文档更新。
- 缓解：deprecated alias 100% 兼容；新增守护测试锁定「客户端方法名 = MCP tool 名」映射。

## Capabilities

### New Capabilities
- `client-naming`: FinanceData Python 客户端的公开方法命名规范。覆盖：方法名从 MCP tool 名派生规则、scope 后缀强制、deprecated alias 机制、守护测试约束。

### Modified Capabilities
- 无（不动 `delivery-tool-spec-contract`、`kline-history`、其他 capability）。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：`src/finance_data/client.py`（重写 33 个方法名 + 加 `__getattr__` + alias 字典）
- 受影响文档：`CLAUDE.md` 使用示例段
- 受影响测试：`tests/test_client_board.py`（更新到新名）+ 新增 `tests/test_client_naming.py`（守护）
- 不修改：所有 MCP / ToolSpec / service / provider / interface / cache / config
- 受影响 spec：新增 `client-naming` capability
- 测试影响：全量 pytest 必须 415 → 417+ passed（新增守护测试）
- 依赖：复用阶段 0 OpenSpec 治理 + 模板；与阶段 4 `delivery-tool-spec-contract` 形成「工具契约 → 客户端方法名」的契约链。
