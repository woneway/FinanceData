# kline-history Specification

## Purpose
TBD - created by archiving change consolidate-kline-history-specs. Update Purpose after archive.
## Requirements
### Requirement: 个股历史 K 线必须按周期独立暴露
系统 MUST 为日线、周线、月线、分钟线四个周期各自暴露独立的工具能力。任一交付入口（CLI、MCP、HTTP API、Web 管理后台）MUST NOT 通过统一 K 线工具加 `period` 参数的方式提供这四种能力，每个周期的工具契约 MUST NOT 出现 `period` 字段。

#### Scenario: CLI 调用各周期 K 线
- **WHEN** 调用方通过 CLI 请求日线、周线、月线或分钟线
- **THEN** 系统按周期分别返回数据
- **AND** 调用参数 MUST NOT 包含 `period`

#### Scenario: MCP 调用各周期 K 线
- **WHEN** 调用方通过 MCP 请求日线、周线、月线或分钟线
- **THEN** 系统按周期分别返回数据
- **AND** MCP 工具契约 MUST NOT 暴露 `period`

#### Scenario: HTTP API 调用各周期 K 线
- **WHEN** 调用方通过 HTTP API 请求日线、周线、月线或分钟线
- **THEN** 系统按周期分别返回数据
- **AND** API 契约 MUST NOT 依赖 `period`

#### Scenario: 前端页面展示独立周期入口
- **WHEN** 调用方进入前端调用页面
- **THEN** 可以分别选择日线、周线、月线、分钟线工具
- **AND** 页面 MUST NOT 通过周期下拉切换实现这些能力

### Requirement: 个股历史 K 线必须先完成上游对齐再实现 provider
系统 MUST 在为任一周期实现或修改 provider 适配前，先完成上游官方接口对齐，并以原始接口返回确认字段含义、单位、更新时效、复权策略、历史范围、未完成周期处理与错误行为。对齐结论 MUST 沉淀为 `upstream-alignment.md`，覆盖至少七个对照维度（调用方式 / 字段 / 单位 / 复权 / 历史范围 / 更新时间 / 状态）。

#### Scenario: 上游对齐完成后再改造适配层
- **WHEN** 维护方为任一周期改造 provider
- **THEN** 维护方 MUST 能给出官方文档入口
- **AND** MUST 已用真实调用打印过返回字段
- **AND** MUST 已记录单位与更新时效

#### Scenario: 缺上游对齐不允许接入
- **WHEN** 一个 change 涉及新周期 provider 但缺 `upstream-alignment.md`
- **THEN** 该 change MUST NOT 进入 archive

### Requirement: 各周期 K 线必须显式定义更新时效与未完成周期处理
系统 MUST 显式定义每个周期的更新时效与未完成周期的对外语义。维护方 MUST 在 spec 与上游对齐文档中描述 provider 的默认行为差异，并在 service 层统一为单一对外语义；交付入口 MUST NOT 因不同 provider 默认行为产生未说明的差异。

#### Scenario: 日线更新时效
- **WHEN** 调用方在交易日 T 当天请求日线
- **THEN** 系统 MUST 在收盘后约 T+1 16:00 之前返回截至 T-1 的完整日线
- **AND** T 当日数据的供给状态 MUST 由 service 层显式确定

#### Scenario: 周线 / 月线包含当前未完成周期时语义一致
- **WHEN** 调用方请求包含当前交易周或交易月的周线 / 月线
- **THEN** 系统对外 MUST 返回一致的「每日更新周线 / 月线」语义
- **AND** MUST NOT 因不同 provider 默认行为产生未说明的不一致
- **AND** 若包含未完成周期 MUST 在返回中可被识别

#### Scenario: 分钟 K 线时效
- **WHEN** 调用方请求 5/15/30/60 分钟 K 线
- **THEN** 系统 MUST 在每个分钟周期结束后将对应 bar 暴露为可查询
- **AND** 实时盘中未完成的分钟 bar MUST NOT 被计入返回

### Requirement: 各周期 K 线必须采用项目偏好的默认主源与 fallback
系统 MUST 按以下默认 provider 链构建每个周期的对外服务：
- 日线：tushare 主源 + akshare（腾讯源）fallback
- 周线 / 月线：tushare 主源 + akshare（东财源，需代理绕过）fallback
- 分钟线：baostock 主源（无 fallback，受上游免费源限制）

其他 provider（xueqiu / tencent / 其它 baostock 接口）默认 MUST NOT 出现在主交付链中，除非通过单独 change 完成验收并显式开启。

#### Scenario: 默认 provider 链收敛
- **WHEN** 系统构建任一周期的默认 provider 链
- **THEN** 默认链 MUST 仅包含本 Requirement 列出的主源与 fallback
- **AND** 其他 provider MUST 默认关闭，直到单独验收通过

#### Scenario: 分钟线无 fallback
- **WHEN** baostock 不可用而调用方请求分钟线
- **THEN** 系统 MUST 返回明确的错误，告知数据源不可用
- **AND** MUST NOT 静默回退到任何未验收的 provider

### Requirement: 涉及东财上游的周期 K 线 fallback 必须配置代理绕过
系统在使用东财上游（akshare 中以 `_em` 结尾或 `stock_zh_a_hist` 等）作为周线 / 月线 fallback 时 MUST 在 provider 模块层强制绕过本地代理，以避免本地 HTTP 代理拦截东财直连。

#### Scenario: 东财 fallback 在模块加载时绕过代理
- **WHEN** 周线或月线 fallback provider 模块被加载
- **THEN** 模块 MUST 在执行任何东财调用前完成代理绕过设置

### Requirement: 各周期 K 线必须在 Web 管理后台暴露源级状态
系统 MUST 在 Web 管理后台展示每个周期 K 线的 service 可用性与 provider 级健康度，使维护方可以分别识别主源与 fallback 状态。

#### Scenario: 后台查看任一周期 K 线状态
- **WHEN** 维护方在 Web 管理后台查看日线、周线、月线或分钟线
- **THEN** 可以看到对应 service 状态
- **AND** 可以看到该周期默认 provider 链中每个 provider 的健康度

### Requirement: 分钟 K 线必须显式声明权限敏感性
系统 MUST 在分钟 K 线工具契约与文档中显式声明：分钟级数据为权限敏感数据，受上游 baostock 免费源策略与 tushare 分钟权限策略影响；调用方 MUST 知悉该数据可能因上游策略变化而不可用。

系统 MUST 在 `pyproject.toml` 中显式锁定 `baostock>=0.9.1` 作为最低版本依赖。原因：baostock 0.9.1（2026-04-14）已将服务地址从 `www.baostock.com` 迁移至 `public-api.baostock.com`，旧地址的 10030 端口已全球停服；0.8.9 及以下版本会卡登录超时，分钟 K 线接口随之不可用。

#### Scenario: 分钟工具描述包含权限提示
- **WHEN** 调用方查阅分钟 K 线工具的契约或文档
- **THEN** 描述 MUST 显式说明数据源、免费源限制与可能的不可用情形

#### Scenario: baostock 依赖最低版本被工程化锁定
- **WHEN** 维护方在新机器执行 `pip install -e .` 或 `pip install finance-data`
- **THEN** 安装解析出的 baostock 版本 MUST >= 0.9.1
- **AND** 不允许 baostock 以孤立安装（未在 `pyproject.toml` 声明）方式存在

#### Scenario: baostock 服务地址变更后的容错
- **WHEN** baostock 上游再次迁移服务地址或进一步限制免费访问
- **THEN** 分钟 K 线 service MUST 抛出明确的 DataFetchError（kind=network 或 kind=auth）
- **AND** MUST NOT 静默回退到任何未验收的 provider
- **AND** 错误信息 MUST 携带 baostock 版本与服务地址提示，便于排查

