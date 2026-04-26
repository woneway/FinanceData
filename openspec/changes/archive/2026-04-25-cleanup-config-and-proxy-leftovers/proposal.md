## Why

阶段 2.4 的 `configuration` capability 第 1 条 Requirement 要求「项目配置必须以 config.toml 为唯一事实来源」+「残余环境变量读取必须显式追踪」。retroactive-config-toml-consolidation 的 acceptance.md 已显式记录两项 drift 待本 change 清理：

- `src/finance_data/cache/resolver.py:39-41` 仍调用 `os.environ.get("FINANCE_DATA_CACHE", "1")` —— 用环境变量控制 DuckDB 缓存开关。
- `src/finance_data/provider/akshare/_proxy.py:13-16` 仍调用 `os.environ.get("no_proxy", "")` 与 `os.environ["no_proxy"] = ...` —— 写入是 akshare 内部消费必需，但**初始 hosts 列表硬编码**。

同时阶段 1 `kline-history` 第 5 条 Requirement「涉及东财上游的周期 K 线 fallback 必须配置代理绕过」目前没有自动化守护：当前 6 个 akshare provider（lhb / lhb_inst_detail / suspend / hot_rank / north_flow / pool）都在模块顶部调用了 `ensure_eastmoney_no_proxy()`，但纯靠维护者记忆，新增 `_em` provider 时极易遗漏。

本 change 是阶段性优化路线图中**第一个动代码的 change**，按「守护测试先行 → 配置迁移 → 残余清理」顺序推进，并把守护规则提升为 spec。

## What Changes

- `cache/resolver.py:_is_cache_enabled()` 改为读 `config.toml [cache] enabled`，通过 `config.py` 新增 `is_cache_enabled()` helper 暴露。
- `provider/akshare/_proxy.py:ensure_eastmoney_no_proxy()` 内部 hosts 列表从 `config.toml [proxy] no_proxy_hosts` 读取（仍写入 `no_proxy` 环境变量供 akshare 内部消费）。`config.py` 新增 `get_no_proxy_hosts()` helper。
- `tests/conftest.py` 改用 monkeypatch `is_cache_enabled` 返回 False，不再写环境变量。
- `config.toml.example` 增 `[cache]` 与 `[proxy]` 两段示例配置。
- 新增 `tests/provider/test_proxy_guard.py`：AST 扫描 `provider/akshare/**/*.py`，凡 import `_em` 后缀函数（含 `stock_zh_a_hist` 这类已知东财源）的模块顶部 MUST 出现 `ensure_eastmoney_no_proxy()` 调用，违例 FAIL。
- 新建 `proxy-bypass` capability（独立单一职责），承接「东财绕代理」相关 spec Requirement（取代阶段 1 `kline-history` 中分散的代理绕过 Requirement）。
- `kline-history` MODIFIED：移除「涉及东财上游的周期 K 线 fallback 必须配置代理绕过」Requirement，迁到新 `proxy-bypass` capability。

**Breaking 影响**：
- `FINANCE_DATA_CACHE=0` 环境变量将不再生效。用户脚本若依赖该变量必须改 `config.toml [cache] enabled = false`。
- `os.environ["no_proxy"]` 仍由 `_proxy.py` 写入，对外行为兼容；新增的初始 hosts 来源是补充，不破坏。

**迁移指引**：
```toml
# config.toml 增补
[cache]
enabled = true  # 默认开启；测试或开发禁用 cache 改为 false

[proxy]
no_proxy_hosts = ["eastmoney.com", ".eastmoney.com"]  # 默认含东财
```

**非目标**：
- 不修改 `_proxy.py` 中 akshare 仍依赖 `os.environ["no_proxy"]` 写入的事实（akshare 内部行为不可控）。
- 不重写其他 provider 的 init 流程。
- 不在本 change 实现 `pct_chg` validator（阶段 2.3 backlog）。
- 不实施 `tomllib.load()` 直接读盘的扫描守护（独立 backlog）。

## Capabilities

### New Capabilities
- `proxy-bypass`: 东财（及未来其它必须绕代理的源）的代理绕过行为契约。覆盖：模块层强制绕代理、no_proxy hosts 配置来源、AST 守护测试、新增 `_em` provider 时的强制接入义务。

### Modified Capabilities
- `configuration`: MODIFIED 第 1 条 Requirement「项目配置必须以 config.toml 为唯一事实来源」—— 补 1 个 Scenario 验证 cache 开关已迁到 config.toml；MODIFIED 第 4 条「可选配置必须有明确的缺省语义」—— 增加 `[cache] enabled` 与 `[proxy] no_proxy_hosts` 的缺省语义说明。
- `kline-history`: REMOVED 「涉及东财上游的周期 K 线 fallback 必须配置代理绕过」Requirement，迁移至 `proxy-bypass`。
- `cache-layer`: MODIFIED 「缓存层必须默认启用且可被显式关闭」—— 把「显式关闭」的 Scenario 从「FINANCE_DATA_CACHE=0」改为「config.toml [cache] enabled = false」。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：`src/finance_data/cache/resolver.py`、`src/finance_data/config.py`、`src/finance_data/provider/akshare/_proxy.py`、`tests/conftest.py`、`config.toml.example`。
- 新增代码：`tests/provider/test_proxy_guard.py`。
- 受影响 spec：3 个 capability MODIFIED + 1 个 capability ADDED。
- 测试影响：全量 pytest 必须绿；新守护测试故意去掉某 provider 的 ensure 调用必须红。
- 依赖：复用阶段 0 OpenSpec 治理 + 模板；阶段 2.3 cache-layer 的「不规定开关具体实现」Decision 给本 change 留出空间；阶段 2.4 configuration 的「残余环境变量必须显式追踪」是本 change 的强 handoff 入口。
