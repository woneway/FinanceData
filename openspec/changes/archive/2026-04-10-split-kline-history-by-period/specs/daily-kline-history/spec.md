## ADDED Requirements

### Requirement: 个股历史日线必须作为独立能力对外提供
系统 MUST 以独立能力对外提供个股历史日线，不再要求调用方通过统一 K 线工具加 `period` 参数来获取日线。

#### Scenario: CLI 调用历史日线
- **WHEN** 调用方通过 CLI 请求个股历史日线
- **THEN** 系统返回日线数据
- **AND** 调用参数只包含日线能力需要的参数，而不包含 `period`

#### Scenario: MCP 调用历史日线
- **WHEN** 调用方通过 MCP 请求个股历史日线
- **THEN** 系统返回日线数据
- **AND** MCP 工具契约不再暴露 `period`

### Requirement: 个股历史日线必须先对齐上游官方定义
系统 MUST 在实现个股历史日线适配前，先对齐 `tushare` 和 `akshare` 的官方日线定义，并以原始接口返回确认字段含义、单位、更新时间和错误行为。

#### Scenario: 上游对齐完成后再改造适配层
- **WHEN** 维护方为历史日线改造 provider
- **THEN** 必须能指出对应的官方文档入口
- **AND** 必须已验证原始接口返回

### Requirement: 个股历史日线默认只使用主源和 fallback
系统 MUST 将 `tushare` 作为个股历史日线的主源，将 `akshare` 作为 fallback，其他 provider 默认不参与主交付链。

#### Scenario: 主交付链只包含主源和 fallback
- **WHEN** 系统构建个股历史日线的默认 provider 链
- **THEN** 默认链中包含 `tushare` 和 `akshare`
- **AND** 默认链中不包含其他未单独验收的 provider

### Requirement: Web 管理后台必须展示历史日线的源级状态
系统 MUST 在 Web 管理后台展示历史日线的 service 可用性和 provider 级健康度，便于维护方识别主源、fallback 和源级错误。

#### Scenario: 后台查看历史日线状态
- **WHEN** 维护方在 Web 管理后台查看历史日线
- **THEN** 可以看到 service 状态
- **AND** 可以看到 `tushare` 与 `akshare` 的源级健康度
