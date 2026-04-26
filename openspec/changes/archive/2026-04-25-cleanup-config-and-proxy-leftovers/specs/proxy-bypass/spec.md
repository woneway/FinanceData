## ADDED Requirements

### Requirement: 东财上游必须在 provider 模块顶部强制绕过本地代理
系统在使用东财（eastmoney.com）作为上游数据源时 MUST 在 provider 模块顶部、所有真实调用之前调用代理绕过函数（当前实现：`ensure_eastmoney_no_proxy()`），将 eastmoney 域名加入 `no_proxy` 环境变量。该约束适用于所有 akshare 中以 `_em` 结尾或已知走东财的函数（含 `stock_zh_a_hist` 等）。

#### Scenario: 模块加载时绕代理生效
- **WHEN** 任一调用东财源的 provider 模块被 import
- **THEN** 在该模块第一次发起东财请求前，`no_proxy` MUST 已包含 eastmoney 相关域名

#### Scenario: 新增东财 provider 必须遵循同一约定
- **WHEN** 维护方新增一个调用 `_em` 函数（或已知东财函数）的 provider 模块
- **THEN** 模块顶部 MUST 出现代理绕过函数调用
- **AND** 不允许仅在调用点临时绕代理

### Requirement: 东财绕代理守护必须由自动化测试强制
系统 MUST 提供自动化守护测试，扫描 `provider/akshare` 目录下所有 Python 模块，检测：若模块导入了 `_em` 后缀函数或已知走东财的 akshare 函数（如 `stock_zh_a_hist`），该模块顶部 MUST 出现代理绕过函数调用。任一违例 MUST 让测试 FAIL。

#### Scenario: 守护测试发现违例
- **WHEN** 任一 provider 模块导入 `_em` 函数但未在模块顶部调用代理绕过
- **THEN** 守护测试 MUST FAIL
- **AND** 失败信息 MUST 列出违例文件路径

#### Scenario: 守护测试通过现有 6 个东财 provider
- **WHEN** 守护测试在当前代码库运行
- **THEN** lhb / lhb_inst_detail / suspend / hot_rank / north_flow / pool 6 个文件 MUST 全部通过
- **AND** 测试 MUST NOT 误报其他不走东财的 provider

### Requirement: no_proxy hosts 列表必须从 config.toml 读取
系统 MUST 让代理绕过函数从 `config.toml [proxy] no_proxy_hosts` 读取要绕代理的 hosts 列表，hosts 列表 MUST 通过 `config.py` helper 函数（`get_no_proxy_hosts()`）暴露。代理绕过函数仍 MUST 写入 `no_proxy` 环境变量（akshare 内部消费必需），但初始 hosts 来源 MUST NOT 在 Python 代码中硬编码。

#### Scenario: 配置项缺省时回退到东财默认
- **WHEN** `config.toml` 中无 `[proxy]` 段或 `no_proxy_hosts` 为空
- **THEN** `get_no_proxy_hosts()` MUST 返回包含 `eastmoney.com` 与 `.eastmoney.com` 的默认列表
- **AND** 维护方未配置时行为与历史一致

#### Scenario: 配置 hosts 被合并到 no_proxy 环境变量
- **WHEN** `config.toml` 设置 `no_proxy_hosts = ["eastmoney.com", ".eastmoney.com", "example.com"]`
- **AND** 任一东财 provider 模块被加载
- **THEN** `os.environ["no_proxy"]` MUST 包含全部三个 hosts
- **AND** 已有的 `no_proxy` 环境变量值 MUST NOT 被覆盖（保持幂等合并）
