## MODIFIED Requirements

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
