# delivery-tool-spec-contract Specification

## Purpose
定义 CLI、MCP、Dashboard API、前端看板四个交付入口如何共同消费 `ToolSpec` 工具契约，以及它们必须满足的一致性、兼容性与验证要求。
## Requirements
### Requirement: 交付入口共享工具契约
系统 SHALL 以统一工具契约作为 CLI、MCP、Dashboard API 和前端看板的工具定义来源。工具名、参数、默认值、参数选项、返回字段、provider 列表、探测配置和业务调用目标 MUST 在各交付入口保持一致。

#### Scenario: 工具列表一致
- **WHEN** 一个工具被注册为可交付工具
- **THEN** CLI、MCP、Dashboard API 和前端看板 MUST 能基于同一工具契约识别该工具

#### Scenario: 参数契约一致
- **WHEN** 一个工具定义了必填参数、可选参数、默认值或参数选项
- **THEN** CLI、MCP、Dashboard API 和前端看板 MUST 暴露一致的参数语义

#### Scenario: 返回字段一致
- **WHEN** 一个工具定义了返回字段
- **THEN** Dashboard API 和前端看板 MUST 使用该返回字段契约展示结果结构

### Requirement: 业务调用统一进入 service
系统 SHALL 保证 CLI、MCP、Dashboard API 和前端看板触发的默认业务调用最终进入 service 语义层。交付入口 MUST NOT 绕过 service 直接依赖 provider 作为默认用户调用路径。

#### Scenario: 默认调用路径
- **WHEN** 用户通过 CLI、MCP、Dashboard API 或前端看板调用工具
- **THEN** 系统 MUST 根据工具契约解析业务调用目标并调用对应 service

#### Scenario: provider 诊断调用
- **WHEN** 用户显式选择 provider 诊断调用
- **THEN** 系统 MUST 仅调用工具契约中声明的 provider，并 MUST 将该调用与默认 service 调用路径区分

### Requirement: MCP 工具契约不得漂移
系统 SHALL 保留 MCP 工具的稳定名称和参数签名，同时 MCP 工具的执行语义 MUST 来源于统一工具契约。MCP 工具不得维护与统一工具契约冲突的默认值、参数映射或 service 调用目标。

#### Scenario: MCP wrapper 调用已注册工具
- **WHEN** MCP 工具函数被调用
- **THEN** 系统 MUST 使用该工具名对应的统一工具契约解析参数并调用 service

#### Scenario: MCP 缺少工具
- **WHEN** 统一工具契约中存在一个可交付工具
- **THEN** MCP 校验 MUST 能发现缺失的对应 MCP 工具暴露

#### Scenario: MCP 参数不匹配
- **WHEN** MCP 工具无法接收统一工具契约中的必填参数
- **THEN** 校验 MUST 报告该工具存在契约不一致

### Requirement: 前端看板不得维护独立工具表
前端看板 SHALL 从 Dashboard API 获取工具契约并动态渲染工具选择、参数表单、provider 选择和结果字段。前端看板 MUST NOT 维护独立的工具参数表、provider 表或返回字段表。

#### Scenario: 动态渲染工具表单
- **WHEN** Dashboard API 返回工具参数契约
- **THEN** 前端看板 MUST 根据该契约渲染对应输入控件

#### Scenario: 工具契约更新
- **WHEN** 后端统一工具契约新增可选参数或参数选项
- **THEN** 前端看板 MUST 在不修改本地工具表的情况下展示新参数或选项

### Requirement: 一致性验证覆盖交付层
系统 SHALL 提供自动化验证，证明统一工具契约与 CLI、MCP、Dashboard API 和前端看板保持一致。验证失败 MUST 阻止该 change 被视为完成。

#### Scenario: 注册表校验
- **WHEN** 运行交付层契约校验
- **THEN** 系统 MUST 检查工具契约完整性、service 调用目标存在性、MCP 暴露一致性和 Dashboard API 投影一致性

#### Scenario: 调用路径校验
- **WHEN** 对同一个工具分别通过 CLI、MCP 和 Dashboard API 触发调用
- **THEN** 系统 MUST 能证明这些入口使用一致的参数归一和 service 调用目标

#### Scenario: 前端契约校验
- **WHEN** 运行前端看板验收
- **THEN** 验收 MUST 覆盖工具契约加载、参数表单渲染和调用请求使用后端契约

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

