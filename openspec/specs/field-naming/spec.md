# field-naming Specification

## Purpose
TBD - created by archiving change retroactive-duckdb-cache-layer. Update Purpose after archive.
## Requirements
### Requirement: 涨跌幅字段必须统一命名为 pct_chg
系统中所有 dataclass、provider 输出 dict、tool_specs return_fields、MCP 工具返回字段中表达「涨跌幅百分比」的字段 MUST 命名为 `pct_chg`，单位 MUST 是百分比。`pct_change` 作为字段名 MUST NOT 出现在新增代码中。

#### Scenario: 新接入 provider 必须用 pct_chg
- **WHEN** 维护方为新数据源实现 provider
- **THEN** 涨跌幅字段 MUST 命名为 `pct_chg`
- **AND** 单位 MUST 是百分比

#### Scenario: 现有 provider 的字段名一致
- **WHEN** 调用方查询任何接口的涨跌幅
- **THEN** 返回字段名 MUST 是 `pct_chg`，不存在 `pct_change` 别名
- **AND** 跨 provider（akshare / tushare / xueqiu / tencent / baostock）必须使用同名

### Requirement: 字段命名 breaking change 必须显式声明
系统在引入任何字段名 breaking change（重命名 / 删除 / 单位变更）时 MUST 在对应 OpenSpec change 的 proposal 中显式声明 breaking、影响范围与迁移指引。fe01b51 之前未走该流程，本 retroactive 已补齐声明。

#### Scenario: 已发生的 breaking 必须留痕
- **WHEN** 维护方需要追溯 `pct_change → pct_chg` 这一历史 breaking
- **THEN** 必须能在 OpenSpec 中找到本 retroactive change（`retroactive-duckdb-cache-layer`）作为合规追认
- **AND** 该 change 的 proposal MUST 列出影响的 4 个 interface 文件与影响的下游

#### Scenario: 未来的字段重命名走完整流程
- **WHEN** 未来出现类似的字段重命名需求
- **THEN** 必须开独立 OpenSpec change，按 propose → spec → apply → verify → archive 流程
- **AND** proposal MUST 显式标注 breaking、列出受影响 dataclass 与受影响调用方
- **AND** 不允许在 retroactive 中追认未来的 breaking

### Requirement: 字段命名规范必须由 validator 守护
系统 MUST 引入 validator 在 CI 或 pre-commit 阶段扫描代码，禁止新增 `pct_change` 字段名。该 validator 在本 retroactive 不实现（追认纪律「不修代码」），但 spec 锁定该约束，由独立后续 change 落地实现。在 validator 实现前，此 Requirement 处于「认可但未守护」状态，对应 acceptance.md 中的「未测试项」记录。

#### Scenario: validator 扫描出违例
- **WHEN** 任何 PR 引入 `pct_change` 字段名（含 dataclass 字段、return_fields、provider 输出 key）
- **THEN** validator MUST 报错并阻止合并
- **AND** 报错信息 MUST 指向本 spec 中「涨跌幅字段必须统一命名为 pct_chg」Requirement

