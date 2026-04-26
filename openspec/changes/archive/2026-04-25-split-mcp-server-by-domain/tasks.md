## 1. 守护测试先行（在拆分前合入）

- [x] 1.1 调研 FastMCP 暴露的「list 已注册 tool」API：尝试 `await mcp.list_tools()`、`mcp._tool_manager._tools`、`mcp.tools` 等路径，确认稳定可用的方式。验证：交互式 Python 中 `from finance_data.mcp.server import mcp` 后能枚举出 48 个 tool 名称。
- [x] 1.2 新建 `tests/mcp/test_tools_layout.py`：断言 mcp 注册的 tool 名称列表 = `TOOL_SPEC_REGISTRY` keys 列表（集合 + 顺序双向一致）。验证：在当前未拆分代码下，集合一致测试 + 元测试 PASS，但**顺序一致测试预计 FAIL**（揭露 pre-existing drift：分钟 K 线在 server.py 中放在文件末尾但在 registry.py 中紧跟在月线后，致 MCP[4] 与 registry[4] 不一致）。这是本 change 要修复的 pre-existing drift，不是守护测试的 bug。
- [x] 1.3 接受 1.2 的预期失败；本 change 完成（task 5.3 拆分后）必须 3 个测试全部 PASS。

## 2. 抽 FastMCP 单例与 helper 到 _app.py

- [x] 2.1 新建 `src/finance_data/mcp/_app.py`：从 server.py 行 41-55 抽出 `mcp = FastMCP("finance-data")` + `_to_json` + `_invoke_tool_json`；保留原 helper 签名。验证：交互式 import `from finance_data.mcp._app import mcp, _invoke_tool_json` 成功。
- [x] 2.2 把 server.py 顶部 `mcp = FastMCP(...)` 与两个 helper 改为 `from finance_data.mcp._app import mcp, _to_json, _invoke_tool_json`。验证：跑全量 pytest 通过；mcp_server.py 启动后仍正常。

## 3. 拆 tool_specs/registry/

- [x] 3.1 新建 `src/finance_data/tool_specs/registry/_factories.py`：从原 registry.py 行 18-111 整段搬 5 个 helper（`_param` / `_provider` / `_service` / `_probe` / `_meta`）。验证：手工 `from finance_data.tool_specs.registry._factories import _param` 成功。
- [x] 3.2 新建 14 个 `src/finance_data/tool_specs/registry/<domain>.py`：把原 registry.py 行 114-968 中的 ToolSpec 字面量按 domain 字段值分组，每个 domain 文件暴露 `SPECS: list[ToolSpec] = [...]`。每个文件顶部 `from finance_data.tool_specs.models import ToolSpec` + `from finance_data.tool_specs.registry._factories import _param, _provider, _service, _probe, _meta`。
- [x] 3.3 新建 `src/finance_data/tool_specs/registry/__init__.py`：定义 `_DOMAIN_ORDER = (stock, kline, quote, index, board, fundamental, cashflow, lhb, pool, north_flow, margin, market, technical, fund_flow)`，并 `TOOL_SPEC_REGISTRY: "OrderedDict[str, ToolSpec]" = OrderedDict((spec.name, spec) for module in _DOMAIN_ORDER for spec in module.SPECS)`。验证：`from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` 成功，`len(...) == 48`。
- [x] 3.4 删除原 `src/finance_data/tool_specs/registry.py` 文件（与 `registry/` 包同名会冲突）。
- [x] 3.5 跑全量 pytest，确认 `tool_specs` 相关测试（adapters / invoke / validators）全绿。

## 4. 拆 mcp/tools/

- [x] 4.1 新建 14 个 `src/finance_data/mcp/tools/<domain>.py`：把原 server.py 行 58-1264 中 48 个 `@mcp.tool()` 函数按 domain 字段（参考 ToolSpec.domain）分组，每个文件顶部 `from finance_data.mcp._app import mcp, _invoke_tool_json` + 本 domain 的 service 实例 import。
- [x] 4.2 新建 `src/finance_data/mcp/tools/__init__.py`：留空（不做 re-export，避免循环 import）。

## 5. 重写 mcp/server.py 为 aggregator

- [x] 5.1 重写 `src/finance_data/mcp/server.py`：仅保留三段（约 50 行）：
  1. `from finance_data.mcp._app import mcp  # noqa: F401`
  2. 按确定顺序显式 import 14 个 tools 子模块以触发 @mcp.tool 注册
  3. re-export 全部 service 名字（与原 server.py 行 9-37 完全一致），每行加 `# noqa: F401`
- [x] 5.2 跑 `from finance_data.mcp.server import mcp; print(len(asyncio.run(mcp.list_tools())))` 确认仍是 48。
- [x] 5.3 跑全量 `pytest tests/`：必须 412 passed + 守护测试通过。

## 6. 文档与终验

- [x] 6.1 更新 `CLAUDE.md` 架构章节：把 `mcp/server.py` 与 `tool_specs/registry.py` 的描述改为 `mcp/tools/<domain>.py` 与 `tool_specs/registry/<domain>.py` 的拆分说明。
- [x] 6.2 跑 `wc -l src/finance_data/mcp/server.py src/finance_data/tool_specs/registry/*.py src/finance_data/mcp/tools/*.py` 确认无文件超 800 行。
- [ ] 6.3 跑 `mcp_server.py` 启动 + MCP client 列出 48 个 tool 验证（手动；非阻塞，由 list_tools API 程序化验证已等价覆盖）。

## 7. 写 acceptance 并归档

- [x] 7.1 写 `acceptance.md`：Completeness 逐条对应 spec 3 条 ADDED Requirement；Correctness 列 pytest 命令 + 行数 grep + 守护测试结果；Coherence 验证拆分前后行为零变更、re-export 兼容、守护测试锁定不变量；未测试项 / drift / 上游未对齐分别显式列出。
- [x] 7.2 `openspec validate split-mcp-server-by-domain --strict` 通过。
- [x] 7.3 `openspec archive split-mcp-server-by-domain -y`：已 MODIFIED `delivery-tool-spec-contract` 加 3 条 Requirement。验证：`openspec list --specs` 显示 9 个 capability，delivery-tool-spec-contract 由 0→5（spec 升级到新格式后正确解析）→8（archive 后追加 3 条新 Requirement）。归档过程顺带升级了 delivery-tool-spec-contract spec 的格式（老 `## ADDED Requirements` → 新 `# Specification + ## Purpose + ## Requirements`），与阶段 1 K线 spec 升级一致。
