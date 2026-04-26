## ADDED Requirements

### Requirement: MCP tool 与 ToolSpec registry 必须按 domain 物理拆分
系统 MUST 把 MCP tool 函数定义与 ToolSpec 字面量按 14 个 domain（参考 CLAUDE.md：stock / kline / quote / index / board / fundamental / cashflow / lhb / pool / north_flow / margin / market / technical / fund_flow）物理拆分到独立文件。每个文件 SHOULD 控制在 800 行以内，与 `.claude/rules/common/coding-style.md` 的「文件 800 行上限」一致。

#### Scenario: 单一文件不再承担全部 tool 定义
- **WHEN** 维护方查看 `src/finance_data/mcp/` 与 `src/finance_data/tool_specs/` 目录结构
- **THEN** MCP tool 定义 MUST 分布在 `mcp/tools/<domain>.py` 多个文件中
- **AND** ToolSpec 字面量 MUST 分布在 `tool_specs/registry/<domain>.py` 多个文件中
- **AND** 任一 `<domain>.py` 文件行数 SHOULD 不超过 800 行

#### Scenario: 新增同 domain 的 tool 不需要修改其他 domain 文件
- **WHEN** 维护方新增一个 lhb domain 的 tool
- **THEN** 改动 MUST 仅涉及 `mcp/tools/lhb.py` + `tool_specs/registry/lhb.py` + service / provider / interface 同 domain 文件
- **AND** 其他 domain 文件 MUST NOT 被修改

### Requirement: MCP tool 注册顺序必须与 ToolSpec registry 顺序严格一致
系统 MUST 保证 `mcp` 实例注册的 48 个 tool（按 `mcp.list_tools()` 或等价方式枚举的顺序）与 `TOOL_SPEC_REGISTRY` OrderedDict 的 keys 顺序完全一致。该一致性 MUST 由自动化守护测试强制：任一拆分或合并改动后，若两个顺序不一致，测试 MUST FAIL。

#### Scenario: 守护测试锁定顺序一致性
- **WHEN** 守护测试枚举 mcp 注册的 tool 名称列表与 `TOOL_SPEC_REGISTRY.keys()` 列表
- **THEN** 两个列表 MUST 元素相同且顺序一致
- **AND** 若不一致，测试 MUST FAIL 并打印两侧差异

#### Scenario: 拆分前后 tool 名称集合稳定
- **WHEN** 守护测试在 split-mcp-server-by-domain 实施前后两次运行
- **THEN** mcp 注册的 tool 名称集合 MUST 保持完全相同（拆分零 breaking）
- **AND** 集合的元素数 MUST 保持 48
- **AND** 顺序在本次实施后由「14 个 domain 的固定 `_DOMAIN_ORDER` × 各 domain 内 SPECS 列表顺序」确定，可与历史源码顺序不同；但 mcp 注册顺序与 TOOL_SPEC_REGISTRY 顺序 MUST 始终保持一致

### Requirement: 拆分必须保留外部 import 入口与测试 mock 路径
系统在按 domain 拆分 MCP / ToolSpec 后 MUST 保留以下外部入口的兼容性：

- `from finance_data.mcp.server import mcp` 仍可工作。
- `from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` 仍可工作。
- `from finance_data.tool_specs import TOOL_SPEC_REGISTRY` 仍可工作。
- 测试中 `patch("finance_data.mcp.server.<service_name>.<method>")` 形式的 mock 路径仍可工作（`server.py` MUST re-export 全部 service 实例名字）。

#### Scenario: 入口 API 兼容
- **WHEN** 任一 src 模块或 mcp_server.py 入口脚本 import `from finance_data.mcp.server import mcp`
- **THEN** import MUST 成功
- **AND** mcp 对象 MUST 是 FastMCP 实例并已注册全部 48 个 tool

#### Scenario: 测试 mock 路径兼容
- **WHEN** `tests/test_mcp_server.py` 用 `patch("finance_data.mcp.server.stock_history.get_stock_info_history", ...)` 等形式 mock
- **THEN** mock MUST 生效
- **AND** 通过该路径的测试 MUST 全部 PASS（不允许测试为兼容拆分而修改 mock 路径）
