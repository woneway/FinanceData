## Context

阶段 2.4 retroactive-config-toml-consolidation 在 acceptance.md 中显式 handoff 两项 spec drift 给本 change：

- `src/finance_data/cache/resolver.py:39-41` 用 `os.environ.get("FINANCE_DATA_CACHE", "1")` 控制缓存开关。
- `src/finance_data/provider/akshare/_proxy.py:13-16` 硬编码 `eastmoney.com,.eastmoney.com` 作为 hosts，再写 `os.environ["no_proxy"]`。

阶段 1 `kline-history` 第 5 条 Requirement「东财 fallback 必须配置代理绕过」在当前代码中 100% 覆盖（6 个 akshare 东财 provider 全部调用 `ensure_eastmoney_no_proxy()`），但纯靠维护者记忆 —— 缺自动化守护。

本 change 是**阶段性优化路线图中第一个动代码的 change**。三类风险并存：
1. `tests/conftest.py` 改动可能破坏现有 mock。
2. `ensure_eastmoney_no_proxy()` 接口签名改变可能影响已经调用它的 6 个 provider。
3. `FINANCE_DATA_CACHE` breaking 影响外部用户脚本。

按 governance「apply 阶段必须先做守护测试」的精神，采用「**守护测试先行 → helper 引入 → 配置迁移 → 残余清理**」的串行节奏，每步独立可回滚。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec | `proxy-bypass`（新建） + `configuration / cache-layer / kline-history`（MODIFIED） | ADDED + MODIFIED + REMOVED |
| 配置入口 | `config.toml` + `config.py` helper | 新增 `[cache]` 与 `[proxy]` 段 + 2 个 helper |
| 守护测试 | `tests/provider/akshare/test_proxy_guard.py` | 新增（AST 扫描） |
| 残余清理 | `cache/resolver.py:39-41` + `provider/akshare/_proxy.py:13-16` | 改实现，对外行为兼容 |

## Goals / Non-Goals

**Goals:**
- 全量清理 `os.environ.get("FINANCE_DATA_*")` 残余（仅 cache 一处）。
- 把 `_proxy.py` 内硬编码 hosts 提到配置层，仍保留 akshare 必需的 `os.environ["no_proxy"]` 写入。
- 引入 AST 守护测试锁定「东财 provider 必须绕代理」不变量。
- 把分散在 `kline-history` 的代理绕过 Requirement 收敛到独立 `proxy-bypass` capability。
- conftest.py 不再用环境变量禁用缓存，改用 monkeypatch helper（更显式、更可控）。

**Non-Goals:**
- 不修改 akshare 内部「靠 `no_proxy` 环境变量决定是否绕代理」的事实。
- 不重写其他 provider 的 init 流程。
- 不实施 `pct_chg` validator（阶段 2.3 backlog）。
- 不实施 `tomllib.load()` 直接读盘扫描守护（独立 backlog）。
- 不增加 `config.toml` 之外的配置入口（如 CLI 标志、`.env` 等）。

## Decisions

### 1. 新建 proxy-bypass capability 而非把 Requirement 留在 kline-history

**理由**：
- 「东财绕代理」是横切关注点，影响 lhb / suspend / hot_rank / north_flow / pool / kline 等 6+ provider，按 capability 应属横切而非业务 domain。
- kline-history 是 K 线行为契约，强行包含「代理绕过」违反 SDD「按行为契约划分 capability」原则。
- 独立 capability 让阶段 4-5 拆分大文件时，proxy-bypass Requirement 不会被误删除或漏迁。

### 2. ensure_eastmoney_no_proxy 函数签名保持兼容

**理由**：
- 6 个 provider 已经调用 `ensure_eastmoney_no_proxy()`（无参）。改签名会触发 6 处 provider 修改 + 测试影响。
- 新方案：函数内部读 `get_no_proxy_hosts()`，调用方无感知。
- 配置项缺省时 helper 返回 `["eastmoney.com", ".eastmoney.com"]`，与现有硬编码完全等价，零行为变更。

### 3. is_cache_enabled() 缺省 True，与历史一致

**理由**：
- 历史 `FINANCE_DATA_CACHE` 缺省 "1"（启用）；新 `[cache] enabled` 缺省 `True`，行为对齐。
- 避免「升级后 cache 被关闭」这种沉默回归。
- 测试 conftest 显式设为 `False`，与历史 `FINANCE_DATA_CACHE=0` 等价。

### 4. tests/conftest.py 改用 monkeypatch helper 而非写 config.toml

**选项**：
- A. conftest 写一个临时 `config.toml`（污染文件系统）。
- B. conftest monkeypatch `is_cache_enabled` 返回 False（运行时拦截）。

**选择 B**。

**理由**：
- A 会破坏开发者本地 `config.toml`。
- B 仅修改运行时函数返回，不动文件，最小副作用。
- 对应实现：在 conftest 中 `import finance_data.config; finance_data.config.is_cache_enabled = lambda: False`。
- 可选优化：用 pytest fixture + autouse 包装；当前 conftest 仅 4 行，简单 monkeypatch 即可。

### 5. AST 守护测试用「文件级文本扫描」而非「真实 import + AST 解析」

**选项**：
- A. 真实 import 每个 provider 模块，用 `ast.parse` 检查模块体。
- B. 直接用 `pathlib + str.contains` 文本扫描每个 .py 文件。

**选择 B**。

**理由**：
- A 触发 import 副作用（akshare 加载），慢且可能因网络失败。
- B 无副作用，速度快，逻辑简单：扫描每个 .py 文件，正则匹配 `_em\b` 或 `stock_zh_a_hist\b` 的 import 行 → 若匹配，断言文件包含 `ensure_eastmoney_no_proxy()` 调用。
- 准确度足够：AST 在本场景没有显著优势，且 false positive / false negative 均易于人工审查。
- 实现 < 30 行，可读性高。

### 6. proxy-bypass Requirement 把 stock_zh_a_hist 也纳入「东财已知函数」

**理由**：
- `ak.stock_zh_a_hist`（无 `_em` 后缀）实际也走东财（与「日线历史」上游对齐文档一致）。
- 守护测试逻辑必须显式包含此函数名，否则误漏。
- spec 中显式声明该名单，未来发现新的「东财但无 `_em` 后缀」函数时，按 spec 加入扫描清单。

### 7. cache-layer MODIFIED 的「显式关闭」Scenario 改为指向 config.toml

**理由**：
- 阶段 2.3 cache-layer 第 1 条 Requirement Scenario 写「`FINANCE_DATA_CACHE=0`」，实施后该入口将不存在 → spec drift。
- 本 change MODIFIED 同时调整该 Scenario 文本指向 `config.toml [cache] enabled = false`，并显式新增「FINANCE_DATA_CACHE 环境变量不再生效」Scenario，避免日后被误以为可用。

## Risks / Trade-offs

- [Risk] 现有用户依赖 `FINANCE_DATA_CACHE=0` 关闭缓存，本 change 后失效。  
  → Mitigation: proposal 显式标注 breaking + 给出 `config.toml [cache] enabled = false` 迁移指引；CLAUDE.md / config.toml.example 同步更新。

- [Risk] conftest.py monkeypatch 在某些测试 import 时机晚于其他 fixture，可能仍读到 `is_cache_enabled() = True`。  
  → Mitigation: monkeypatch 直接在 conftest 模块顶层执行（pytest 加载 conftest 时立即生效），先于任何测试模块 import。验证方式：跑全量 pytest 必须绿。

- [Risk] AST 守护测试对未来引入「真实 mock akshare 的测试」可能误报。  
  → Mitigation: 守护只扫 `src/finance_data/provider/akshare`，不扫 `tests/`。

- [Risk] `_proxy.py` 内 hosts 列表来源切换可能与 akshare 版本兼容性细节冲突。  
  → Mitigation: 缺省回退到 `["eastmoney.com", ".eastmoney.com"]` 与原硬编码 1:1 等价；行为零变更。

- [Risk] 守护测试如果实现不当，可能阻断未来「akshare 不再走东财」的合理重构。  
  → Mitigation: 守护测试基于「import _em / stock_zh_a_hist」触发条件；如果未来 provider 不再 import 此类函数，自然不被守护检查。

## Migration Plan

按「守护测试先行」原则严格串行：

1. **守护测试先行**：新建 `tests/provider/akshare/test_proxy_guard.py`，跑过证实当前 6 个 provider 100% 通过；故意删除某 provider 的 `ensure_eastmoney_no_proxy()` 调用 → 测试 FAIL → 恢复。
2. **config.py 加 helper**：新增 `is_cache_enabled()` 与 `get_no_proxy_hosts()`，附 `@lru_cache`。
3. **改 _proxy.py**：`ensure_eastmoney_no_proxy()` 内部读 `get_no_proxy_hosts()`；签名不变。跑全量 pytest 验证。
4. **改 cache/resolver.py**：`_is_cache_enabled()` 改读 `is_cache_enabled()`；删除 `import os`（若无其他用途）。
5. **改 conftest.py**：monkeypatch `finance_data.config.is_cache_enabled = lambda: False`；删除环境变量写入。跑全量 pytest 验证（含新守护测试）。
6. **更新 config.toml.example**：增 `[cache] enabled = true` 与 `[proxy] no_proxy_hosts = [...]`。
7. **acceptance.md**：记录 spec drift 已清零、breaking 已显式声明。
8. **archive**：`openspec archive cleanup-config-and-proxy-leftovers -y`。

回滚策略：每一步都是独立 commit / 文件修改，可单点 `git revert`。守护测试合入后即使其余步骤失败，也仅是测试红，不破坏运行时。

## Open Questions

- 是否需要在 `config.toml.example` 中加注释说明「false 等价于历史的 FINANCE_DATA_CACHE=0」？  
  → 是。提升可发现性。
- 守护测试是否要扫描 `tests/` 中的 fixture 是否绕过了 `ensure_eastmoney_no_proxy`？  
  → 否。tests/ 通常 mock akshare，不会真实访问东财；守护只锁 src/。
