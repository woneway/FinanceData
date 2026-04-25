# RETROACTIVE — 历史合规化 change

> 本 change 为 fe01b51（2026-04-18，feat: DuckDB 缓存层接入 + pct_change→pct_chg 全量统一）的 retroactive 制品。该 commit 同时携带：
> 1. 一个**新基础设施**（DuckDB cache 层）；
> 2. 一项**字段名 breaking change**（`pct_change → pct_chg` 全量统一）。
> 本 retroactive 既追认基础设施，也将 breaking change 显式标注以便下游接入方可见。**不修改任何代码。**

## Why

fe01b51 commit 在 OpenSpec 流程外引入了两件结构性变更：

**A. DuckDB 缓存层（新基础设施）**
- 新增 `cache/db.py`（DuckDB 单连接 + `query_df` 通用查询）与 `cache/resolver.py`（`fetch_cached` 单日 / `fetch_cached_range` 范围 / `resolve` 统一入口）。
- 17 个 tushare provider 接入「cache hit 时跳过 API 调用」模式，覆盖 chip / daily_basic / daily_market / fund_flow / hot_rank / lhb / margin / market(auction) / pool / stk_limit / technical 等大半个 tushare provider 矩阵。
- 引入「T-1 规则」：今天的数据不从缓存读取（避免读到隔夜未更新数据）。
- 引入 `FINANCE_DATA_CACHE=0` 环境变量开关（测试时通过 `tests/conftest.py` 自动禁用）。
- 这是项目第一个跨 provider 的横切基础设施，需要 capability 显式记录其行为契约。

**B. pct_change → pct_chg 全量统一（breaking change）**
- 影响 4 个 interface 文件（hot_rank / lhb / pool / sector_fund_flow），共 ~10 处字段名变更。
- tencent client 输出 key 同步变更；registry return_fields 同步更新。
- 对 SDK 调用方（直接消费 `to_dict()` 或 DataFrame）构成 breaking：使用 `pct_change` 列名的脚本 / 表格在升级后会出现 `KeyError` 或 `Column not found`。
- 该 commit 未在 OpenSpec 中显式声明这一 breaking，未提供迁移指引，违反 governance「archive 必须确认 spec 与代码一致」要求。

阶段 0 / 阶段 1 已为 OpenSpec 治理立好基线，本 retroactive 用合规材料追认 fe01b51 这一关键基础设施 commit，并把 breaking change 提到 spec 层显式可见。

## What Changes

- 新增 `openspec/changes/archive/2026-04-25-retroactive-duckdb-cache-layer/` 历史合规归档：proposal / design / tasks / acceptance（不需要 upstream-alignment，因本 change 不接入新数据源）。
- 新增 `cache-layer` capability，定义 DuckDB 缓存层的行为契约（T-1 规则、cache hit 语义、禁用开关、写入责任）。
- 新增 `field-naming` capability，将 `pct_change → pct_chg` 提升为项目级字段命名规范，覆盖现有所有 dataclass 与未来新接入。
- 不修改任何 src/ 代码、不调整 cache 层接口签名、不重新讨论是否回滚 breaking。
- 非目标：不评估 DuckDB 是否合适、不引入其他 provider（akshare / xueqiu / baostock）的缓存接入、不在本 change 修阶段 3 即将清理的 `os.environ.get("FINANCE_DATA_CACHE")` 遗留。
- 兼容性：纯文档动作，运行时零影响；breaking change 已在 fe01b51 落地，本 retroactive 仅是事后声明。
- 上线风险：无。

## Capabilities

### New Capabilities
- `cache-layer`: DuckDB 本地缓存层的行为契约。覆盖：T-1 规则、cache hit 跳过 API、cache miss 落回 API、`FINANCE_DATA_CACHE` 开关、resolver 三个入口（`fetch_cached` / `fetch_cached_range` / `resolve`）的语义、tushare provider 接入约束。
- `field-naming`: 项目级字段命名规范。覆盖：`pct_chg` 作为统一涨跌幅字段名（弃用 `pct_change`）、跨 interface 一致性要求、新 provider 接入字段命名义务。

### Modified Capabilities
- 无。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：无。
- 历史 commit 追溯：fe01b51（2026-04-18，含 33 个文件变化、375 行新增、51 行删除）。
- 受影响 spec：新增 `openspec/specs/cache-layer/` 与 `openspec/specs/field-naming/`。
- 依赖：复用阶段 0 OpenSpec 治理 + 模板；与阶段 3 `cleanup-config-and-proxy-leftovers` 形成前后呼应（阶段 3 将清理 `FINANCE_DATA_CACHE` 环境变量遗留）。
