## Context

阶段 4 已确认 48 个 MCP tool 名称都遵循 `tool_get_<entity>_<scope>` 格式（scope ∈ {history, realtime, snapshot, daily}）。`FinanceData` Python 客户端当前 48 个公开方法名（与 MCP 1:1 对应）多数省略了 scope 后缀，部分还省略了 `entity` 前缀（例如 `quote` 对应 `tool_get_stock_quote_realtime`）。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| MCP tool 名 | `TOOL_SPEC_REGISTRY.keys()` | 不动 |
| 客户端方法名规则 | spec 第 1 条 Requirement | 新建 |
| 客户端方法名实现 | `client.py` 48 个方法 | 全部重命名 |
| 旧名兼容 | `client.py` 中 `__getattr__` + `_DEPRECATED_ALIASES` 字典 | 新建 |
| 守护测试 | `tests/test_client_naming.py` | 新建 |

完整重命名映射（48 项）：

| 旧名（保留为 alias） | 新名 = MCP tool 去 `tool_get_` 前缀 |
|---|---|
| `stock_info` | `stock_info_snapshot` |
| `stock_list` | `stock_basic_list_snapshot` |
| `kline_daily` | `kline_daily_history` |
| `kline_weekly` | `kline_weekly_history` |
| `kline_monthly` | `kline_monthly_history` |
| `kline_minute` | `kline_minute_history` |
| `quote` | `stock_quote_realtime` |
| `index_quote` | `index_quote_realtime` |
| `index_kline` | `index_kline_history` |
| `board_index` | `board_index_history` |
| `board_member` | `board_member_history` |
| `board_kline` | `board_kline_history` |
| `chip` | `chip_distribution_history` |
| `financial_summary` | `financial_summary_history` |
| `dividend` | `dividend_history` |
| `capital_flow` | `capital_flow_realtime` |
| `trade_calendar` | `trade_calendar_history` |
| `market_stats` | `market_stats_realtime` |
| `suspend` | `suspend_daily` |
| `hot_rank` | `hot_rank_realtime` |
| `ths_hot` | `ths_hot_history` |
| `auction` | `auction_history` |
| `auction_close` | `auction_close_history` |
| `daily_market` | `daily_market_history` |
| `daily_basic_market` | `daily_basic_market_history` |
| `stk_limit` | `stk_limit_daily` |
| `lhb_detail` | `lhb_detail_history` |
| `lhb_stock_stat` | `lhb_stock_stat_history` |
| `lhb_active_traders` | `lhb_active_traders_history` |
| `lhb_trader_stat` | `lhb_trader_stat_history` |
| `lhb_stock_detail` | `lhb_stock_detail_daily` |
| `lhb_inst_detail` | `lhb_inst_detail_history` |
| `hm_list` | `hm_list_snapshot` |
| `hm_detail` | `hm_detail_history` |
| `zt_pool` | `zt_pool_daily` |
| `strong_stocks` | `strong_stocks_daily` |
| `previous_zt` | `previous_zt_daily` |
| `zbgc_pool` | `zbgc_pool_daily` |
| `limit_list` | `limit_list_history` |
| `kpl_list` | `kpl_list_history` |
| `limit_step` | `limit_step_history` |
| `north_hold` | `north_hold_history` |
| `north_capital` | `north_capital_snapshot` |
| `margin` | `margin_history` |
| `margin_detail` | `margin_detail_history` |
| `stock_factor` | `stock_factor_pro_history` |
| `board_moneyflow` | `dc_board_moneyflow_history` |
| `market_moneyflow` | `dc_market_moneyflow_history` |

48 旧名 → 48 新名，集合 1:1。

## Goals / Non-Goals

**Goals:**
- 客户端 48 个方法名 = MCP 48 个 tool 名去 `tool_get_` 前缀（集合一致）。
- 旧名 100% 兼容（deprecated alias，行为零变更，发出 `DeprecationWarning`）。
- 守护测试锁定「客户端方法名 = MCP tool 名」+ alias 兼容性。
- CLAUDE.md 文档示例使用新名，引导新用户从一开始就用新规则。

**Non-Goals:**
- 不动 MCP tool 名称、ToolSpec、service / provider / interface。
- 不动方法签名（参数名 / 类型 / 默认值 / 返回类型）。
- 不删除任何旧名（仅 deprecated）。
- 不实施反射机制自动从 MCP tool 名生成 client 方法。
- 不动 `tests/test_client_board.py` 之外的测试（其他测试不直接调用 `fd.<method>`）。

## Decisions

### 1. 用 `__getattr__` 拦截器实现 alias，而非每个旧名一个 wrapper 方法

**选项**：
- A. 每个旧名定义一个 wrapper 方法：`def quote(self, *args, **kwargs): warnings.warn(...); return self.stock_quote_realtime(*args, **kwargs)`。48 个旧名 → 48 个 wrapper。
- B. 用 `__getattr__` + `_DEPRECATED_ALIASES: dict[str, str]` 集中管理，48 个旧名压成一个字典字面量 + 一段拦截逻辑。

**选择 B**。

**理由**：
- A 让 client.py 行数翻倍（每个 wrapper ~5 行 × 48 = +240 行），可读性下降。
- B 只增加 ~15 行（`__getattr__` 实现 + 字典字面量），可读性高，新增 alias 时改字典即可。
- B 副作用：被拦截的旧名不在 `dir(FinanceData)` 中（除非显式特殊处理），但这正符合「rename 后旧名应被淡出文档可见性」的语义。
- alias 的 `DeprecationWarning` 在 `__getattr__` 中只发一次还是每次调用都发？选择「每次调用都发」（与 Python 标准库 `warnings` 默认 filter 一致；用户可自行 `warnings.filterwarnings` 控制）。

### 2. `__getattr__` 必须区分 deprecated alias 与真实不存在的属性

**理由**：
- 用户写 `fd.typo_method()` 时应抛 `AttributeError`，不能被 alias 拦截器吞掉。
- 实现：拦截器只拦截在 `_DEPRECATED_ALIASES` 字典中的 key；其他名字按 Python 默认行为抛 `AttributeError`。

### 3. 重命名采用「重写 client.py」而非 minimal diff

**选项**：
- A. 用 `git mv` 风格仅修改方法名（保留 method body 与 docstring）。
- B. 重写整个 client.py 文件（method 顺序按 ToolSpec _DOMAIN_ORDER 重排，同步 docstring 模板化）。

**选择 A**。

**理由**：
- 阶段 5 是命名 change，不是结构 change。重排 method 顺序会引入「diff 巨大但行为零变更」的认知噪音。
- minimal diff 只改方法名，加 `__getattr__` + 字典；其他保留，git diff 清晰。
- 缓解：未来若需要按 _DOMAIN_ORDER 重排 client.py，可独立 refactor change。

### 4. CLAUDE.md 示例改新名但保留旧名兼容性提示

**理由**：
- CLAUDE.md 是新用户第一次接触项目的文档，应直接展示新规则。
- 同时在示例段落末尾补一句「旧名 `fd.kline_daily` 等仍可工作但发出 DeprecationWarning，请新代码使用新名」。

### 5. 守护测试与 client_naming spec 第 3 条 Requirement 一致：双向集合 + alias 调用

**实现**：
- 测试 1：`set(fd 公开方法) == set(MCP tool 名去前缀)`，用 `inspect.getmembers` 过滤 callable 且不以 `_` 开头。但要排除 alias（alias 通过 `__getattr__` 暴露但不在 `dir()` 中），所以 `dir()` 自然只含真实方法 → 与 MCP 集合相等。
- 测试 2：遍历 `_DEPRECATED_ALIASES`，对每个旧名 `getattr(fd, old_name)` 不应 raise，且应触发 DeprecationWarning。用 `pytest.warns(DeprecationWarning)` 捕获。
- 测试 3：每个 alias 的新名必须存在（防止字典写错）。

### 6. 不在 client.py 中实施 `tool(name, **params)` 通用入口

**理由**：
- 增加复杂度，且与「方法 1:1 对应 MCP tool」spec 形成两套并存入口。
- 若未来需要，可独立 change 引入。

### 7. lhb 域内特殊处理：lhb_active_traders / lhb_trader_stat 是否带前缀？

**判断**：MCP tool 名分别是 `tool_get_lhb_active_traders_history` 与 `tool_get_lhb_trader_stat_history`，去前缀 = `lhb_active_traders_history` / `lhb_trader_stat_history`。client 方法名按规则就是这两个，不需要额外前缀讨论。

### 8. board_moneyflow / market_moneyflow 改名为 dc_* 是否会让用户困惑？

**判断**：MCP tool 名是 `tool_get_dc_board_moneyflow_history` / `tool_get_dc_market_moneyflow_history`（dc = 东财 datacenter）。按规则去前缀 = `dc_board_moneyflow_history`。这暴露了「数据源前缀」到 API 名 —— 不理想，但当前 ToolSpec 名已固定（阶段 2.2 retroactive 已 archive），本 change 不修 MCP tool 名。

**缓解**：在 design.md Open Question 标注：未来若要 ToolSpec 重命名（去掉 `dc_`），应另开 change，届时 client 方法名自动跟随。

## Source-of-Truth 映射（实现 → spec）

| 实施事实 | 来源 | 对应 Requirement |
| --- | --- | --- |
| 48 个新方法名 = MCP tool 去前缀 | `client.py` 重命名 | client-naming「公开方法名必须从 MCP tool 名派生」 |
| `_DEPRECATED_ALIASES: dict[str, str]` 含 48 项 | `client.py` 顶部常量 | client-naming「重命名必须保留 deprecated alias」 |
| `__getattr__` 拦截器 + DeprecationWarning | `client.py` `__getattr__` | client-naming「旧名调用仍可工作」Scenario |
| `tests/test_client_naming.py` 三测试 | 新增测试 | client-naming「客户端命名一致性必须由守护测试强制」 |

## Risks / Trade-offs

- [Risk] `__getattr__` 拦截可能影响 IDE 自动补全 / mypy 静态分析。  
  → Mitigation: alias 是 deprecated 路径，IDE 应该引导用户用新名。可选：定义一个 `__deprecated_aliases__` class attribute 让 IDE 插件识别。本 change 不做，留作 backlog。

- [Risk] DeprecationWarning 默认在 `__main__` 上下文外被静默（Python 3 默认）。  
  → Mitigation: 用户在 pytest 或 IDE 可见。生产用户若用 `warnings.filterwarnings("default")` 可看到。CLAUDE.md 标注「如未看到 warning，请检查 warning filter」。

- [Risk] alias 拦截器吞掉用户拼写错误的「类似旧名的拼错」（如 `fd.qoute` 不被拦截 → AttributeError 是正确行为）。  
  → Mitigation: 字典精确匹配，仅 48 项。任何其他名按默认 AttributeError。

- [Risk] 用户在测试中 `with patch.object(fd, "kline_daily", ...)` 这种 mock 会失败（因为 `kline_daily` 不再是真实方法属性）。  
  → Mitigation: 文档说明：mock 应针对新名。`tests/test_client_board.py` 已更新示范。

- [Risk] `dc_board_moneyflow_history` 暴露 `dc_` 数据源前缀到 API。  
  → Mitigation: 接受现状，未来 ToolSpec 重命名 change 自动跟随。

## Migration Plan

1. **守护测试先行**：写 `tests/test_client_naming.py` 但暂不包含 alias 部分（因为 alias 还不存在）；先写 method 集合一致性测试 → 在当前未重命名代码下应 FAIL（揭露 drift）。
2. **写 _DEPRECATED_ALIASES 字典与 __getattr__**：在 client.py 顶部加字典 + 类内加 `__getattr__`。
3. **逐方法重命名**：48 个方法 `def old_name` → `def new_name`，docstring 不动，body 不动。
4. **更新 CLAUDE.md**：替换 5 处旧名示例为新名 + 补一段 deprecation 提示。
5. **更新 tests/test_client_board.py**：`fd.board_member` → `fd.board_member_history`。
6. **补全守护测试 alias 部分**：`pytest.warns(DeprecationWarning)` 验证。
7. **跑全量 pytest**：必须 415 → 418+ passed（新增守护测试）。
8. **archive**。

回滚策略：`git revert` 单 commit，运行时影响为零（alias 兼容旧调用）。

## Open Questions

- 是否要把 `dc_` 前缀从 `dc_board_moneyflow_history` / `dc_market_moneyflow_history` 中去掉（即 ToolSpec 重命名）？  
  → 不在本 change 范围；独立 change 评估。
- 是否要 `__deprecated_aliases__` class attribute 让 IDE 识别？  
  → 不在本 change，留作 backlog。
