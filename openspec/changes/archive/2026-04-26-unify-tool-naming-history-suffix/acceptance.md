<!-- 用 openspec/templates/acceptance.template.md 落地。 -->

## 验收结论

变更 `unify-tool-naming-history-suffix` 已完成实现和验证。`FinanceData` Python 客户端 48 个公开方法名全部重命名为「MCP tool 名去掉 `tool_get_` 前缀」格式，强制带 scope 后缀（`_history` / `_realtime` / `_snapshot` / `_daily`）。48 个旧名通过 `__getattr__` + `_DEPRECATED_ALIASES` 字典 100% 兼容，调用时发出 `DeprecationWarning`。新建 `client-naming` capability（3 Req）锁定命名规则 + alias 策略 + 守护测试。**pytest 418 passed**（415 + 3 新守护），零行为回归。本 change 是阶段性优化路线图最终阶段。

## Completeness

按 spec 3 条 ADDED Requirement 逐条核对：

- 已实现「客户端公开方法名必须从 MCP tool 名派生」：`client.py` 48 个方法名全部 = MCP tool 名去掉 `tool_get_` 前缀。守护测试 `test_client_methods_match_mcp_tools_as_set` 验证集合完全相等。
- 已实现「客户端方法重命名必须保留 deprecated alias」：`client.py` 顶部 `_DEPRECATED_ALIASES: dict[str, str]` 含 48 项「旧名 → 新名」映射；`FinanceData.__getattr__` 拦截器对每个旧名调用发出 `DeprecationWarning(f"fd.{old}() 已废弃，请改用 fd.{new}()")`，并代理到新方法。私有 / dunder 名因不在字典中按 Python 默认 `AttributeError` 处理。
- 已实现「客户端命名一致性必须由守护测试强制」：`tests/test_client_naming.py` 含 3 个测试 — 集合一致性 / alias 兼容性 + warning 触发 / alias 旧名与新方法不重叠。当前未重命名前 2 测试 FAIL，本 change 后 3 测试全 PASS。

附加交付：
- `CLAUDE.md` Python Library 示例 4 处旧名替换为新名 + 补「命名规则」callout 引导新用户。
- `tests/test_client_board.py` 旧 `fd.board_member` 调用更新为新名 `fd.board_member_history`。

## Correctness

已执行并通过：

- `openspec validate unify-tool-naming-history-suffix --strict` → `Change ... is valid`
- `pytest tests/` → **418 passed, 8 skipped**（包含 3 个新守护测试 + 之前的 415 个）
- `pytest tests/test_client_naming.py -v` → 3 passed
  - test_client_methods_match_mcp_tools_as_set PASSED
  - test_deprecated_aliases_are_callable_and_warn PASSED
  - test_alias_keys_do_not_overlap_with_real_methods PASSED
- 拆分前后对比：
  - 重命名前跑守护测试：2 failed 1 passed（揭露 client 当前 drift 与 alias 字典缺失）
  - 重命名 + 加 alias 后跑守护测试：3 passed（drift 修复）
- 手动验证 alias 触发 warning：
  ```
  $ python3 -W default -c "from finance_data import FinanceData; FinanceData().kline_daily"
  DeprecationWarning: fd.kline_daily() 已废弃，请改用 fd.kline_daily_history()。旧名将在下个 minor 版本移除。
  ```
- 手动验证 alias 解析正确：`FinanceData().kline_daily` 经 `__getattr__` 解析返回 `kline_daily_history` 方法对象（`__name__` 为 `kline_daily_history`）。
- `pytest tests/test_client_board.py -v` → 1 passed（旧调用已更新到新名）

未做 Playwright 验证：本 change 不涉及前端。

## Coherence

- 48 个方法签名（参数名 / 类型注解 / 默认值 / 返回类型）零变更（与 design.md「Non-Goals」一致）。
- Method body 与 docstring zero-touch（与 design.md Decision 3 一致）。
- 用 `__getattr__` 集中拦截 alias 而非 48 个 wrapper 方法，client.py 行数仅 +90 行（与 design.md Decision 1 一致）。
- 私有 / dunder / 拼错名按 Python 默认 `AttributeError` 处理，alias 拦截器仅响应字典中的 48 个旧名（与 design.md Decision 2 一致）。
- 旧名集合与新方法集合无重叠，由 `test_alias_keys_do_not_overlap_with_real_methods` 守护（防止字典写错把当前方法名当 alias）。
- DeprecationWarning 文本含旧名 + 新名 + 移除时间承诺（「下个 minor 版本」），符合 spec「warning 文本必须含旧名、新名与迁移指引」。
- CLAUDE.md 示例使用新名，并加 callout 提示旧名仍兼容；`__getattr__` 对私有 / dunder 名零干扰。
- 不修改 MCP tool 名 / ToolSpec / service / provider，与 design.md「Non-Goals」一致。

## 未测试项与风险

- **未实测「IDE 自动补全 / mypy 静态分析对 alias 的识别」**：`__getattr__` 暴露的 alias 不在 `dir(FinanceData)` 中，IDE 与 mypy 默认无法自动补全旧名。这正是 deprecation 的预期效果（引导用户用新名），但若有项目依赖 IDE 补全旧名将看不到。可作 backlog：未来加 `__deprecated_aliases__` class attribute 让 IDE 插件识别。
- **未实测「下游用户脚本的真实调用面」**：项目内已扫描所有 `fd.<method>` 调用并更新（仅 CLAUDE.md 4 处 + 1 处测试）。外部用户脚本（如 PlaybookOS 等消费方）需自行响应 DeprecationWarning。
- **未实测 `__getattr__` 与 `pickle.dumps(fd)` / 深拷贝 / `inspect.signature(fd.kline_daily)` 等元编程场景的兼容性**：当前测试覆盖标准调用 + warning 触发；元编程场景 case 较少，留作后续观察。
- **未实测「同时通过 alias 和新名调用」的混合场景**：守护测试单独验证两条路径，混合场景由 Python 解释器的 `__getattr__` 机制天然保证（alias 调用每次都触发 warning）。

## Spec Drift

无。

阶段 5 没有未修复的 drift；本 change 引入的所有 spec Requirement（3 条）都有实现证据 + 守护测试。alias 与新方法集合的不重叠由 `test_alias_keys_do_not_overlap_with_real_methods` 强制；MCP tool 集合与 client 方法集合的一致性由 `test_client_methods_match_mcp_tools_as_set` 强制。任何未来漂移都会被守护测试立即捕获。

## 上游未对齐项

无。本 change 不涉及任何上游金融数据源，纯客户端命名规范沉淀。

注：design.md Open Question 标注的 `dc_board_moneyflow_history` / `dc_market_moneyflow_history` 中 `dc_` 数据源前缀暴露问题，是 ToolSpec 层面的命名瑕疵（已在阶段 2.2 retroactive archive 中固定），本 change 仅按规则机械派生，不主动修复。未来若 ToolSpec 重命名（去 `dc_`），客户端方法名会自动跟随。
