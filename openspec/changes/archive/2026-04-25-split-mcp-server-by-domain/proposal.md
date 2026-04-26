## Why

`src/finance_data/mcp/server.py`（**1263 行**）与 `src/finance_data/tool_specs/registry.py`（**968 行**）均严重违反 `.claude/rules/common/coding-style.md` 的「文件 800 行上限」规范。两个文件分别堆放：

- server.py：48 个 `@mcp.tool()` 函数 + 38 行 service import 块
- registry.py：48 个 ToolSpec 字面量 + 5 个工厂 helper

随着接口数量增长（48 → 50+ 即将再加），每次新增接口都要在两个超大文件里 navigate，diff 评审负担重，git blame 难追溯，测试 mock 容易碰撞。

按 CLAUDE.md「四层分离 Domain-first」原则，MCP / ToolSpec 早就该按 14 个 domain 物理拆分。本 change 把两个超大文件按 domain 切片为：

- `mcp/tools/<domain>.py` × 14（每个 domain 含本域 `@mcp.tool` 定义）
- `tool_specs/registry/<domain>.py` × 14（每个域含本域 ToolSpec 字面量）

**行为零变更**：48 个 MCP tool 名称、签名、注册顺序、返回 JSON、ToolSpec 内容、`TOOL_SPEC_REGISTRY` OrderedDict 顺序全部不变。

## What Changes

**MCP 层**：
- 新建 `src/finance_data/mcp/_app.py`：FastMCP 单例 `mcp` + `_to_json` / `_invoke_tool_json` 两个 helper（从 server.py 顶部抽出）。
- 新建 `src/finance_data/mcp/tools/<domain>.py` × 14：每个 domain 持有本域 `@mcp.tool()` 函数，从 `_app` import `mcp` 与 helper，从 `service.<domain>` import service 实例。
- 重写 `src/finance_data/mcp/server.py` 为 aggregator：按固定顺序 import 14 个 tools 子模块（保证 `@mcp.tool()` 注册顺序与原 server.py 一致），re-export 全部 service 实例（兼容 `patch("finance_data.mcp.server.<service_name>.<method>")` 等测试 mock 路径）+ 仍导出 `mcp`。

**ToolSpec 层**：
- 新建 `src/finance_data/tool_specs/registry/__init__.py`：导出 `TOOL_SPEC_REGISTRY = OrderedDict(...)`，按固定顺序合并 14 个 domain registry 子模块的 specs 列表。
- 新建 `src/finance_data/tool_specs/registry/_factories.py`：把 `_param` / `_provider` / `_service` / `_probe` / `_meta` 5 个工厂 helper 集中提供（供 14 个子模块复用）。
- 新建 `src/finance_data/tool_specs/registry/<domain>.py` × 14：每个 domain 暴露 `SPECS: list[ToolSpec] = [...]`。
- 删除原 `src/finance_data/tool_specs/registry.py` 文件（迁到 `registry/` 目录）。注意：`from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` 仍能 work（因 Python 包的 `__init__.py` 即模块路径）。

**测试**：
- 不修改任何现有测试文件。`test_mcp_server.py` 4 处 `patch("finance_data.mcp.server.<service>.<method>")` 必须仍可工作 ← 由 server.py re-export 全部 service 名字保证。
- 新增 `tests/mcp/test_tools_layout.py`（守护测试）：断言 server.py 中导出的 `mcp` 注册的 48 个工具名称与 `TOOL_SPEC_REGISTRY.keys()` 完全一致且顺序一致；任一新增/重命名 tool 都能被锁定。

**非目标**：
- 不修改任何 service / provider / interface / client / cache / config 代码。
- 不修改 `delivery-tool-spec-contract` 的现有 5 条 Requirement 行为。
- 不修改 ToolSpec 字段（params / providers / probe / metadata 全保留）。
- 不调整任何 MCP tool 的参数签名、docstring、返回 JSON 结构。
- 不动 `dashboard` / `cli` / `verify` 任何代码。
- 不动 client.py（命名统一留待阶段 5）。

**兼容性**：
- 对外 API 入口完全兼容：
  - `from finance_data.mcp.server import mcp` ✓（server.py 仍导出 mcp）
  - `from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` ✓（registry/ 是包）
  - `from finance_data.tool_specs import TOOL_SPEC_REGISTRY` ✓（__init__.py 不变）
  - `patch("finance_data.mcp.server.<service>.<method>")` ✓（server.py re-export 全部 service 名字）
- 48 个 MCP tool 名称 / 签名 / docstring / 返回字段全部不变。
- `TOOL_SPEC_REGISTRY` 集合稳定（48 个），但**顺序按 14 domain 集中后会与历史源码顺序不同**（详见 design.md Decision 4）。守护测试只锁「mcp 注册顺序 = TOOL_SPEC_REGISTRY 顺序」一致性，不要求与历史一致。下游 dashboard 工具列表展示顺序可能微变，工具集合不变。

**上线风险**：
- 中。涉及 41 个文件移动 / 创建（28 个新增 + 1 个删除 + 12 个修改）。
- 缓解：守护测试先行（test_tools_layout.py 断言 48 个 tool name 顺序与 TOOL_SPEC_REGISTRY 一致），守护测试在拆分前先合入并验证当前代码通过；拆分后再跑全量 pytest 必须 412 passed。

## Capabilities

### Modified Capabilities
- `delivery-tool-spec-contract`: ADDED 1 条 Requirement「MCP tool 与 ToolSpec registry 必须按 domain 物理拆分」+ ADDED 1 条 Requirement「MCP tool 注册顺序必须与 ToolSpec registry 顺序严格一致」。这两条 Requirement 描述新的物理结构契约，作为现有 5 条行为契约的补充。

### New Capabilities
- 无。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：
  - 修改：`src/finance_data/mcp/server.py`（1263 行 → ~50 行 aggregator）
  - 删除：`src/finance_data/tool_specs/registry.py`（968 行）
  - 新增：`src/finance_data/mcp/_app.py`（~25 行）、`src/finance_data/mcp/tools/__init__.py`、`src/finance_data/mcp/tools/<domain>.py` × 14、`src/finance_data/tool_specs/registry/__init__.py`、`src/finance_data/tool_specs/registry/_factories.py`、`src/finance_data/tool_specs/registry/<domain>.py` × 14
  - 新增：`tests/mcp/test_tools_layout.py`（守护测试）
- 不修改：service / provider / interface / client / cache / config / cli / dashboard / verify
- 受影响 spec：`delivery-tool-spec-contract` ADDED 2 Req
- 测试影响：全量 pytest 必须 412 passed；新增 test_tools_layout.py 在拆分前后均绿
- 依赖：复用阶段 0 OpenSpec 治理 + 模板；遵循阶段 2.2 retroactive-tushare-stk-factor-pro 中 `delivery-tool-spec-contract` 的「MCP 工具契约不得漂移」基础约束。
