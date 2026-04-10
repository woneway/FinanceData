## ADDED Requirements

### Requirement: 个股历史周线必须作为独立能力对外提供
系统 MUST 以独立能力对外提供个股历史周线，不再通过统一 K 线工具内的 `period=weekly` 暴露该能力。

#### Scenario: CLI 调用历史周线
- **WHEN** 调用方通过 CLI 请求个股历史周线
- **THEN** 系统返回周线数据
- **AND** 调用参数中不包含 `period`

#### Scenario: Web 页面展示独立历史周线入口
- **WHEN** 调用方在 Web 页面选择个股历史周线
- **THEN** 页面展示独立工具入口
- **AND** 不再依赖历史 K 线周期下拉切换到周线

### Requirement: 个股历史周线必须采用每日更新周线语义
系统 MUST 将个股历史周线定义为“每日更新周线”，并在 `tushare` 与 `akshare` 上游对齐后统一未完成周的处理方式。

#### Scenario: 周线包含当前未完成周时语义一致
- **WHEN** 调用方请求包含当前交易周的历史周线
- **THEN** 系统对外返回一致的周线语义
- **AND** 不因不同 provider 的默认行为而产生未说明的差异

### Requirement: 个股历史周线必须先完成上游对齐再改造 provider
系统 MUST 先完成 `tushare` 官方“周/月线行情（每日更新）”与 `akshare` 官方周线定义对齐，再实现 provider 兼容层。

#### Scenario: 周线 provider 改造前验证官方接口
- **WHEN** 维护方开始改造历史周线 provider
- **THEN** 必须已定位官方文档入口
- **AND** 必须已验证原始接口返回的字段、单位和更新时间语义

### Requirement: 个股历史周线默认只使用 tushare 和 akshare
系统 MUST 将 `tushare` 与 `akshare` 作为个股历史周线默认启用的两个源，其它源默认不参与主交付链。

#### Scenario: 周线默认 provider 收敛
- **WHEN** 系统构建历史周线的默认 provider 链
- **THEN** 默认只启用 `tushare` 和 `akshare`
- **AND** 其它源保持关闭状态，直到单独验收通过
