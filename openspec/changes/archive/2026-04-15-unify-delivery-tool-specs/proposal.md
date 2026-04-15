## Why

当前 CLI、Dashboard API、前端看板已经主要消费 `tool_specs`，但 MCP 仍保留大量手写直调 service 的函数体，导致工具契约和调用路径仍可能与注册表漂移。现在需要把交付层统一到同一套工具契约上，保证新增工具时只维护一次 `ToolSpec`，并由统一验证证明 CLI、MCP、Dashboard 和前端看板一致。

## What Changes

- MCP、CLI、Dashboard API、前端看板统一以 `tool_specs` 作为工具契约来源。
- MCP 保留显式工具函数签名和 docstring，但函数体通过统一 ToolSpec dispatch helper 调用 service target。
- CLI 和 Dashboard invoke 继续通过 `ToolSpec.service` 调用 service，并复用同一套参数默认值、alias 归一和错误输出策略。
- 前端看板只消费后端 `/api/tools` 与 invoke API，不维护独立工具参数表。
- 增强验证，覆盖 MCP 函数与 ToolSpec 注册项、CLI invoke、Dashboard API、前端工具表单契约的一致性。
- 非目标：不改 provider 选型、不新增金融数据接口、不改变 `FinanceData` Python 客户端的领域 API 形态。
- 兼容性影响：对外工具名、参数名和 service 语义保持兼容；若发现现有 MCP 手写默认值与 ToolSpec 不一致，应以 ToolSpec 为准并补回归测试。
- 迁移影响：新增工具应先注册 `ToolSpec`，再通过统一 helper 暴露到 MCP/CLI/Dashboard/前端。
- 上线风险：MCP 函数体收敛可能改变错误 JSON、默认值处理或 alias 处理细节，需要用现有 MCP/CLI/Dashboard 测试和前端页面验收覆盖。

## Capabilities

### New Capabilities
- `delivery-tool-spec-contract`: 定义 CLI、MCP、Dashboard API、前端看板如何共同消费 `tool_specs`，以及它们必须满足的一致性、兼容性和验证要求。

### Modified Capabilities
- 无。

## Impact

- 受影响代码：`finance_data.tool_specs`、`finance_data.mcp.server`、CLI tools 命令、Dashboard invoke API、前端工具调用页面、相关 validators 与测试。
- 受影响 API：MCP tools、`finance-data tools/describe/invoke`、Dashboard `/api/tools`、Dashboard `/api/tools/{tool}`。
- 依赖：不新增上游金融数据源依赖；本 change 不涉及上游官方数据接口语义变更。
- 系统：交付层契约、健康检查、验证入口和前端动态表单渲染。
