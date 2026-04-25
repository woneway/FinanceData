## MODIFIED Requirements

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
