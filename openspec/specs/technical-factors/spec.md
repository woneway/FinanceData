# technical-factors Specification

## Purpose
TBD - created by archiving change retroactive-tushare-stk-factor-pro. Update Purpose after archive.
## Requirements
### Requirement: 技术因子能力必须按单一工具暴露
系统 MUST 以单一工具向 CLI、MCP、HTTP API、Web 管理后台暴露个股技术因子（含 MA / MACD / KDJ / RSI / BOLL / CCI 与估值字段）。工具契约 MUST 接受可选的 `ts_code`、`trade_date`、`start_date`、`end_date` 四参数。

#### Scenario: 单股票多日查询
- **WHEN** 调用方传 `ts_code` + `start_date` + `end_date`
- **THEN** 系统返回该股票在区间内的因子序列
- **AND** 每行 MUST 含 `trade_date` 与 `symbol`

#### Scenario: 全市场单日查询
- **WHEN** 调用方仅传 `trade_date`
- **THEN** 系统返回该日所有股票的因子快照
- **AND** 单次返回 MUST 在上游 10000 条限制内（详见「单源 tushare 限制必须显式声明」）

### Requirement: 技术因子必须先完成上游对齐再实现 provider
系统 MUST 在为技术因子 capability 实现或修改 provider 适配前，先完成对 tushare `stk_factor_pro` 的上游对齐，并以原始接口返回确认字段含义、单位、积分门槛与单次条数限制。对齐结论 MUST 沉淀为 `upstream-alignment.md`。

#### Scenario: 上游对齐覆盖技术指标字段名规则
- **WHEN** 维护方为技术因子改造 provider
- **THEN** 必须已记录 tushare 原始字段名前缀（`ma_bfq_`、`rsi_bfq_`）和后缀（`_bfq`）映射到项目统一字段名（`ma5`、`rsi_6`、`macd` 等）的规则

### Requirement: 技术因子的字段单位必须经 provider 显式换算
系统 MUST 在 provider 适配层完成 tushare 原始字段到项目统一单位的换算：`vol` × 100 → 股、`amount` × 1000 → 元、`total_share / float_share / free_share / total_mv / circ_mv / free_mv` × 10000 → 股 / 元。换算后的字段 MUST 与 spec 中声明的单位（股 / 元 / 百分比 / 倍数）一致。

#### Scenario: 单位换算后对外语义一致
- **WHEN** 调用方收到任一行因子数据
- **THEN** `volume` 单位 MUST 是「股」、`amount` 单位 MUST 是「元」、`total_mv / circ_mv / free_mv` 单位 MUST 是「元」
- **AND** 与日线 K 线（`kline-history`）的同名字段单位 MUST 完全一致

### Requirement: 单源 tushare 限制必须显式声明
系统 MUST 在工具契约或文档中显式声明：技术因子能力当前为 tushare 单源，无 fallback；需要 5000 积分权限；单次返回上限 10000 条。

#### Scenario: 用户契约知悉积分要求
- **WHEN** 调用方查阅工具描述
- **THEN** 描述 MUST 列出「需要 5000 积分」、「无 fallback」、「单次最多 10000 条」三条限制

#### Scenario: 超限返回时的容错
- **WHEN** 上游因积分不足或单次限制返回错误
- **THEN** service MUST 抛出 `DataFetchError`（kind=`auth` 或 kind=`data`）
- **AND** MUST NOT 静默返回部分数据

