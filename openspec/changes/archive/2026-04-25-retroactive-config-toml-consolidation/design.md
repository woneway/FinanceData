## Context

本 change 是对 1e0ae0b（2026-04-19）的 retroactive 合规。该 commit 是 FinanceData 自上线以来规模最大的 refactor，70 个文件、325 行新增、1816 行删除，包含三件结构性变更：

- **A. 配置统一**：新建 `config.py` + `config.toml`，替代环境变量；service / client 层全量迁移；新增 `daily_basic.volume_ratio` fallback。
- **B. 大规模死代码清理**：删除 `KlineHistoryProtocol` 旧方法、`xueqiu/kline`、`baostock/kline`、`sector_fund_flow`、`akshare` 禁用占位等。
- **C. 治理空白**：未声明配置 / API / capability 三类 breaking。

按 governance「proposal 应聚焦一个逻辑意图」纪律，1e0ae0b 实际混合了三件 change。本 retroactive 用 `configuration` capability 把「最具结构性的 A」沉淀，B 和 C 在 design.md 中纪录为「已发生事实」，不进入 spec（spec 只覆盖前向约束）。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec capability | `configuration`（新增） | ADDED Requirements |
| 历史 commit | 1e0ae0b | 引用 |
| 实际接入代码 | 70 个文件（详见 git stat） | 不修改 |
| 后续清理 | 阶段 3 `cleanup-config-and-proxy-leftovers` 处理 `cache/resolver.py:41` 与 `_proxy.py` 残余 | 引用 |

## Goals / Non-Goals

**Goals:**
- 把 1e0ae0b 引入的配置统一规范沉淀为 `configuration` capability，覆盖 6 条 Requirement：唯一事实来源 / 不入 git / helper 模式 / 缺省语义 / token 缺失降级 / 缺失文件错误信息。
- 在 spec 中显式约束「残余环境变量读取必须显式追踪」，为阶段 3 提供前置依据。
- 给 1e0ae0b 中删除的 capability（sector_fund_flow）和废弃的 client 构造函数参数（token / url）留下追溯路径（design.md「Context」段）。

**Non-Goals:**
- 不修改任何 src/ 代码、不改 `config.py` API、不评估是否回退到环境变量。
- 不重新评估 `sector_fund_flow` 删除是否合理。
- 不在 spec 中追责 1e0ae0b 当时未拆 commit。
- 不修改 `daily_basic.volume_ratio fallback` 行为。
- 不在本 change 实现「残余 os.environ.get 扫描守护」（独立 backlog）。

## Decisions

### 1. 仅沉淀「配置统一」为 capability，B / C 类变更只在 design.md 留痕

**理由**：
- A（配置统一）有清晰的前向约束，可写为 capability Requirement。
- B（死代码清理）是一次性物理动作，没有持续约束意义；spec 中沉淀「禁止再写死代码」无法落地（什么算死代码本身就是判断题）。
- C（治理空白）是 governance Requirement 已经覆盖的元约束，不需要 capability 层再重复。

### 2. spec 显式包含「残余 os.environ.get 必须追踪」

**理由**：
- 当前确实存在残余（`cache/resolver.py:41` 的 `FINANCE_DATA_CACHE`、`provider/akshare/_proxy.py:13,16` 的 `no_proxy`）。
- spec 只规定「必须追踪」，给阶段 3 留出实现空间（迁到 `[cache] enabled` / `[proxy] no_proxy_hosts` 配置）。
- 不在本 change 修这些残余（retroactive 纪律）。

### 3. token 缺失时显式降级而非「调用时抛错」

**理由**：
- 1e0ae0b 实际实现是 service `_build_*()` 在加载时根据 `has_tushare_token()` 决定是否加入 tushare provider。这是「装配阶段降级」而非「调用阶段抛错」。
- spec 明确这一行为，避免未来误改成「装配总是加 tushare，调用时抛 auth」。
- 与 cache-layer「写入责任与读路径解耦」类似，明确装配路径与调用路径的责任。

### 4. 不在 spec 中规定具体的 `[tushare]` / `[xueqiu]` TOML 字段名

**理由**：
- TOML 字段名是实现细节，应由 `config.toml.example` 与 `config.py` helper 函数共同决定。
- spec 只约束「helper 行为」与「缺省语义」，这是真正的行为契约。
- 避免 spec 与代码的字段名出现 drift（spec 写 `tushare.token` 但代码改成 `tushare.api_token`）。

### 5. `volume_ratio` fallback 不进入本 capability

**理由**：
- `daily_basic.volume_ratio` 缺失时从 `stk_factor_pro` fallback 是业务逻辑，与配置无关。
- 应归属 `daily-basic` 或类似业务 capability。当前没有该 capability，本 retroactive 不创建（不超出 scope）。
- 该业务 fallback 由 retroactive-tushare-stk-factor-pro 间接覆盖（technical-factors capability 的 stk_factor_pro 是 fallback 源），但未显式记录跨 capability 的 fallback 链。留作 backlog。

## Source-of-Truth 映射（实施 → spec）

| 实施事实 | 来源 | 对应 Requirement |
| --- | --- | --- |
| `config.py` + `config.toml` 唯一来源 | 1e0ae0b 新增 `src/finance_data/config.py` | configuration「项目配置必须以 config.toml 为唯一事实来源」 |
| `.gitignore` 排除 config.toml | 已在 .gitignore 中 | configuration「敏感配置不得进入 git」 |
| `config.toml.example` 模板 | 已存在 | configuration「敏感配置不得进入 git」 |
| `@lru_cache(maxsize=1)` 单次读盘 | `config.py:_load()` | configuration「config.py 必须用 helper 函数封装」 |
| `get_xueqiu_cookie()` 缺失返回空字符串 | `config.py:30` | configuration「可选配置必须有明确的缺省语义」 |
| `has_tushare_stock_minute_permission()` 缺失返回 False | `config.py:41` | configuration「可选配置必须有明确的缺省语义」 |
| service `_build_*()` 装配阶段跳过 tushare | service/*.py 的 fe01b51 + 1e0ae0b diff | configuration「tushare token 缺失时 service 层必须显式降级」 |
| `_load()` 缺文件抛 FileNotFoundError 含修复指引 | `config.py:13-16` | configuration「config.toml 缺失时进程必须给出清晰错误」 |

## Risks / Trade-offs

- [Risk] spec 要求「残余 `os.environ.get` 必须追踪」，但当前确实有残余。  
  → Mitigation: 该残余即将由阶段 3 清理。本 change 的 acceptance.md 明确把残余记为「待跟进 drift」，与阶段 3 形成强 handoff。

- [Risk] spec 不规定具体 TOML 字段名，未来若 helper 函数与字段名脱节，难以定位。  
  → Mitigation: 由 `config.toml.example` 作为字段名权威来源；`config.py` helper 函数与之同步是工程纪律，不是 spec 约束。

- [Risk] `daily_basic.volume_ratio` fallback 未进入任何 capability。  
  → Mitigation: 记为 backlog，开 `add-daily-basic-capability` 时一并补。

- [Risk] sector_fund_flow 删除是「物理删除」，未来若想恢复需要重新设计 capability。  
  → Mitigation: 接受。git history 即追溯路径。

## Migration Plan

1. 创建 4 份制品（proposal / design / tasks / acceptance）；不需要 upstream-alignment（不接入新数据源）。
2. 创建 ADDED spec：`configuration`（6 条 Requirement）。
3. `openspec validate retroactive-config-toml-consolidation --strict` 通过。
4. 写 acceptance.md，标记残余 `os.environ.get` 为「待跟进 drift」并指向阶段 3。
5. `openspec archive retroactive-config-toml-consolidation -y`，自动落地 `configuration` capability。
6. 与阶段 3 衔接：阶段 3 实施前先核对 configuration Requirement「残余环境变量读取必须显式追踪」，作为「为何要清理 FINANCE_DATA_CACHE 与 no_proxy」的 spec 依据。

回滚策略：纯文档动作，回滚为 `git revert` 即可。

## Open Questions

- 是否要把「config.toml.example 字段名权威」也写为 capability？  
  → 不。example 文件本身就是事实。
- 是否要扫描所有 src 文件确认没有 `tomllib.load()` 直接读盘？  
  → 留作 backlog，可作为「configuration validator」change 实现。
