# RETROACTIVE — 历史合规化 change

> 本 change 为 1e0ae0b（2026-04-19，refactor: config.toml 统一配置 + 清理全部死代码）的 retroactive 制品。该 commit 是 FinanceData 自上线以来**规模最大**的 refactor：70 个文件、325 行新增、1816 行删除。**不修改任何代码。**

## Why

1e0ae0b commit 在 OpenSpec 流程外完成了三件结构性变更：

**A. 配置统一（核心）**
- 新增 `config.py` 模块（`get_tushare_token` / `get_tushare_api_url` / `get_xueqiu_cookie` / `has_tushare_token` / `has_tushare_stock_minute_permission`）。
- 新增 `config.toml` 作为配置唯一事实来源，替代环境变量（`TUSHARE_TOKEN` / `TUSHARE_API_URL` / `XUEQIU_COOKIE` / `TUSHARE_STOCK_MINUTE_PERMISSION` 等）。
- 全部 service 层从 `os.getenv` 迁移到 `has_tushare_token()` 等 config API。
- `client.py` 构造函数去掉 `token` / `url` 参数（强制走 `config.toml`）。
- 业务增强：`daily_basic` 的 `volume_ratio` 缺失时从 `stk_factor_pro` fallback。

**B. 大规模死代码清理**
- 删除 `KlineHistoryProtocol` 和所有 provider 的 `get_kline_history` 旧方法（被 `daily/weekly/monthly` 拆分替代后遗留）。
- 删除 `xueqiu/kline`、`baostock/kline`（仅有旧 `get_kline_history` 方法）。
- 删除 `sector_fund_flow`（service + provider + interface，整 capability 下线）。
- 删除 akshare 的 `cashflow / stock / realtime` 禁用占位文件。
- 删除文档中已下线接口表与已禁用注释。
- 清理 -1816 行测试与文档。

**C. 治理空白**
- 该 commit 既未声明配置 breaking（环境变量 → config.toml），也未声明 API breaking（`client.py` 构造函数变更），也未声明 capability 删除（`sector_fund_flow`）。任一项独立看都是值得专门 change 的变更。

阶段 0 governance 已要求「proposal 必须明确兼容性影响、迁移影响、上线风险」。本 retroactive 把上述三类变更分别沉淀为合规材料，并新建 `configuration` capability 把「配置必须从 config.toml 读」提升为项目级约束。

## What Changes

- 新增 `openspec/changes/archive/2026-04-25-retroactive-config-toml-consolidation/` 历史合规归档：proposal / design / tasks / acceptance（不需要 upstream-alignment）。
- 新增 `configuration` capability，定义 FinanceData 的配置统一读取契约（config.toml 唯一来源、密钥不入 git、helper 模式、可缺省的可选配置）。
- 不修改任何 src/ 代码、不调整 `config.py` API、不重新决策环境变量是否回退。
- 阶段 3 `cleanup-config-and-proxy-leftovers` 将完成残余清理（`cache/resolver.py:41` 的 `os.environ.get("FINANCE_DATA_CACHE")` 与 `provider/akshare/_proxy.py` 的 `no_proxy` 读写），本 retroactive 是其前置依据。
- 非目标：不评估 `sector_fund_flow` 删除是否合理、不重新引入 `xueqiu/kline` / `baostock/kline`、不修改 `daily_basic.volume_ratio fallback` 逻辑。
- 兼容性：纯文档动作。
- 上线风险：无。

## Capabilities

### New Capabilities
- `configuration`: FinanceData 的项目级配置规范。覆盖：config.toml 作为唯一事实来源、密钥与 cookie 不进入 git、config.py helper 模式、可选配置的缺省值约定、token 缺失时 service 层降级行为。

### Modified Capabilities
- 无（本 change 不动其他 capability；阶段 3 清理时再评估 cache-layer 是否需要 MODIFIED）。

### Removed Capabilities
- 无（`sector_fund_flow` 在 OpenSpec 中此前未曾存在 capability；删除是事实，不需要 OpenSpec REMOVED）。

## Impact

- 受影响代码：无。
- 历史 commit 追溯：1e0ae0b（2026-04-19，含 70 个文件变化、325 行新增、1816 行删除）。
- 受影响 spec：新增 `openspec/specs/configuration/`。
- 依赖：复用阶段 0 OpenSpec 治理 + 模板；与阶段 3 形成强前置关系（阶段 3 用本 change 的 spec 作为「为何 FINANCE_DATA_CACHE 应该改 config.toml」的依据）。
