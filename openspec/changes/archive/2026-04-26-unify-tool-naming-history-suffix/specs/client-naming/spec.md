## ADDED Requirements

### Requirement: 客户端公开方法名必须从 MCP tool 名派生
系统的 `FinanceData` Python 客户端公开方法名 MUST 与对应 MCP tool 名严格对应：客户端方法名 = MCP tool 名去掉 `tool_get_` 前缀后的剩余部分。scope 后缀（`_history` / `_realtime` / `_snapshot` / `_daily`）MUST 保留，不允许省略。

#### Scenario: 客户端方法名与 MCP tool 名 1:1 对应
- **WHEN** 维护方查阅 `FinanceData` 类的全部公开方法
- **THEN** 每个方法名 MUST 等于某个 MCP tool 名去掉 `tool_get_` 前缀
- **AND** MCP tool 名集合 MUST 等于客户端公开方法名集合（不含 alias）

#### Scenario: scope 后缀必须显式
- **WHEN** 一个 ToolSpec 的 scope 是 `history`
- **THEN** 对应客户端方法名 MUST 以 `_history` 结尾
- **AND** 不允许出现既无后缀又无前缀替代的简短别名作为公开方法

### Requirement: 客户端方法重命名必须保留 deprecated alias
系统在重命名客户端公开方法时 MUST 保留旧名为 deprecated alias 至少 1 个 minor 版本。调用 alias MUST 实际调用新方法（行为零变更）并 MUST 发出 `DeprecationWarning`，warning 文本 MUST 含旧名、新名与迁移指引。

#### Scenario: 旧名调用仍可工作
- **WHEN** 用户脚本调用 `fd.<old_name>(...)` 任一已重命名方法
- **THEN** 调用 MUST 成功并返回与新方法等价的结果
- **AND** Python warning system MUST 发出 `DeprecationWarning`
- **AND** warning 文本 MUST 包含「请改用 `fd.<new_name>()`」字样

#### Scenario: 私有方法与 dunder 不被 alias 覆盖
- **WHEN** 用户访问 `fd._get_service` 或 `fd.__init__` 等私有 / dunder 名
- **THEN** alias 拦截 MUST NOT 触发
- **AND** 行为与 Python 默认属性查找一致

### Requirement: 客户端命名一致性必须由守护测试强制
系统 MUST 提供自动化守护测试，断言：
1. 客户端公开方法名集合（去掉以 `_` 开头的私有方法 + alias）= MCP tool 名集合（去掉 `tool_get_` 前缀）。
2. 每个 deprecated alias 调用都能 work 并发出 `DeprecationWarning`。

#### Scenario: 集合一致性守护
- **WHEN** 守护测试枚举 `FinanceData` 公开方法名（排除以 `_` 开头）与 `TOOL_SPEC_REGISTRY.keys()` 去前缀
- **THEN** 两个集合 MUST 完全相等
- **AND** 若集合不一致，测试 MUST FAIL 并打印两侧差异

#### Scenario: alias 兼容性守护
- **WHEN** 守护测试遍历 `_DEPRECATED_ALIASES` 字典
- **THEN** 每个旧名 MUST 在 `FinanceData` 实例上可访问
- **AND** 调用任一旧名 MUST 触发 Python `DeprecationWarning`
- **AND** alias 对应的新名 MUST 在 `FinanceData` 上以方法形式存在
