## MODIFIED Requirements

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
