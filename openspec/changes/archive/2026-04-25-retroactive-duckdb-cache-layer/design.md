## Context

本 change 是对 fe01b51（2026-04-18）的 retroactive 合规。该 commit 一次性合入了两件**性质不同**的变更：

- **A. 基础设施新增**：DuckDB 缓存层 + 17 个 tushare provider 接入。
- **B. Breaking change**：`pct_change → pct_chg` 字段名全量统一（4 个 interface、tencent client、registry return_fields）。

按 governance「proposal 应聚焦一个逻辑意图，禁止把无关重构混入同一个 change」的纪律，fe01b51 当时的合并方式存在缺陷：缓存层接入与字段重命名应是两个独立 change。但事实已成定局，本 retroactive 把两者**用两个独立 capability** 分离声明，作为对历史合规化的最佳近似：

- `cache-layer` capability：DuckDB 缓存层行为契约。
- `field-naming` capability：字段命名规范，把 `pct_chg` 提升为项目级约定。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec capability | `cache-layer`、`field-naming`（新增） | ADDED Requirements |
| 历史 commit | fe01b51 | 引用 |
| 实际接入代码 | 33 个文件（cache 层 + 17 provider + 4 interface + 测试） | 不修改 |
| 后续清理 | 阶段 3 `cleanup-config-and-proxy-leftovers` 将清理 `os.environ.get("FINANCE_DATA_CACHE")` 遗留 | 引用 |

## Goals / Non-Goals

**Goals:**
- 把 fe01b51 的两件结构性变更各自沉淀为独立 capability，避免「缓存层 + 字段命名」继续混淆。
- 在 spec 中显式记录 breaking change（`pct_change → pct_chg`），让下游接入方有迹可查。
- 把「缓存写责任不在 read 路径」「测试必须关闭缓存」「resolver 三个入口语义」等关键约束沉淀为正式规范。
- 为阶段 3 的「清理 `os.environ.get('FINANCE_DATA_CACHE')` 遗留」提供 spec 依据：cache-layer Requirement「必须可被显式关闭」承认开关存在，但不规定通过环境变量实现，给阶段 3 改用 `config.toml` 留出空间。

**Non-Goals:**
- 不修改任何 src/ 代码。
- 不评估 DuckDB 是否合适、不引入其他 provider 的缓存接入。
- 不在本 change 完成「`pct_change` validator」（spec 中标记为 SHOULD，作为 backlog）。
- 不评估 fe01b51 当时是否应该拆 commit。

## Decisions

### 1. 拆为两个 capability 而非合并

**理由**：
- governance「proposal 应聚焦一个逻辑意图」的精神同样适用于 capability 划分。
- `cache-layer` 是横切基础设施，其 Requirement 描述「缓存机制行为」；`field-naming` 是项目级命名规范，其 Requirement 描述「字段名命名义务」。两者主体不同，不应合并。
- 拆分后，阶段 3 的清理 change 只需引用 `cache-layer`（讨论开关实现），无需触及 `field-naming`。

### 2. cache-layer 不规定开关具体实现

**理由**：
- fe01b51 当前用 `FINANCE_DATA_CACHE` 环境变量实现开关。
- 阶段 3 计划改为 `config.toml [cache] enabled` 配置项。
- 为给阶段 3 留空间，cache-layer Requirement 写「调用方 MUST 能通过单一开关显式关闭」，不规定开关的具体实现形式（环境变量 / TOML / CLI 标志均可）。
- 这也符合 governance「rules 仅定义边界不规定具体写法」的精神。

### 3. field-naming 的 validator 写为 SHOULD 而非 MUST

**理由**：
- validator 实现是工程动作，不在本 retroactive 范围（不修代码原则）。
- 用 SHOULD 表达「期望」，让该 Requirement 同时承担 backlog 引导作用：未来 change 看到 SHOULD 自动会想到「是否该升级为 MUST + 实现 validator」。
- 与 RFC 2119 一致：MUST 是绝对要求，SHOULD 是强烈建议但允许例外。

### 4. cache 写责任与读路径解耦

**理由**：
- fe01b51 中 cache resolver 仅负责读，不在 cache miss 后自动写回。
- 这是有意设计：写责任在独立的下载脚本（aa87952 的 retroactive-baostock-minute-kline 之外的 retroactive 4 中处理：`retroactive-config-toml-consolidation` —— 注：这是另一个 retroactive，不是本 change）。
- spec 中显式记录该解耦决定，避免未来误把「自动写回」当成 cache-layer 的隐含需求。

### 5. 不在本 change 提及 fe01b51 应拆分

**理由**：
- retroactive 的纪律是「追认事实，不追溯责任」。
- proposal 与 design 中已经隐含了「按理应该拆分」的批评（「fe01b51 的合并方式存在缺陷」），但不要在 spec 中留痕（spec 是行为契约，不是历史评论）。
- 未来类似情况由 governance 中的 proposal rules「一个 change 只聚焦一个逻辑意图」实时阻止。

## Source-of-Truth 映射（实施 → spec）

| 实施事实 | 来源 | 对应 Requirement |
| --- | --- | --- |
| `FINANCE_DATA_CACHE=0` 关闭开关 | `cache/resolver.py:41` | cache-layer「默认启用且可被显式关闭」 |
| T-1 规则（今天数据不缓存） | `cache/resolver.py` _today + 比较逻辑 | cache-layer「T-1 规则避免读到未稳定数据」 |
| 三个 resolver 入口（fetch_cached / fetch_cached_range / resolve） | `cache/resolver.py` 函数定义 | cache-layer「三个语义清晰的查询入口」 |
| 17 provider 接入「先查 cache 再调 API」 | provider/tushare/* 的 fe01b51 diff | cache-layer「tushare provider 接入缓存必须遵循统一模式」 |
| `tests/conftest.py` 禁用缓存 | tests/conftest.py 4 行新增 | cache-layer「不得绕过测试 mock」 |
| read 路径不写回 cache | provider 代码无 `cache.write()` 调用 | cache-layer「写入责任与读路径必须解耦」 |
| 4 个 interface 字段 pct_change → pct_chg | interface/{hot_rank,lhb,pool,sector_fund_flow}/* | field-naming「涨跌幅字段必须统一命名为 pct_chg」 |
| breaking 未在原 commit 显式声明 | fe01b51 commit message 仅在「字段名统一」段落简述 | field-naming「字段命名 breaking change 必须显式声明」 |

## Risks / Trade-offs

- [Risk] 阶段 3 改用 `config.toml` 后，「FINANCE_DATA_CACHE 环境变量」是否仍兼容？  
  → Mitigation: 阶段 3 自己决策。本 change 的 cache-layer Requirement 不规定开关形式，给阶段 3 留出空间。

- [Risk] 「validator 守护字段名」的 SHOULD 永远不被实现。  
  → Mitigation: 接受。SHOULD 表达期望即可；未来若 `pct_change` 错误重新出现，可由独立 change 升级为 MUST 并实现。

- [Risk] cache-layer 不显式约束「写入责任」具体由谁承担。  
  → Mitigation: 当前由 aa87952 的 download 脚本承担；若未来变更，在对应 capability 的 spec 中说明，不破坏本 retroactive 的 cache-layer 约束。

- [Risk] field-naming 仅声明 `pct_chg`，未来其他字段的命名（如 `volume` vs `vol` vs `成交量`）没有统一约束。  
  → Mitigation: 接受。本 retroactive 仅追认已发生的 breaking。其他字段命名规范若需要，独立 change 处理。

## Migration Plan

1. 创建 4 份制品（proposal / design / tasks / acceptance）；不需要 upstream-alignment（不接入新数据源）。
2. 创建 2 个 ADDED spec：`cache-layer`（6 条 Requirement）+ `field-naming`（3 条 Requirement）。
3. `openspec validate retroactive-duckdb-cache-layer --strict` 通过。
4. 写 acceptance.md，标记「validator 守护未实现」为 backlog。
5. `openspec archive retroactive-duckdb-cache-layer -y`，自动落地两个新 capability。
6. 与阶段 3 衔接：阶段 3 实施前先核对 cache-layer Requirement 是否给「config.toml 开关」留出空间，确认后才能改 `cache/resolver.py:41`。

回滚策略：纯文档动作，回滚为 `git revert` 即可。

## Open Questions

- 是否要把「cache 写责任」也提升为 capability（如 `cache-write`）？  
  → 暂不。aa87952 的 download 脚本是独立工具，与运行时无关；若未来引入「自动写回」需求，再开 capability。
- `pct_chg` 之外的字段命名是否需要统一规范（如所有「成交量」字段必须用 `volume`）？  
  → 不在本 retroactive 范围，留作 backlog。
