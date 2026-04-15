## ADDED Requirements

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
