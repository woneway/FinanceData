## ADDED Requirements

### Requirement: 个股历史月线必须作为独立能力对外提供
系统 MUST 以独立能力对外提供个股历史月线，不再通过统一 K 线工具内的 `period=monthly` 暴露该能力。

#### Scenario: MCP 调用历史月线
- **WHEN** 调用方通过 MCP 请求个股历史月线
- **THEN** 系统返回月线数据
- **AND** MCP 工具契约不包含 `period`

#### Scenario: HTTP API 调用历史月线
- **WHEN** 调用方通过 HTTP API 请求个股历史月线
- **THEN** 系统返回月线数据
- **AND** API 契约不依赖 `period`

### Requirement: 个股历史月线必须采用每日更新月线语义
系统 MUST 将个股历史月线定义为“每日更新月线”，并统一不同 provider 对未完成月的处理方式。

#### Scenario: 月线包含当前未完成月时语义一致
- **WHEN** 调用方请求包含当前交易月的历史月线
- **THEN** 系统对外返回一致的月线语义
- **AND** 不因 provider 默认行为差异造成未说明的不一致

### Requirement: 个股历史月线必须先完成上游对齐再改造 provider
系统 MUST 先完成 `tushare` 官方“周/月线行情（每日更新）”与 `akshare` 官方月线定义对齐，再实现 provider 兼容层。

#### Scenario: 月线 provider 改造前验证官方接口
- **WHEN** 维护方开始改造历史月线 provider
- **THEN** 必须已定位官方文档入口
- **AND** 必须已验证原始接口返回的字段、单位和更新时间语义

### Requirement: 前端与后台必须同步改造成独立历史月线能力
系统 MUST 将前端调用页面和 Web 管理后台同步改造成独立历史月线能力，而不是继续复用旧的统一历史 K 线入口。

#### Scenario: 前端页面展示独立月线入口
- **WHEN** 调用方进入前端调用页面
- **THEN** 可以直接选择历史月线工具
- **AND** 页面不再通过周期下拉来切换到月线
