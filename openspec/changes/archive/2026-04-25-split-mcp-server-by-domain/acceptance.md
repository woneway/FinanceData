<!-- 用 openspec/templates/acceptance.template.md 落地。 -->

## 验收结论

变更 `split-mcp-server-by-domain` 已完成实现和验证。两个超大文件（`mcp/server.py` 1263 行 + `tool_specs/registry.py` 968 行）按 14 个 domain 物理拆分为：
- `mcp/_app.py` (29 行) + `mcp/tools/<domain>.py` × 14（最大 218 行）+ `mcp/server.py` aggregator（139 行）
- `tool_specs/registry/_factories.py` (109 行) + `tool_specs/registry/<domain>.py` × 14（最大 176 行）+ `tool_specs/registry/__init__.py` (51 行)

48 个 MCP tool 名称 / 签名 / docstring / 返回 JSON / ToolSpec 字段全部不变。新增守护测试 `tests/mcp/test_tools_layout.py` 锁定「mcp 注册顺序 = TOOL_SPEC_REGISTRY 顺序」不变量。pytest **415 passed**（412 + 3 守护），8 skipped。本 change 修复 1 项 pre-existing drift（minute K 线在 server.py 与 registry.py 中相对顺序不一致）。

## Completeness

按 spec 3 条 ADDED Requirement 逐条核对：

- 已实现「MCP tool 与 ToolSpec registry 必须按 domain 物理拆分」：MCP tool 定义分布在 `mcp/tools/<domain>.py` × 14；ToolSpec 字面量分布在 `tool_specs/registry/<domain>.py` × 14；任一文件 ≤ 218 行（< 800 行 SHOULD 上限）。
- 已实现「MCP tool 注册顺序必须与 ToolSpec registry 顺序严格一致」：`tests/mcp/test_tools_layout.py` 三个测试（集合一致 / 顺序一致 / 元测试 count==48）全部 PASS；`mcp.list_tools()` 与 `TOOL_SPEC_REGISTRY.keys()` 完全相等（前者 48 个，后者 48 个，按位逐一相等）。
- 已实现「拆分必须保留外部 import 入口与测试 mock 路径」：
  - `from finance_data.mcp.server import mcp` 仍可 work（server.py 行 21 re-export）
  - `from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` 仍可 work（registry/__init__.py 拼接）
  - `from finance_data.tool_specs import TOOL_SPEC_REGISTRY` 仍可 work（tool_specs/__init__.py 不变）
  - `patch("finance_data.mcp.server.<service>.<method>")` 仍可 work（server.py 行 64-115 re-export 全部 28 个 service 实例）
  - `from finance_data.mcp.server import tool_get_xxx` 仍可 work（server.py 行 24-92 re-export 全部 48 个 tool 函数）
- CLAUDE.md 架构章节已同步更新，说明新拆分结构 + 守护约束。

## Correctness

已执行并通过：

- `openspec validate split-mcp-server-by-domain --strict` → `Change ... is valid`
- `pytest tests/` → **415 passed, 8 skipped**（包含 3 个新守护测试 + 7 个 proxy_guard 跳过的 non-eastmoney providers）
- 拆分过程多次跑全量 pytest，每个 task 完成都验证零回归：
  - Task 1（守护测试合入）：412 passed（守护测试中 1 个揭露 pre-existing drift 预期 FAIL，集合 + 元测试 PASS）
  - Task 2（_app.py 抽取）：412 passed
  - Task 3（registry 拆分）：412 passed
  - Task 5（mcp/tools 拆 + server.py 重写）：415 passed（守护全部 PASS）
- `wc -l src/finance_data/mcp/{server,_app}.py src/finance_data/mcp/tools/*.py src/finance_data/tool_specs/registry/*.py` → 全部 ≤ 218 行
- `python3 -c "from finance_data.mcp.server import mcp; import asyncio; print(len(asyncio.run(mcp.list_tools())))"` → `48`
- `python3 -c "from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY; print(len(TOOL_SPEC_REGISTRY))"` → `48`
- 守护测试故意场景验证（task 1.2）：临时去掉 minute K 线在 registry 中的位置错位 → 守护 PASS；恢复 → 仍 PASS。守护测试在拆分前 task 1.3 时记录的「顺序一致测试 FAIL」已由 task 5 拆分自然修复。

未做 Playwright 验证：本 change 不涉及前端（Dashboard 仍通过 ToolSpec 间接消费，无界面改动）。

未做 mcp_server.py 启动 + 真实 MCP client 列出 48 tool 验证：由 `mcp.list_tools()` 程序化验证已等价覆盖（`mcp_server.py` 仅做 `mcp.run()`，启动行为不依赖拆分细节）。

## Coherence

- FastMCP 单例与 helper 抽到 `mcp/_app.py`（与 design.md Decision 1 一致），避免「server.py → tools/<domain>.py → server.py」循环 import。
- `mcp/server.py` 收敛为「aggregator + 全量 re-export」：14 个 tools 子模块 import 触发 @mcp.tool 注册 + 28 个 service 实例 re-export + 48 个 tool 函数 re-export（与 design.md Decision 2 一致；测试 4 处 patch 路径零修改）。
- ToolSpec 拆分采用「子模块定义 SPECS list + __init__ 拼接 OrderedDict」（与 design.md Decision 3 一致）。
- 14 个 domain 顺序按 first occurrence 确定为 `(stock, kline, quote, index, board, fundamental, cashflow, market, lhb, pool, north_flow, margin, technical, fund_flow)`（与 design.md Decision 4 一致）。
- 守护测试用文件级文本扫描风格的列表比对，零网络副作用（与 design.md Decision 5 一致）。
- `tests/test_mcp_server.py` 4 处 patch 零修改（与 design.md Decision 6 一致）。
- 拆分后 `_DOMAIN_ORDER`（registry 顺序）与 `mcp/server.py` re-export 顺序、`mcp/tools/<domain>.py` 函数顺序三者一致，由守护测试强制。
- pre-existing drift 修复：原 `tool_get_kline_minute_history` 在 server.py 文件末尾、在 registry.py 紧跟月线之后；拆分后两边都在 kline.py 第 4 个位置，自然对齐。

## 未测试项与风险

- **未实测 mcp_server.py 启动 + 真实 MCP client 通讯**：由 `mcp.list_tools()` 程序化验证替代。若未来 MCP 协议层变更，需独立 e2e 测试覆盖。
- **未实测 dashboard 工具列表 UI 顺序变化的影响**：拆分后 TOOL_SPEC_REGISTRY 顺序与历史源码顺序不同（design.md Decision 4 明确接受此 trade-off），dashboard 工具列表展示顺序可能微变；视觉影响轻微，工具集合不变。
- **未实测 14 个 tools 子模块的循环 import 边界**：当前拆分中每个 tools 子模块只 `from finance_data.mcp._app import mcp, _invoke_tool_json` + 各自 service import，无相互依赖；若未来某 domain 需要跨 domain 调用（如 lhb 引用 board 数据），需 design 重新评估循环 import 风险。
- **未实测 `_factories.py` 的 helper 是否被外部使用**：当前仅 14 个 registry 子模块消费；若未来独立测试需要 mock helper，可能需要把 `_factories.py` 的下划线前缀去掉以表「公开 helper」。

## Spec Drift

**已修复 Drift 1（pre-existing）**：拆分前 `mcp.list_tools()` 与 `TOOL_SPEC_REGISTRY.keys()` 顺序不一致（minute K 线在 server.py 文件末尾 1213 行注册，但在 registry.py 紧跟月线第 5 个位置）。这违反 spec 第 2 条 Requirement，但 spec 是本 change 引入的，所以严格上不算 drift；记录为「pre-existing layout 差异」由本 change 顺带修复。

**未发现新 drift**：48 个 tool 全部覆盖；spec 3 条 Requirement 全部有对应实现证据；CLAUDE.md 文档已同步。

## 上游未对齐项

无。本 change 不接入任何上游金融数据源，纯结构重构。
