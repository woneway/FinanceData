# fund-flow Specification

## Purpose
TBD - created by archiving change retroactive-tushare-stk-factor-pro. Update Purpose after archive.
## Requirements
### Requirement: 板块资金流必须按单一工具暴露概念 / 行业 / 地域三类
系统 MUST 以单一工具向 CLI、MCP、HTTP API、Web 管理后台暴露东财板块资金流。工具契约 MUST 接受可选的 `trade_date`、`start_date`、`end_date`、`ts_code`、`content_type` 五参数；`content_type` 取值 MUST 限定为 `概念` / `行业` / `地域` 三选一（或空表示全部）。

#### Scenario: 按 content_type 过滤
- **WHEN** 调用方传 `content_type=行业` 与 `trade_date`
- **THEN** 系统返回该日全部行业板块的资金流数据
- **AND** 返回行 `content_type` 字段 MUST 全部等于「行业」

#### Scenario: 按 ts_code 查询单板块历史
- **WHEN** 调用方传 `ts_code=BK1032` + `start_date` + `end_date`
- **THEN** 系统返回该板块在区间内的资金流序列

### Requirement: 大盘资金流必须按单一工具暴露沪深整体
系统 MUST 以单一工具向 CLI、MCP、HTTP API、Web 管理后台暴露东财大盘资金流（沪深整体）。工具契约 MUST 接受可选的 `trade_date`、`start_date`、`end_date` 三参数。返回字段 MUST 同时包含沪市与深市两组（`close_sh / pct_change_sh / close_sz / pct_change_sz`）以及大盘整体 `net_amount` 与 `net_amount_rate`。

#### Scenario: 单日全市场快照
- **WHEN** 调用方仅传 `trade_date`
- **THEN** 系统返回该日的沪深大盘资金流单条记录

### Requirement: 资金流必须先完成上游对齐再实现 provider
系统 MUST 在为板块或大盘资金流 capability 实现或修改 provider 适配前，先完成对 tushare `moneyflow_ind_dc` / `moneyflow_mkt_dc` 的上游对齐，并以原始接口返回确认字段含义、单位、更新时效与 `content_type` 的允许值。

#### Scenario: 上游对齐确认字段单位
- **WHEN** 维护方为资金流 provider 改造或新增
- **THEN** 必须已记录 `net_amount / buy_*_amount` 的单位（万元 → 元换算）
- **AND** 必须已记录 `pct_chg / net_amount_rate` 是百分比

### Requirement: 资金流的字段单位必须经 provider 显式换算
系统 MUST 在 provider 适配层完成 tushare 原始字段到项目统一单位的换算：金额类字段（`net_amount`、`buy_elg_amount`、`buy_lg_amount`、`buy_md_amount`、`buy_sm_amount` 等）单位为万元，必须 × 10000 转为元；百分比字段（`pct_chg`、`net_amount_rate`）保持百分比形式。

#### Scenario: 金额单位与日线一致
- **WHEN** 调用方收到资金流数据
- **THEN** 所有金额字段单位 MUST 是「元」，与 `kline-history` 日线 `amount` 字段单位一致

### Requirement: 资金流必须显式声明数据更新时效
系统 MUST 在工具契约或文档中显式声明：板块资金流与大盘资金流均为 T+1 17:00 左右更新；当日盘中数据 MUST NOT 被视为最终值。

#### Scenario: 调用方知悉更新时效
- **WHEN** 调用方查阅资金流工具描述
- **THEN** 描述 MUST 显式说明 T+1 17:00 更新

### Requirement: 资金流单源 tushare 必须显式声明
系统 MUST 在工具契约或文档中声明板块与大盘资金流均为 tushare 单源，无 fallback。

#### Scenario: 上游不可用时的容错
- **WHEN** tushare 接口不可用
- **THEN** service MUST 抛出 `DataFetchError`
- **AND** MUST NOT 静默回退到任何未验收的 provider

