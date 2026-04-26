# configuration Specification

## Purpose
TBD - created by archiving change retroactive-config-toml-consolidation. Update Purpose after archive.
## Requirements
### Requirement: 项目配置必须以 config.toml 为唯一事实来源
系统 MUST 将 `config.toml`（位于项目根目录）作为所有运行时配置的唯一事实来源。配置项 MUST NOT 同时存在「环境变量」与「config.toml」两个等价入口。`os.environ.get("FINANCE_DATA_*")` 在本 change 后 MUST NOT 出现在 src/ 代码中；任何外部依赖（如 akshare 内部读 `no_proxy` 环境变量）的写入仍允许，但**初始来源**必须可追溯到 `config.toml` 与 `config.py` helper。

#### Scenario: 新配置项必须落 config.toml
- **WHEN** 项目需要新增运行时配置（如 token / cookie / 开关）
- **THEN** 该配置 MUST 在 `config.toml` 中定义
- **AND** MUST 通过 `config.py` 的 helper 函数读取
- **AND** MUST NOT 同时挂在环境变量与 config.toml 两个地方

#### Scenario: 残余环境变量读取必须显式追踪
- **WHEN** 维护方扫描代码发现仍有 `os.environ.get("FINANCE_DATA_*")` 或类似读取
- **THEN** 必须开 OpenSpec change 把该读取迁移到 config.toml
- **AND** 不允许长期容忍残留

#### Scenario: cache 与 proxy 配置已迁出环境变量
- **WHEN** 维护方扫描 `src/finance_data/` 下的 `os.environ.get`
- **THEN** MUST NOT 找到 `FINANCE_DATA_CACHE` 读取
- **AND** `provider/akshare/_proxy.py` 内的初始 hosts 列表 MUST 来自 `config.py` helper（而非硬编码字符串）

### Requirement: 敏感配置不得进入 git
系统 MUST 在 `.gitignore` 中排除 `config.toml`；MUST 提供 `config.toml.example` 作为模板（含字段名 + 占位值，无真实密钥）。

#### Scenario: 仓库不含真实密钥
- **WHEN** 任何提交触发 secret scanning
- **THEN** `config.toml` MUST NOT 出现在版本控制中
- **AND** `config.toml.example` MUST 仅含占位值（如 `your_token`）

#### Scenario: 新机器初始化流程
- **WHEN** 维护方在新机器克隆项目
- **THEN** 必须存在「拷贝 config.toml.example 到 config.toml 并填值」的明确步骤（已记录于 CLAUDE.md「配置」章节）

### Requirement: config.py 必须用 helper 函数封装配置读取
系统 MUST 通过 `config.py` 模块提供 helper 函数（如 `get_tushare_token()` / `has_tushare_token()` / `get_xueqiu_cookie()` / `has_tushare_stock_minute_permission()`）暴露 config 数据。其他模块 MUST 通过 helper 调用，MUST NOT 直接读 `tomllib` 或解析 `config.toml`。

#### Scenario: 任何模块只用 helper 读配置
- **WHEN** 任一 src 模块需要配置项
- **THEN** MUST 调用 `from finance_data.config import get_xxx`
- **AND** MUST NOT 出现 `tomllib.load()` 或 `open("config.toml")` 的直接读取

#### Scenario: helper 必须使用 lru_cache 避免重复 IO
- **WHEN** 多个模块在同一进程多次调用 helper
- **THEN** 底层 `_load()` MUST 仅读盘一次（当前实现：`@lru_cache(maxsize=1)`）

### Requirement: 可选配置必须有明确的缺省语义
系统 MUST 为可选配置提供明确缺省值与缺省行为：缺失时 helper 返回空字符串 / `False` / 项目级默认列表，service 层与 provider 层据此降级而不抛错。

#### Scenario: cookie 缺失时 xueqiu 仍可启动
- **WHEN** `config.toml` 中无 `[xueqiu]` 段或 `cookie = ""`
- **THEN** `get_xueqiu_cookie()` MUST 返回空字符串
- **AND** xueqiu provider MUST 不参与 service 层默认 provider 链
- **AND** MUST NOT 抛 `KeyError` 或导致进程启动失败

#### Scenario: 分钟权限缺失时分钟接口降级
- **WHEN** `config.toml` 中无 `tushare.stock_minute_permission` 或值为 `false`
- **THEN** `has_tushare_stock_minute_permission()` MUST 返回 `False`
- **AND** 涉及该权限的 tushare 接口 MUST 在 service 层标记为「不可用」或在 ToolSpec `available_if` 处过滤

#### Scenario: cache 开关缺失时默认启用
- **WHEN** `config.toml` 中无 `[cache]` 段或 `enabled` 字段缺失
- **THEN** `is_cache_enabled()` MUST 返回 `True`
- **AND** 行为与历史 `FINANCE_DATA_CACHE=1` 一致

#### Scenario: proxy hosts 列表缺失时回退到东财默认
- **WHEN** `config.toml` 中无 `[proxy]` 段或 `no_proxy_hosts` 为空
- **THEN** `get_no_proxy_hosts()` MUST 返回包含 `eastmoney.com` 与 `.eastmoney.com` 的默认列表

### Requirement: tushare token 缺失时 service 层必须显式降级
系统 MUST 在 `has_tushare_token()` 返回 `False` 时让所有依赖 tushare 的 service 层 dispatcher 不把 tushare provider 加入默认链；MUST NOT 在调用时才抛 `auth` 错误。

#### Scenario: 无 token 时 dispatcher 跳过 tushare
- **WHEN** `config.toml` 缺 `[tushare]` 段或 `token = ""`
- **THEN** service `_build_*()` 函数 MUST 在装配 dispatcher 时直接跳过 tushare provider
- **AND** 仅启用其他可用 provider（如 akshare）
- **AND** 若无任何 provider 可用，service 层应在调用时抛清晰的 `DataFetchError`

### Requirement: config.toml 缺失时进程必须给出清晰错误
系统 MUST 在 `config.toml` 不存在时由 `config.py` 的 `_load()` 抛出 `FileNotFoundError` 并附带可操作错误信息：明确指出文件路径与「请复制 config.toml.example 为 config.toml 并填写配置」的修复步骤。

#### Scenario: 首次运行无 config.toml
- **WHEN** 维护方在没有 `config.toml` 的环境下运行 finance-data
- **THEN** 进程 MUST 抛出 `FileNotFoundError`
- **AND** 错误信息 MUST 包含文件绝对路径
- **AND** 错误信息 MUST 包含修复指引（拷贝 example）

