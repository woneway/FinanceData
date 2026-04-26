# cache-layer Specification

## Purpose
TBD - created by archiving change retroactive-duckdb-cache-layer. Update Purpose after archive.
## Requirements
### Requirement: 缓存层必须默认启用且可被显式关闭
系统 MUST 默认启用 DuckDB 本地缓存层；调用方 MUST 能通过 `config.toml [cache] enabled = false` 显式关闭缓存（替代历史的 `FINANCE_DATA_CACHE` 环境变量）。当缓存关闭时，所有读请求 MUST 直接落回上游 API，不查任何本地缓存。

#### Scenario: 默认启用
- **WHEN** 调用方未做任何配置就调用任一接入缓存的 provider
- **THEN** 缓存层 MUST 介入查询本地缓存
- **AND** cache hit 时 MUST 跳过上游 API 调用

#### Scenario: 通过 config.toml 显式关闭
- **WHEN** 维护方在 `config.toml` 设置 `[cache] enabled = false`
- **THEN** 所有 provider MUST 直接调用上游 API
- **AND** `cache resolver` MUST NOT 查询任何本地缓存表

#### Scenario: 测试环境默认关闭缓存
- **WHEN** pytest 加载 `tests/conftest.py`
- **THEN** 缓存开关 MUST 被设置为关闭（实现：monkeypatch helper 或写入 config）
- **AND** 任一 provider 测试中 mock 的 API 调用 MUST 实际生效，不被 cache hit 绕过

#### Scenario: 历史 FINANCE_DATA_CACHE 环境变量不再生效
- **WHEN** 维护方仅设置 `FINANCE_DATA_CACHE=0` 但未改 `config.toml`
- **THEN** 缓存 MUST 仍按 `config.toml` 中 `[cache] enabled` 决定（默认 `true`）
- **AND** 该环境变量 MUST NOT 被代码读取

### Requirement: 缓存层必须遵循 T-1 规则避免读到未稳定数据
系统 MUST 在读缓存时排除「今天」的数据（按调用时机的本地日期判断）。今天的数据 MUST 始终从上游 API 读取，避免读到隔夜未更新或盘中变化的数据。

#### Scenario: 今天数据不命中缓存
- **WHEN** 调用方请求 `trade_date = 今天`
- **THEN** 缓存层 MUST NOT 返回缓存数据
- **AND** provider MUST 落回上游 API 调用

#### Scenario: T-1 及更早数据可命中
- **WHEN** 调用方请求 `trade_date = 昨天或更早`
- **AND** 该日数据已存在于缓存表中
- **THEN** 缓存层 MUST 返回缓存数据
- **AND** provider MUST 跳过上游 API 调用

### Requirement: 缓存层必须提供三个语义清晰的查询入口
系统 MUST 在 cache resolver 中暴露三个查询入口，分别对应不同查询模式：

- 单日查询：按精确 `trade_date` 取数；命中则返回 DataFrame，否则返回 `None`。
- 范围查询：按 `[start_date, end_date]` 区间取数；当且仅当区间内全部交易日都在缓存中时返回，否则返回 `None`（避免静默返回部分数据）。
- 统一入口：根据传入参数自动选择上述两种模式之一。

#### Scenario: 单日查询命中
- **WHEN** 调用方传 `trade_date` 且该日已缓存
- **THEN** 返回该日 DataFrame

#### Scenario: 范围查询全覆盖才命中
- **WHEN** 调用方传 `[start_date, end_date]` 且区间内有任一交易日缺失
- **THEN** MUST 返回 `None`
- **AND** MUST NOT 返回部分匹配的数据

### Requirement: tushare provider 接入缓存必须遵循统一模式
系统中接入缓存的 tushare provider MUST 在调用 tushare API 前先查 cache resolver；当 cache resolver 返回 `None`（cache miss 或缓存关闭）时再调用 tushare API。provider 不允许：
- 在 cache hit 时仍调用 API。
- 用 `df = fetch_cached(...) or pro.xxx(...)` 这种短路写法（pandas DataFrame 不支持 bool 评估）。
- 自行实现独立的缓存逻辑，绕过 resolver。

#### Scenario: cache hit 跳过 API
- **WHEN** provider 调用 `fetch_cached()` / `fetch_cached_range()` / `resolve()` 之一
- **AND** 返回非 `None`
- **THEN** provider MUST 直接使用返回的 DataFrame
- **AND** MUST NOT 再调用 tushare API

#### Scenario: cache miss 落回 API
- **WHEN** cache resolver 返回 `None`
- **THEN** provider MUST 调用对应的 tushare API
- **AND** 写入缓存表的责任不在本 change scope（由独立下载脚本承担）

### Requirement: 缓存层不得绕过测试 mock
系统 MUST 保证测试环境中 mock 的 tushare API 调用不会被缓存绕过。具体方式：测试 conftest 必须显式关闭缓存。

#### Scenario: 测试环境默认关闭缓存
- **WHEN** pytest 加载 `tests/conftest.py`
- **THEN** 缓存开关 MUST 被设置为关闭
- **AND** 任一 provider 测试中 mock 的 API 调用 MUST 实际生效，不被 cache hit 绕过

### Requirement: 缓存层的写入责任与读路径必须解耦
系统的缓存层在 fe01b51 接入时仅负责「读」。缓存表的「写」责任 MUST 由独立的下载脚本承担，provider 在 cache miss 时调用 API 的返回值 MUST NOT 被自动写回缓存。

#### Scenario: 读路径不写缓存
- **WHEN** provider 在 cache miss 后调用 API 拿到数据
- **THEN** 该数据 MUST NOT 被自动写入 DuckDB 缓存表
- **AND** 缓存表的填充由独立下载流程完成

